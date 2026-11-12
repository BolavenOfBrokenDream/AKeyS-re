import json
import time
from contextvars import ContextVar
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

import openai
from openai import OpenAI

from util import get_from_cache, save_to_cache

LOG_MAX_LENGTH = 300
sample_context = ContextVar("sample_id", default=None)
usage_log_lock = Lock()


def set_sample_id(sample_id):
    sample_context.set(sample_id)


def identity(res):
    return res


def get_model(args):
    model_name, temperature = args.model, args.temperature
    base_url = args.openai_proxy if hasattr(args, 'openai_proxy') else None
    print('base_url: ', base_url)

    if 'gpt' in model_name or 'deepseek' in model_name:
        return GPT(args.api_key, model_name, temperature, base_url)
    raise KeyError(f"Model {model_name} not implemented")


class Model(object):
    def __init__(self):
        self.post_process_fn = identity

    def set_post_process_fn(self, post_process_fn):
        self.post_process_fn = post_process_fn


class GPT(Model):
    def __init__(self, api_key, model_name, temperature=1.0, base_url=None,
                 max_tokens=1024, usage_log_path=None, run_id=None):
        super().__init__()
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.usage_log_path = usage_log_path
        self.run_id = run_id
        self.badrequest_count = 0
        self.is_deepseek = 'deepseek' in model_name.lower()
        openai.api_key = api_key
        if base_url:
            openai.base_url = base_url
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def get_response(self, **kwargs):
        for attempt in range(3):
            try:
                return self.client.chat.completions.create(**kwargs)
            except openai.RateLimitError:
                print('RateLimitError')
                if attempt == 2:
                    raise
                time.sleep(10 * (attempt + 1))
            except (openai.APIConnectionError, openai.APITimeoutError):
                print('APIConnectionError/APITimeoutError')
                if attempt == 2:
                    raise
                time.sleep(30)
            except openai.BadRequestError:
                self.badrequest_count += 1
                print('BadRequestError', self.badrequest_count)
                raise

    def write_usage_log(self, status, sample_id, call_type, response=None,
                        usage=None, error=None):
        if not self.usage_log_path:
            return
        usage_data = usage.model_dump() if usage is not None else {}
        prompt_details = usage_data.get('prompt_tokens_details') or {}
        cached_tokens = prompt_details.get('cached_tokens')
        if cached_tokens is None:
            cached_tokens = usage_data.get('prompt_cache_hit_tokens')
        record = {
            'run_id': self.run_id,
            'sample_id': sample_id or sample_context.get(),
            'call_type': call_type,
            'model': self.model_name,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'status': status,
            'prompt_tokens': usage_data.get('prompt_tokens'),
            'completion_tokens': usage_data.get('completion_tokens'),
            'total_tokens': usage_data.get('total_tokens'),
            'cached_tokens': cached_tokens,
            'usage': usage_data,
            'response': response,
            'error': error,
        }
        log_path = Path(self.usage_log_path)
        with usage_log_lock:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with log_path.open('a', encoding='utf-8') as log_file:
                log_file.write(json.dumps(record, ensure_ascii=False) + '\n')

    def forward(self, head=None, prompt=None, use_cache=True, logger=None,
                forward_use_logger=True, use_json_format=False, sample_id=None,
                call_type='chat'):
        messages = []
        info = {}

        if logger is None:
            forward_use_logger = False

        if head is not None:
            messages.append({"role": "system", "content": head})
        messages.append({"role": "user", "content": prompt})

        key = json.dumps([self.model_name, messages])

        if forward_use_logger:
            logger.info(f"Messages: {str(messages)[:LOG_MAX_LENGTH]}")

        if use_cache:
            cached_value = get_from_cache(key, logger, forward_use_logger)
            if cached_value is not None:
                if forward_use_logger:
                    logger.info("Cache Hit")
                else:
                    print("Cache Hit")
                self.write_usage_log('cache_hit', sample_id, call_type,
                                     response=cached_value)
                return cached_value, None

        if forward_use_logger:
            logger.info("Cache Miss")
        else:
            print("Cache Miss")

        request_kwargs = {
            'model': self.model_name,
            'messages': messages,
            'temperature': self.temperature,
        }
        if use_json_format:
            request_kwargs['response_format'] = {"type": "json_object"}
        if self.is_deepseek:
            request_kwargs['max_tokens'] = self.max_tokens
            request_kwargs['extra_body'] = {"thinking": {"type": "disabled"}}

        try:
            response = self.get_response(**request_kwargs)
        except openai.OpenAIError as exc:
            error = f"{type(exc).__name__}: {exc}"
            self.write_usage_log('api_error', sample_id, call_type, error=error)
            if forward_use_logger:
                logger.error(error)
            return None, {'response': None, 'message': None, 'error': error}

        content = response.choices[0].message.content
        messages.append({"role": "assistant", "content": content})
        info = response.usage.model_dump()
        info['response'] = content
        info['message'] = messages
        self.write_usage_log('success', sample_id, call_type, response=content,
                             usage=response.usage)

        if forward_use_logger:
            logger.info(f"Response: {str(info['response'])[:LOG_MAX_LENGTH]}")
        save_to_cache(key, content, logger, forward_use_logger)
        if forward_use_logger:
            logger.info("Cache Saved")

        return self.post_process_fn(content), info
