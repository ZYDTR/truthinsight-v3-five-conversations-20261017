"""Read live native transcripts; no scientific computation or model invocation."""
import ast
import collections
import json
import re
import sys
from pathlib import Path
from controller_impl import E, ENV, Client, save, stamp


def observe(task, since=0):
    run = E / 'runs' / task
    manifest = json.loads((run / 'run.json').read_text())
    project = Path(manifest['project'])
    secrets = []
    for line in (ENV / 'private/route.env').read_text().splitlines():
        if '=' not in line:
            continue
        key, value = line.split('=', 1)
        if any(x in key for x in ('KEY', 'TOKEN', 'SECRET', 'PASSWORD')):
            try:
                value = ast.literal_eval(value)
            except Exception:
                pass
            if len(value) > 10:
                secrets.append(value)

    for user in json.loads((ENV / 'private/users.json').read_text()).values():
        secrets.extend(v for k, v in user.items() if isinstance(v, str) and any(x in k.lower() for x in ('token', 'password', 'secret')) and len(v) > 10)
    for raw_path in (project.parent / 'state/claude/projects').rglob('*.jsonl'):
        for key, value in re.findall(r'([A-Z_]*(?:TOKEN|SECRET|KEY|PASSWORD)[A-Z_]*)=([^\s\\\"\']+)', raw_path.read_text(errors='replace')):
            if len(value) > 20 and '$' not in value:
                secrets.append(value)

    def scrub(value):
        text = json.dumps(value, ensure_ascii=False)
        for secret in secrets:
            text = text.replace(secret, '[REDACTED]')
        return text

    status = Client(run).status()
    data = status.get('data', {})
    print(scrub({'task': task, 'at': stamp(), 'status': data.get('status'),
                 'state': data.get('conversation_state')}))
    files = []
    for path in sorted((project.parent / 'state/claude/projects').rglob('*.jsonl')):
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        models = collections.Counter(row.get('message', {}).get('model')
                                     for row in rows if row.get('type') == 'assistant')
        child = 'subagents' in path.parts
        files.append({'file': str(path), 'child': child, 'lines': len(rows), 'models': dict(models)})
        print(scrub(files[-1]))
        for index, row in enumerate(rows, 1):
            if index <= since:
                continue
            content = row.get('message', {}).get('content')
            if not isinstance(content, list):
                continue
            for block in content:
                kind = block.get('type')
                if kind == 'tool_use':
                    item = {'line': index, 'tool': block.get('name'), 'input': block.get('input')}
                    # Agent prompts are always shown completely. Long source writes stay in raw evidence.
                    if item['tool'] not in ('Agent', 'Task') and len(scrub(item)) > 2200:
                        item['input'] = str(item['input'])[:2200] + ' [see full raw JSONL]'
                    print(scrub(item))
                elif kind == 'text':
                    print(scrub({'line': index, 'text': block.get('text')}))
                elif kind == 'tool_result' and block.get('is_error'):
                    print(scrub({'line': index, 'error': block.get('content')}))
    save(run / 'private/live-observation.json', {'at': stamp(), 'files': files, 'status': status})


if __name__ == '__main__':
    observe(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 0)
