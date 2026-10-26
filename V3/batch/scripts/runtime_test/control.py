"""五个操作者共用入口：身份校验、单会话发送锁、两运行槽、证据封存。"""
import argparse
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
import uuid

import controller_impl as c

E, ENV = c.E, c.ENV


@contextlib.contextmanager
def lock(path, blocking=True):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB))
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


@contextlib.contextmanager
def slot(job):
    handles = [(E / '.local' / f'slot-{i}.lock').open('a') for i in range(2)]
    held = None
    try:
        while held is None:
            for handle in handles:
                try:
                    fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    held = handle
                    break
                except BlockingIOError:
                    pass
            if held is None:
                c.save(job / 'state.json', {'state': 'WAITING_FOR_SLOT', 'at': c.stamp()})
                time.sleep(5)
        yield
    finally:
        for handle in handles:
            if handle is held:
                fcntl.flock(handle, fcntl.LOCK_UN)
            handle.close()


def monitor(task):
    run = E / 'runs' / task
    m = json.loads((run / 'run.json').read_text())
    project = Path(m['project'])
    if not project.exists():
        return
    def inventory(root):
        return {str(p.relative_to(root)): {'bytes': p.stat().st_size, 'sha256': c.sha(p)}
                for p in root.rglob('*') if p.is_file() and not p.is_symlink()}
    previous = run / 'monitoring/latest.json'
    prev = json.loads(previous.read_text()) if previous.exists() else {}
    files = inventory(project)
    raw = inventory(project.parent / 'state/claude/projects')
    changes = [p for p in files if files[p] != prev.get('project_files', {}).get(p)]
    growth = [p for p in raw if raw[p] != prev.get('raw_jsonl', {}).get(p)]
    progress = bool(growth) or any(p.startswith(('output/', 'working/')) for p in changes)
    proof = {'at': c.stamp(), 'task': task, 'status': c.Client(run).status(),
             'project_files': files, 'raw_jsonl': raw, 'project_changed': changes,
             'raw_changed': growth, 'substantive_progress': progress,
             'consecutive_no_progress_checks': 0 if progress else prev.get('consecutive_no_progress_checks', 0) + 1}
    c.save(run / 'monitoring' / (proof['at'].replace(':', '') + '.json'), proof)
    c.save(previous, proof)
    return {k: proof[k] for k in ('at', 'task', 'substantive_progress', 'consecutive_no_progress_checks')}


def run_turn(task, job):
    request = json.loads((job / 'request.json').read_text())
    stop = threading.Event()
    def sample():
        while not stop.is_set():
            try:
                monitor(task)
            except Exception as exc:
                c.save(job / 'monitor-error.json', {'type': type(exc).__name__, 'error': str(exc), 'at': c.stamp()})
            stop.wait(240)
    with lock(E / 'runs' / task / 'send.lock', blocking=False):
        with slot(job):
            c.save(job / 'state.json', {'state': 'RUNNING', 'at': c.stamp()})
            sampler = threading.Thread(target=sample, daemon=True)
            sampler.start()
            try:
                c.send(task, input_path=request.get('input_path'), warmup=request['warmup'])
                c.save(job / 'state.json', {'state': 'COMPLETED', 'at': c.stamp()})
            except BaseException as exc:
                c.save(job / 'state.json', {'state': 'ERROR', 'type': type(exc).__name__, 'error': str(exc), 'at': c.stamp()})
                raise
            finally:
                stop.set()
                sampler.join(timeout=5)


def start(task, input_path, warmup):
    run = E / 'runs' / task
    with lock(run / 'dispatch.lock', blocking=False):
        if (run / 'sealed.json').exists():
            raise RuntimeError('Sealed run cannot receive messages')
        if warmup and (run / 'rounds/000-warmup').exists():
            raise RuntimeError('Warmup already exists; inspect its recorded outcome')
        if not warmup and input_path and not list((run / 'rounds').glob('[0-9][0-9][0-9]')):
            if Path(input_path).read_bytes() != (run / 'first-message.md').read_bytes():
                raise RuntimeError('First scientific message must equal original LaunchPrompt')
        jobs = run / 'jobs'
        jobs.mkdir(exist_ok=True)
        for previous in jobs.iterdir():
            state = json.loads((previous / 'state.json').read_text())
            if state['state'] in ('QUEUED', 'RUNNING', 'WAITING_FOR_SLOT'):
                raise RuntimeError('An existing send job is pending; inspect status instead of resending: ' + str(previous))
        job = jobs / (str(time.time_ns()) + '-' + uuid.uuid4().hex[:6])
        job.mkdir()
        path = None
        if input_path:
            p = Path(input_path).resolve()
            if not p.is_relative_to(run.resolve()) or not p.is_file():
                raise RuntimeError('Feedback must be saved inside this task run directory')
            path = str(job / 'input.md')
            Path(path).write_bytes(p.read_bytes())
        c.save(job / 'request.json', {'task': task, 'warmup': warmup, 'input_path': path,
                                    'owner': c.assignment(task)['operator_session_id']})
        c.save(job / 'state.json', {'state': 'QUEUED', 'at': c.stamp()})
        with (job / 'process.log').open('ab') as log:
            process = subprocess.Popen([sys.executable, '-B', __file__, '_run-turn', '--job', str(job)],
                                       stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                                       start_new_session=True, env=os.environ.copy())
        c.save(job / 'process.json', {'pid': process.pid, 'started_at': c.stamp()})
        return {'job': str(job), 'pid': process.pid, 'state': 'QUEUED'}


def seal(task, blocked):
    run = E / 'runs' / task
    with lock(run / 'dispatch.lock', blocking=False), lock(run / 'send.lock', blocking=False):
        for job in (run / 'jobs').glob('*'):
            state = json.loads((job / 'state.json').read_text())['state']
            if state in ('QUEUED', 'RUNNING', 'WAITING_FOR_SLOT'):
                raise RuntimeError('Cannot seal a pending send job')
        st = c.Client(run).status()
        if not st['data']['conversation_state']['can_accept_input']:
            raise RuntimeError('Conversation still active; wait or cancel through API and preserve evidence')
        for rel in ('docs/execution-report.md', 'reviews/verdict.json'):
            if not (run / rel).is_file():
                raise RuntimeError('Missing human/agent review artifact: ' + rel)
        c.collect(task)
        review = json.loads((run / 'reviews/verdict.json').read_text())
        if not review.get('raw_jsonl_reviewed') or not review.get('raw_files'):
            raise RuntimeError('Original JSONL reading evidence required')
        if review.get('scoring_performed') is not False:
            raise RuntimeError('Explicit no-scoring declaration required')
        snapshot = json.loads((run / 'latest-collection.json').read_text())['snapshot']
        proof = {'task_id': task, 'at': c.stamp(), 'state': 'BLOCKED' if blocked else 'SEALED',
                 'snapshot': snapshot, 'owner': c.assignment(task)['operator_session_id'],
                 'manifest': c.hashes(Path(snapshot)), 'review_sha256': c.sha(run / 'reviews/verdict.json')}
        # 此用户仅拥有本题；封存后立即回收其 worker，公共服务等最后一题封存再回收。
        m = json.loads((run / 'run.json').read_text())
        ids = subprocess.check_output([c.D, 'ps', '-aq', '--filter', 'label=codex.run_id=' + ENV.name], text=True).split()
        removed = []
        for ident in ids:
            info = json.loads(subprocess.check_output([c.D, 'inspect', ident], text=True))[0]
            mounts = json.dumps(info.get('Mounts', []))
            if '/users/' + m['user_code'] in mounts and '/harness' not in mounts:
                with (run / 'private' / ('worker-' + ident + '.log')).open('wb') as stream:
                    subprocess.run([c.D, 'logs', ident], stdout=stream, stderr=subprocess.STDOUT)
                subprocess.run([c.D, 'rm', '-f', '-v', ident], check=True, capture_output=True)
                removed.append(ident)
        c.save(run / 'worker-cleanup.json', {'at': c.stamp(), 'removed': removed})
        c.save(run / 'sealed.json', proof)
        return proof | {'manifest': 'stored in sealed.json'}


def finish_shared():
    with lock(E / '.local/shared-cleanup.lock'):
        registry = json.loads((E / 'control/ownership.json').read_text())
        pending = [x['task_id'] for x in registry['bindings'] if not (E / 'runs' / x['task_id'] / 'sealed.json').exists()]
        if pending:
            return {'shared_cleanup': 'WAITING', 'pending': pending}
        destination = E / 'docs/cleanup.json'
        if destination.exists():
            return json.loads(destination.read_text())
        config = json.loads((ENV / 'config.json').read_text())
        with (ENV / 'private/final-database.sql').open('wb') as stream:
            subprocess.run([c.D, 'exec', ENV.name + '-pg', 'pg_dump', '-U', 'probe', config['database']],
                           stdout=stream, stderr=subprocess.PIPE, check=True)
        (ENV / 'private/final-database.sql').chmod(0o600)
        from environment import cleanup
        cleanup()
        proof = json.loads((ENV / 'cleanup.json').read_text())
        c.save(destination, {'at': c.stamp(), 'run_id': ENV.name, 'remaining': proof,
                             'passed': not any(proof.values()), 'database_backup': str(ENV / 'private/final-database.sql')})
        return json.loads(destination.read_text())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['whoami', 'prepare', 'warmup', 'send', '_run-turn', 'status', 'collect', 'monitor', 'observe', 'audit', 'seal', 'finish'])
    parser.add_argument('--input')
    parser.add_argument('--job')
    parser.add_argument('--since', type=int, default=0)
    parser.add_argument('--blocked', action='store_true')
    args = parser.parse_args()
    a = c.assignment()
    task = a['task_id']
    run = E / 'runs' / task
    result = None
    if args.action == 'whoami':
        result = a | {'run_directory': str(run), 'environment_ready': (ENV / 'ready.json').is_file()}
    elif args.action == 'prepare':
        c.prepare(task)
    elif args.action in ('warmup', 'send'):
        result = start(task, args.input, args.action == 'warmup')
    elif args.action == '_run-turn':
        job = Path(args.job).resolve()
        if not job.is_relative_to((run / 'jobs').resolve()):
            raise RuntimeError('Foreign job denied')
        run_turn(task, job)
    elif args.action == 'status':
        result = {'binding': a, 'jobs': {p.name: json.loads((p / 'state.json').read_text()) for p in (run / 'jobs').glob('*')},
                  'status': c.Client(run).status() if (run / 'run.json').exists() else 'NOT_PREPARED'}
    elif args.action == 'collect':
        c.collect(task)
    elif args.action == 'monitor':
        result = monitor(task)
    elif args.action == 'observe':
        from observe import observe
        observe(task, args.since)
    elif args.action == 'audit':
        from audit_raw import audit
        audit(task)
    elif args.action == 'seal':
        result = seal(task, args.blocked)
        result['shared_cleanup'] = finish_shared()
    elif args.action == 'finish':
        result = finish_shared()
    if result is not None:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
