"""Root-only V2 completion gate and V3 infrastructure activation; never sends science."""
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

B = Path(__file__).resolve().parents[1]
V = B.parents[1]
SPEC = json.loads((B / 'control/run-spec.json').read_text())
PREVIOUS = Path(SPEC['predecessor_gate']['batch'])
ENV = Path(json.loads((B / '.local/active.json').read_text())['environment'])
D = '/usr/local/bin/docker'


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    path.chmod(0o600)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def gate():
    pending, rows = [], []
    for task in SPEC['tasks']:
        name = task['task_id']
        run = PREVIOUS / 'runs' / name
        required = ['sealed.json', 'docs/execution-report.md', 'docs/execution-index.json',
                    'docs/comparison-v1-v2.md', 'reviews/verdict.json']
        missing = [rel for rel in required if not (run / rel).is_file()]
        active_jobs = [p.parent.name for p in run.glob('jobs/*/state.json')
                       if json.loads(p.read_text())['state'] in ('QUEUED', 'RUNNING', 'WAITING_FOR_SLOT')]
        if missing or active_jobs:
            pending.append(name)
        rows.append({'task': name, 'missing': missing, 'pending_jobs': active_jobs,
                     'sealed_sha256': sha(run / 'sealed.json') if (run / 'sealed.json').exists() else None})
    cp = PREVIOUS / 'docs/cleanup.json'
    cleanup = json.loads(cp.read_text()) if cp.exists() else {}
    if cleanup.get('passed') is not True or any(cleanup.get('remaining', {}).values()):
        pending.append('V2 shared cleanup')
    proof = {'at': datetime.now(timezone.utc).isoformat(), 'passed': not pending,
             'pending': pending, 'tasks': rows, 'cleanup_sha256': sha(cp) if cp.exists() else None}
    save(B / 'docs/predecessor-gate.json', proof)
    return proof


def require_gate():
    result = gate()
    if not result['passed']:
        raise RuntimeError('V2 is not complete; no V3 environment/session may start: ' + ', '.join(result['pending']))
    # Verify actual resources as well as the saved cleanup claim.
    prior_env = Path(json.loads((PREVIOUS / '.local/active.json').read_text())['environment'])
    remaining = {}
    for key, command in {'containers': ['ps', '-aq'], 'networks': ['network', 'ls', '-q'],
                         'volumes': ['volume', 'ls', '-q'], 'images': ['images', '-aq']}.items():
        remaining[key] = subprocess.check_output([D, *command, '--filter', 'label=codex.run_id=' + prior_env.name], text=True).split()
    if any(remaining.values()):
        raise RuntimeError('V2 resources remain: ' + str(remaining))
    return result


def verify():
    expected = json.loads((ENV / 'source-after.json').read_text())
    actual = {str(p.relative_to(ENV / 'source')): sha(p) for p in sorted((ENV / 'source').rglob('*'))
              if p.is_file() and '__pycache__' not in p.parts}
    assert actual == expected, 'Prepared source changed'
    ready = json.loads((ENV / 'ready.json').read_text())
    assert ready['model'] == 'qwen3.7-flash' and ready['fallback'] == ''
    for key, value in [('max_turns', 500), ('max_rounds', 40), ('max_concurrent_subagents', 4)]:
        assert ready[key] == value, key
    checks = {}
    for kind, target in [('api', '/app/app/agent_runtime/container_worker/claude_code_sdk_worker.py'),
                         ('worker', '/opt/ccsdk_worker/claude_code_sdk_worker.py')]:
        program = "from pathlib import Path;import hashlib;print(hashlib.sha256(Path(" + repr(target) + ").read_bytes()).hexdigest())"
        if kind == 'api':
            command = [D, 'exec', ENV.name + '-api', 'python3', '-c', program]
        else:
            command = [D, 'run', '--rm', '--label', 'codex.test=true', '--label', 'codex.run_id=' + ENV.name,
                       '--label', 'codex.owner=/root/shared_v31_five_operators', '--label', 'codex.cleanup=required',
                       ENV.name + '-worker:candidate', 'python3', '-c', program]
        digest = subprocess.check_output(command, text=True, stderr=subprocess.PIPE).strip()
        assert digest == expected['app/agent_runtime/container_worker/claude_code_sdk_worker.py'], kind + ' wrong prompt/source'
        checks[kind + '_worker_source_sha256'] = digest
    source = (ENV / 'source/app/agent_runtime/container_worker/claude_code_sdk_worker.py').read_text()
    node = next(n for n in ast.parse(source).body if isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == 'CONVERSATION_SYSTEM_PROMPT_APPEND' for t in n.targets))
    assert ast.literal_eval(node.value) == (V / 'subject/system_prompt.md').read_text()
    prior_env = Path(json.loads((PREVIOUS / '.local/active.json').read_text())['environment'])
    def versions_in(path):
        # V2 startup retries appended identical probes; compare measurements, not log repetition/warnings.
        lines = path.read_text().splitlines()
        packages = [json.loads(line) for line in lines if line.startswith('{')]
        cli = [line for line in lines if re.fullmatch(r'\d+\.\d+\.\d+ \(Claude Code\)', line)]
        assert packages and cli, 'Version measurements missing'
        assert all(p == packages[-1] for p in packages) and len(set(cli)) == 1, 'Inconsistent measurements'
        return {'packages': packages[-1], 'cli': cli[-1]}
    versions = versions_in(ENV / 'versions.txt')
    prior_versions = versions_in(prior_env / 'versions.txt')
    assert versions == prior_versions, 'SDK/CLI/scientific dependency drift'
    proof = {'at': datetime.now(timezone.utc).isoformat(), 'passed': True, 'backend_sha': SPEC['backend_sha'],
             'environment': str(ENV), 'api_base': ready['api_base'], 'image_ids': ready['image_ids'],
             'source_file_count': len(expected), 'checks': checks, 'dependency_versions_identical': True, 'versions': versions,
             'actual_agent_models': 'Verified by each operator from neutral warmup and first scientific child JSONL.'}
    save(B / 'docs/environment-verification.json', proof)
    return proof


def up():
    require_gate()
    subprocess.run([sys.executable, '-B', str(V / 'scripts/validate_context.py')], check=True)
    if (ENV / 'ready.json').exists():
        return verify()
    for tag, expected in json.loads((ENV / 'base-images.json').read_text()).items():
        actual = subprocess.check_output([D, 'image', 'inspect', '-f', '{{.Id}}', tag], text=True).strip()
        assert actual == expected, 'Baseline image drift: ' + tag
    subprocess.run([sys.executable, '-B', str(B / 'scripts/runtime_test/environment.py'), 'up'], check=True)
    try:
        return verify()
    except BaseException:
        subprocess.run([sys.executable, '-B', str(B / 'scripts/runtime_test/environment.py'), 'down'], check=False)
        raise


if __name__ == '__main__':
    action = sys.argv[1]
    result = {'gate': gate, 'up': up, 'verify': verify}[action]()
    print(json.dumps(result, ensure_ascii=False, indent=2))
