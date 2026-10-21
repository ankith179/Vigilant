"""Local-only Ollama inference with pinned installed-model digests and bounded memory."""
import json
import os
from urllib.parse import urlsplit
import httpx
from ingestion.models import Decision
from llm.providers import LLMProvider

MODELS_32GB = ('qwen3:8b', 'qwen2.5-coder:14b', 'qwen3:14b')


class OllamaProvider(LLMProvider):
    name = 'ollama'
    evidence_budget = 18000
    evidence_limit = 24

    def __init__(self, model=None):
        self.model = model or os.getenv('OLLAMA_MODEL', 'qwen3:8b')
        self.identity = None

    @staticmethod
    def base_url():
        base = os.getenv('OLLAMA_URL', 'http://127.0.0.1:11434').rstrip('/')
        u = urlsplit(base)
        if (u.scheme not in {'http','https'} or u.hostname not in {'localhost','127.0.0.1','::1'}
                or u.username or u.password or u.query or u.fragment or u.path):
            raise ValueError('OLLAMA_URL must be a local loopback URL without credentials or a path')
        return base

    @classmethod
    def models(cls):
        with httpx.Client(trust_env=False, follow_redirects=False, timeout=15) as c:
            r = c.get(cls.base_url()+'/api/tags'); r.raise_for_status()
            return r.json()['models']

    def preflight(self):
        if ':cloud' in self.model.lower():
            raise ValueError('Cloud models are disabled; select an installed local model')
        row = next((m for m in self.models() if m.get('name')==self.model or m.get('model')==self.model),None)
        if not row or not row.get('digest'):
            raise ValueError('Model not installed with a verifiable digest: '+self.model)
        with httpx.Client(trust_env=False, follow_redirects=False, timeout=15) as c:
            r=c.post(self.base_url()+'/api/show',json={'model':self.model});r.raise_for_status();info=r.json()
        if info.get('remote_host') or info.get('remote_model') or row.get('remote_host'):
            raise ValueError('Remote-backed Ollama models are disabled in this local profile')
        self.identity={'model':self.model,'digest':row['digest'],'size_bytes':row.get('size'),
            'quantization':row.get('details',{}).get('quantization_level'),
            'supports_thinking':'thinking' in info.get('capabilities',[]),
            'num_ctx':8192,'num_predict':512,'temperature':0,'think':False}
        return self.identity

    @staticmethod
    def citation_schema(messages):
        """Constrain aliases to the exact excerpts that survived context selection."""
        schema = Decision.model_json_schema()
        excerpts = json.loads(messages[-1]['content'])['evidence']
        for field, key in [('evidence_ids', 'evidence_id'), ('affected_artifacts', 'artifact_id')]:
            allowed = list(dict.fromkeys(e[key] for e in excerpts))
            if allowed:
                schema['properties'][field]['items']['enum'] = allowed
            else:
                schema['properties'][field]['maxItems'] = 0
        return schema

    def investigate(self, question, evidence):
        result = super().investigate(question, evidence)
        # Derived references identify cited artifacts, not proven dependency impacts.
        by_id = {e['evidence_id']: e['artifact_id'] for e in evidence}
        result['cited_artifacts'] = list(dict.fromkeys(
            by_id[e] for e in result['decision']['evidence_ids'])) if not result['validation_error'] else []
        return result

    def complete(self, messages):
        if self.identity is None:self.preflight()
        schema=getattr(self,'output_schema',None) or self.citation_schema(messages)
        body={'model':self.model,'messages':messages,'stream':False,'format':schema,
            'keep_alive':0,'options':{'temperature':0,'num_ctx':8192,'num_predict':512,'seed':42}}
        if self.identity['supports_thinking']:body['think']=False
        # ponytail: unload after each call to avoid concurrent models on a 32 GB PC;
        # retain a model longer only after measuring available RAM and throughput.
        with httpx.Client(trust_env=False,follow_redirects=False,timeout=600) as c:
            r=c.post(self.base_url()+'/api/chat',json=body);r.raise_for_status();d=r.json()
        completion_error=None if d.get('done') and d.get('done_reason')=='stop' else 'Incomplete Ollama generation'
        text=d.get('message',{}).get('content')
        if not isinstance(text,str) or not text.strip():raise ValueError('Ollama returned no final text')
        return text,{'input_tokens':d.get('prompt_eval_count'),'output_tokens':d.get('eval_count'),
            'reported_model':d.get('model'),'api_cost_usd':0.,'local_model':self.identity,
            'elapsed_seconds':d.get('total_duration',0)/1e9,'completion_error':completion_error,
            'done':d.get('done'),'done_reason':d.get('done_reason'),'output_schema':schema,
            'citation_policy':'selected-alias-enums-v1'}
