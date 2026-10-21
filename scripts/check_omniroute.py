"""Read-only connection/model check; never generates tokens or changes routing."""
from pathlib import Path
import argparse
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from llm.omniroute import OmniRouteProvider


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--list-models', action='store_true')
    args = parser.parse_args()
    try:
        if args.list_models:
            rows = OmniRouteProvider.models()
            print(json.dumps({'models': [x['id'] for x in rows],
                              'note': 'Availability is not proof of free eligibility.'}, indent=2))
        else:
            _, _, model = OmniRouteProvider.configuration()
            rows = OmniRouteProvider.models()
            if model not in {x['id'] for x in rows}:
                raise ValueError('Configured route is absent from the gateway model catalog')
            print(json.dumps({'status': 'READY_FOR_SMOKE_TEST', 'model': model,
                              'inference_executed': False, 'accuracy_evaluated': False}))
        return 0
    except Exception as exc:
        # Do not echo request headers, credentials, upstream error bodies or URLs.
        message = str(exc) if isinstance(exc, ValueError) else type(exc).__name__
        print(json.dumps({'status': 'NOT_READY', 'reason': message, 'inference_executed': False}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
