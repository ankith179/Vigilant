"""Parse bounded chat actions; repository operations use the existing API worker."""
import re

REF = r'[A-Za-z0-9_][A-Za-z0-9_./~^@{}-]{0,179}'


def comparison(question, base=None, head=None):
    requested = bool(base or head or re.match(r'^\s*(compare|investigate)\b', question, re.I))
    if not requested:
        return None
    match = re.fullmatch(r'\s*(?:compare|investigate)\s+(' + REF + r')\s+(?:with|against|to)\s+(' + REF + r')', question.rstrip('?.! '), re.I)
    if match:
        base, head = base or match[1], head or match[2]
    if not base or not head:
        return {'state': 'NEEDS_CLARIFICATION', 'answer': 'Specify both revisions, for example: compare HEAD~1 with HEAD.'}
    if not re.fullmatch(REF, base) or not re.fullmatch(REF, head):
        return {'state': 'NEEDS_CLARIFICATION', 'answer': 'Use Git revision names or commit hashes without shell commands.'}
    return {'state': 'READY', 'base': base, 'head': head}


def response(state, answer, **extra):
    return {'state': state, 'answer': answer, 'decision': {'decision': state}, 'citations': [],
            'retrieved_evidence': [], 'validation_error': None, 'inference_calls': 0,
            'semantic_entailment_verified': False,
            'confidence_note': 'Repository comparison uses deterministic tools; no model call.', **extra}
