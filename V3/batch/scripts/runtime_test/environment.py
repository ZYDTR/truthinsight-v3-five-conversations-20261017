"""Pinned-main V3 environment up/down, adapted from V1 scripts/runtime_test/environment.py.

Adaptations only: archived final V1 images as bases (no pip installs at build time),
V3 env root / RUN_ID / owner labels, qwen3.7-flash model, tibv2_ usernames via archived
bootstrap (single prefix diff), route.env copied from V1 archived env. Everything else
uses fetched main app/migrations plus the frozen V3 prompt. Dependency base stays V1."""
import ast, hashlib, json, secrets, socket, subprocess, sys, time, urllib.request
from datetime import datetime, timezone
from pathlib import Path

E = Path(__file__).resolve().parents[2]          # batch root
SOURCE_E = E.parents[1]                          # V2 experiment root
env = Path(json.loads((E / '.local/active.json').read_text())['environment'])
rid = env.name
D = '/usr/local/bin/docker'
OWNER = '/root/shared_v31_five_operators'
V1_ENV = Path('/Users/zhengyidi/yage/context-infrastructure/adhoc_jobs/truthinsight_bench_harness/'
              'experiments/shared-context-v1-20261016/.local/tibv1-1832e3ea')
API_BASE_IMAGE = 'tibv1-1832e3ea-api:candidate'
WORKER_BASE_IMAGE = 'tibv1-1832e3ea-worker:candidate'
MODEL = 'qwen3.7-flash'

def save(name, value):
    p = env / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    p.chmod(0o600)

def call(args, log=None):
    if log:
        with (env / log).open('ab') as f:
            p = subprocess.run([D, *args], stdout=f, stderr=subprocess.STDOUT)
        if p.returncode:
            raise RuntimeError('Docker failed; log ' + str(env / log))
        return ''
    return subprocess.check_output([D, *args], text=True, stderr=subprocess.PIPE).strip()

def labels():
    return sum((['--label', k + '=' + v] for k, v in {'codex.test': 'true', 'codex.run_id': rid,
               'codex.owner': OWNER, 'codex.cleanup': 'required'}.items()), [])

def ids(kind):
    cmds = {'containers': ['ps', '-aq'], 'networks': ['network', 'ls', '-q'],
            'volumes': ['volume', 'ls', '-q'], 'images': ['images', '-aq']}
    return sorted(set(call(cmds[kind] + ['--filter', 'label=codex.run_id=' + rid,
                                          '--filter', 'label=codex.owner=' + OWNER]).split()))

def cleanup():
    for ident in ids('containers'):
        call(['logs', ident], 'container-' + ident + '.log')
    for kind, cmd in [('containers', ['rm', '-f', '-v']), ('networks', ['network', 'rm']),
                      ('volumes', ['volume', 'rm']), ('images', ['image', 'rm'])]:
        v = ids(kind)
        if v:
            try:
                call(cmd + v, 'cleanup-' + kind + '.log')
            except Exception as exc:
                save('cleanup-' + kind + '-error.json', {'error': str(exc)})
    save('cleanup.json', {k: ids(k) for k in ['containers', 'networks', 'volumes', 'images']})

def prepare_files():
    for name in ['private', 'runtime_state', 'skills', 'logs', 'bin']:
        (env / name).mkdir(exist_ok=True)
    # config.json: NEW database/JWT/user secrets generated for this round only.
    cfg = {'run_id': rid, 'database': 'sap_' + rid.replace('-', '_'),
           'database_password': secrets.token_hex(16), 'jwt_secret': secrets.token_hex(32),
           'user_password': secrets.token_urlsafe(24), 'state_host': str(env / 'runtime_state'),
           'skills_host': str(env / 'skills'), 'worker_base_image': WORKER_BASE_IMAGE,
           'model_name': MODEL, 'port': 0}
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        cfg['port'] = s.getsockname()[1]
    save('config.json', cfg)
    # route.env: byte copy of V1 archived env credentials (programmatic, values never printed).
    route = (V1_ENV / 'private/route.env').read_bytes()
    selected = []
    for line in route.decode().splitlines():
        if '=' in line and (line.startswith('CCSDK_OPENAI_COMPAT_') or line.startswith('CCSDK_MODEL_PROXY_PROVIDER=')):
            key = line.split('=', 1)[0]
            if key == 'CCSDK_OPENAI_COMPAT_FALLBACK_MODEL':
                line = key + '=""'
            selected.append(line)
    (env / 'private/route.env').write_text('\n'.join(selected) + '\n')
    (env / 'private/route.env').chmod(0o600)
    # docker wrapper adding codex labels, identical to V1 except owner/run_id come from config.
    wrapper = '''#!/usr/bin/env python3
import os,sys,json
from pathlib import Path
cfg=json.loads(Path('/harness/config.json').read_text());args=sys.argv[1:]
if args and args[0] in ('run','build'):
    for k,v in {'codex.test':'true','codex.run_id':cfg['run_id'],'codex.owner':'/root/shared_v31_five_operators','codex.cleanup':'required'}.items():args[1:1]=['--label',k+'='+v]
os.execv('/usr/bin/docker',['docker',*args])
'''
    (env / 'bin/docker').write_text(wrapper)
    (env / 'bin/docker').chmod(0o755)
    # bootstrap.py: archived file with the single tibv1_ -> tibv2_ username-prefix change.
    boot = (V1_ENV / 'bootstrap.py').read_text()
    assert boot.count('tibv1_') == 1, 'unexpected tibv1_ occurrences: %d' % boot.count('tibv1_')
    boot_v2 = boot.replace('tibv1_', 'tibv31_')
    (env / 'bootstrap.py').write_text(boot_v2)
    import difflib
    (env / 'bootstrap-adaptation.diff').write_text(''.join(difflib.unified_diff(
        boot.splitlines(True), boot_v2.splitlines(True), fromfile='v1-archived-bootstrap', tofile='v2-bootstrap')))
    (env / 'Dockerfile.api').write_text(
        'FROM ' + API_BASE_IMAGE + '\nUSER root\nCOPY source/app/ /app/app/\nCOPY source/migrations/ /app/migrations/\nCOPY source/requirements.txt /app/requirements.txt\nRUN python3 -m pip install --no-cache-dir filelock==3.20.0\nWORKDIR /app\n'
        'ENTRYPOINT ["python3", "/harness/bootstrap.py"]\n')
    (env / 'Dockerfile.worker').write_text(
        'FROM ' + WORKER_BASE_IMAGE + '\nUSER root\n'
        'COPY source/app/agent_runtime/container_worker/ /opt/ccsdk_worker/\n'
        'COPY source/app/agent_runtime/contracts.py source/app/agent_runtime/evidence_selection.py '
        'source/app/agent_runtime/workflow_dag_contract.py /opt/ccsdk_worker/\n'
        'COPY source/app/agent_runtime/context_assets/ /runtime_assets/contexts/\n'
        'COPY source/app/agent_runtime/docker/ccsdk_env_scrub_bwrap /opt/agent-runtime/npm-global/bin/bwrap\n'
        'RUN chown -R root:root /opt/ccsdk_worker && chmod -R go-w /opt/ccsdk_worker\nUSER agent\n')

def up():
    for name in ['private', 'runtime_state', 'skills', 'logs', 'bin']:
        (env / name).mkdir(exist_ok=True)
    cfg = json.loads((env / 'config.json').read_text())
    port = cfg['port']
    call(['build', *labels(), '-f', str(env / 'Dockerfile.api'), '-t', rid + '-api:candidate', str(env)], 'api-build.log')
    call(['network', 'create', *labels(), rid + '-net'])
    call(['volume', 'create', *labels(), rid + '-pgdata'])
    call(['run', '-d', *labels(), '--name', rid + '-pg', '--network', rid + '-net',
          '-v', rid + '-pgdata:/var/lib/postgresql/data', '-e', 'POSTGRES_DB=' + cfg['database'],
          '-e', 'POSTGRES_USER=probe', '-e', 'POSTGRES_PASSWORD=' + cfg['database_password'],
          'postgres:16-alpine'])
    call(['run', '-d', *labels(), '--name', rid + '-redis', '--network', rid + '-net',
          '--tmpfs', '/data:rw,size=128m', 'redis:7-alpine'])
    for _ in range(60):
        if subprocess.run([D, 'exec', rid + '-pg', 'pg_isready', '-U', 'probe'], capture_output=True).returncode == 0:
            break
        time.sleep(1)
    common = ['--network', rid + '-net', '-v', str(env) + ':/harness',
              '-v', str(env / 'runtime_state') + ':/app/runtime_state',
              '-v', str(env / 'skills') + ':/app/skills',
              '-v', str(env / 'private/route.env') + ':/credentials.env:ro',
              '-v', '/var/run/docker.sock:/var/run/docker.sock']
    call(['run', '--rm', *labels(), '--name', rid + '-seed', *common, rid + '-api:candidate', 'seed'], 'seed.log')
    digest = call(['run', '--rm', *labels(), '--name', rid + '-digest', *common, rid + '-api:candidate', 'digest']).splitlines()[-1]
    # Overlay the same-origin runtime files onto the archived final worker image (no pip installs).
    call(['build', '--platform', 'linux/amd64', *labels(), '--label', 'ccsdk.worker.source_digest=' + digest,
          '-f', str(env / 'Dockerfile.worker'), '-t', rid + '-worker:candidate', str(env)], 'worker-build.log')
    call(['run', '--rm', *labels(), '--name', rid + '-versions', rid + '-worker:candidate', 'python3', '-c',
          "import importlib.metadata as m,json,subprocess,claude_agent_sdk;from pathlib import Path;"
          "print(json.dumps({x:m.version(x) for x in ['claude-agent-sdk','numpy','pandas','scipy','scikit-learn','statsmodels','matplotlib','seaborn','openpyxl','h5py']}));"
          "print(subprocess.check_output([str(Path(claude_agent_sdk.__file__).parent/'_bundled/claude'),'--version'],text=True))"],
         'versions.txt')
    call(['run', '-d', *labels(), '--name', rid + '-api', '-p', f'127.0.0.1:{port}:8001', *common, rid + '-api:candidate', 'serve'])
    base = f'http://127.0.0.1:{port}'
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    for _ in range(90):
        try:
            with opener.open(base + '/openapi.json', timeout=2) as r:
                (env / 'openapi.json').write_bytes(r.read())
            break
        except Exception:
            time.sleep(1)
    else:
        raise RuntimeError('API_TIMEOUT')
    save('ready.json', {'run_id': rid, 'api_base': base, 'worker_source_digest': digest,
                        'image_ids': {n: call(['image', 'inspect', '-f', '{{.Id}}', rid + '-' + n + ':candidate'])
                                       for n in ['api', 'worker']},
                        'model': cfg['model_name'], 'fallback': '', 'max_turns': 500, 'max_rounds': 40,
                        'max_concurrent_subagents': 4})
    print(json.dumps(json.loads((env / 'ready.json').read_text()), indent=2))

if __name__ == '__main__':
    if sys.argv[1] == 'down':
        cleanup()
    elif sys.argv[1] == 'prepare':
        prepare_files()
        print(json.dumps({'prepared': str(env)}))
    else:
        try:
            up()
        except BaseException as e:
            save('startup-error.json', {'type': type(e).__name__, 'error': str(e)})
            cleanup()
            raise
