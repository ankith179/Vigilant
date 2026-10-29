"""Explicit GLM API provider; requests are opt-in and never retried or rerouted."""
import os

import httpx

from llm.providers import LLMProvider


class GLMProvider(LLMProvider):
    name = 'glm'

    def __init__(self, model=None):
        self.model = model or os.getenv('GLM_MODEL', '').strip()

    def preflight(self):
        if not os.getenv('GLM_API_KEY'):
            raise ValueError('GLM_API_KEY is required; no request was sent')
        if not self.model:
            raise ValueError('GLM_MODEL must name the explicitly selected GLM model')
        return {'provider': self.name, 'model': self.model, 'identity_verification': 'provider-reported only'}

    def complete(self, messages):
        self.preflight()
        with httpx.Client(trust_env=False, follow_redirects=False, timeout=90) as client:
            response = client.post(
                'https://api.z.ai/api/paas/v4/chat/completions',
                headers={'Authorization': 'Bearer ' + os.environ['GLM_API_KEY']},
                json={'model': self.model, 'messages': messages, 'temperature': 0,
                      'max_tokens': 1200, 'response_format': {'type': 'json_object'}},
            )
        if not 200 <= response.status_code < 300:
            raise RuntimeError(f'GLM API HTTP {response.status_code}; no retry or fallback attempted')
        data = response.json()
        choice = data['choices'][0]
        if choice.get('finish_reason') != 'stop':
            raise ValueError('GLM generation incomplete; response excluded from accuracy scoring')
        text = choice['message']['content']
        if not isinstance(text, str) or not text.strip():
            raise ValueError('GLM returned no final text')
        return text, {**data.get('usage', {}), 'provider': self.name, 'requested_model': self.model,
                      'reported_model': data.get('model'), 'response_id': data.get('id'),
                      'api_cost_usd': None, 'cost_policy': 'provider billing not independently verified',
                      'temperature': 0, 'max_tokens': 1200}
