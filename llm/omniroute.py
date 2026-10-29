"""Explicit free-route integration. The router operator controls upstream billing.

No automatic routing, client fallback, retry, or credit purchase. Availability
and zero-cost eligibility must be confirmed on the connected provider account.
"""
import json
import os
from urllib.parse import urlsplit

import httpx

from ingestion.models import Decision, digest
from llm.providers import LLMProvider


class OmniRouteProvider(LLMProvider):
    name = 'omniroute'
    evidence_budget = 48000
    evidence_limit = 24

    @staticmethod
    def connection():
        base = os.getenv('OMNIROUTE_BASE_URL', 'http://127.0.0.1:20128/v1').rstrip('/')
        url = urlsplit(base)
        if (url.scheme not in {'http', 'https'} or url.hostname not in {'127.0.0.1', 'localhost', '::1'}
                or url.username or url.password or url.query or url.fragment or url.path != '/v1'):
            raise ValueError('OMNIROUTE_BASE_URL must be a local loopback URL ending in /v1')
        key = os.getenv('OMNIROUTE_API_KEY', '')
        return base, {'Authorization': 'Bearer '+key} if key else {}

    @classmethod
    def configuration(cls):
        base, headers = cls.connection()
        model = os.getenv('OMNIROUTE_MODEL', '').strip()
        allowed = {x.strip() for x in os.getenv('OMNIROUTE_FREE_MODELS', '').split(',') if x.strip()}
        if not model or '/' not in model or model.split('/', 1)[0].lower() in {'auto', 'combo', 'combos'} or '*' in model:
            raise ValueError('Select an explicit provider/model from OmniRoute; auto/combos are disabled')
        if model not in allowed:
            raise ValueError('Route is not in OMNIROUTE_FREE_MODELS; confirm its free-tier eligibility first')
        return base, headers, model

    @classmethod
    def models(cls):
        base, headers = cls.connection()
        # Never send the local gateway credential through a redirect or system proxy.
        with httpx.Client(trust_env=False, follow_redirects=False, timeout=15) as client:
            response = client.get(base+'/models', headers=headers)
            response.raise_for_status()
            return response.json()['data']

    def complete(self, messages):
        base, headers, model = self.configuration()
        body = {'model': model, 'messages': messages, 'stream': False, 'temperature': 0,
                'max_tokens': 4096, 'response_format': {'type': 'json_object'}}
        with httpx.Client(trust_env=False, follow_redirects=False, timeout=180) as client:
            response = client.post(base+'/chat/completions', headers=headers, json=body)
            if response.status_code == 429:
                raise RuntimeError('Free-route quota exhausted; stopped without retry or fallback')
            if response.status_code >= 300:
                raise RuntimeError(f'OmniRoute HTTP {response.status_code}; no fallback attempted')
            data = response.json()
        choice = data['choices'][0]
        if choice.get('finish_reason') != 'stop':
            raise ValueError('OmniRoute generation incomplete; response excluded from accuracy scoring')
        text = choice['message']['content']
        if not isinstance(text, str) or not text.strip():
            raise ValueError('OmniRoute returned no final text')
        usage = {**data.get('usage', {}), 'requested_model': model, 'reported_model': data.get('model'),
                 'response_id': data.get('id'), 'api_cost_usd': None,
                 'cost_policy': 'operator-confirmed free route; billing not independently verified',
                 'prompt_sha256': digest(messages), 'temperature': 0, 'max_tokens': 4096}
        return text, usage

