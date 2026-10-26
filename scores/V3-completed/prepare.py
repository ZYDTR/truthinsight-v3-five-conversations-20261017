"""Export sealed V3.1 submissions without changing participant artifacts."""
from pathlib import Path
import datetime
import hashlib
import json
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
HARNESS = ROOT.parents[1]
BENCH = HARNESS / 'TruthInsightBench'
BATCH = HARNESS / 'experiments/shared-context-v3.1-20261016/batches/qwen3.7-flash-main-6d52948-20261016'
sys.path.insert(0, str(BENCH / 'agents'))
from workspace_integrity import sha256_file, tree_snapshot, validate_workspace

def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def main():
    assert not (ROOT / 'exports').exists(), 'Export already exists; do not replace frozen inputs.'
    rows = []
    for sealed_path in sorted((BATCH / 'runs').glob('*/sealed.json')):
        seal = json.loads(sealed_path.read_text())
        task = seal['task_id']
        run_dir = sealed_path.parent
        run = json.loads((run_dir / 'run.json').read_text())
        snap = Path(seal['snapshot'])
        project = snap / 'project'
        assert seal['state'] == 'SEALED'
        assert all(sha256_file(snap / f) == h for f, h in seal['manifest'].items()), task
        assert all(sha256_file(project / f) == h for f, h in run['input_hashes'].items()), task
        rounds = sorted(p for p in (run_dir / 'rounds').iterdir() if p.is_dir() and p.name != '000-warmup')
        status_file = rounds[-1] / 'status.json'
        status = json.loads(status_file.read_text())
        assert status['success'] and status['data']['status'] == 'completed'
        assert status['data']['active_run_id'] is None
        collection = json.loads((snap / 'collection.json').read_text())
        assert not collection['input_changed'] and not collection['shared_changed']
        assert set(collection['model_counts']) <= {'qwen3.7-flash', '<synthetic>'}
        destination = ROOT / 'exports' / task
        workspace = destination / 'workspace'
        workspace.mkdir(parents=True)
        # Copy exactly the originally frozen public input set, plus the complete final output.
        for relative, digest in run['input_hashes'].items():
            target = workspace / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(project / relative, target)
            assert sha256_file(target) == digest
        shutil.copytree(project / 'output', workspace / 'output')
        original_output = tree_snapshot(project / 'output')
        output = tree_snapshot(workspace / 'output')
        assert output == original_output and not output['unsafe_entries']
        check = validate_workspace(workspace, expected_task_id=task)
        assert check['passed'], check['errors']
        validation_path = destination / 'submission_validation.json'
        subprocess.run([sys.executable, '-B', str(BENCH / 'evaluation/submission_format/validate_submission.py'), str(workspace / 'output'), '--receipt', str(validation_path)], check=True, stdout=subprocess.DEVNULL)
        validation = json.loads(validation_path.read_text())
        assert validation['passed']
        receipt = {
            'schema': 'truthinsightbench-agent-run-receipt', 'release': 'V1.0',
            'agent_id': 'sap-shared-context-v3.1', 'task_id': task,
            'model': run['model'], 'harness': 'SAP Conversation with shared scientific context and operator feedback',
            'harness_version': '3.1.0', 'subject_commit': '52fff1847bec1a2f82b1abd8e23caeda979dea21',
            'status': 'completed', 'platform_exit_code': 0,
            'platform_exit_code_note': 'Adapter normalizes the recorded SAP completed terminal status to successful exit; no new process run is claimed.',
            'receipt_kind': 'posthoc_adapter_from_frozen_SAP_evidence',
            'started_at': run['created_at'], 'finished_at': seal['at'],
            'workspace': 'workspace', 'output_path': 'workspace/output',
            'output_validation_passed': True, 'workspace_input_integrity_passed': True,
            'workspace_input_tree_sha256': check['input_tree_sha256'],
            'workspace_input_file_count': check['input_file_count'], 'workspace_input_bytes': check['input_bytes'],
            'output_tree_sha256': output['sha256'], 'output_file_count': output['file_count'], 'output_bytes': output['bytes'],
            'source_seal': str(sealed_path), 'source_seal_sha256': sha256_file(sealed_path),
            'source_terminal_status': str(status_file), 'source_terminal_status_sha256': sha256_file(status_file),
            'source_snapshot': str(snap), 'scientific_round_count': len(rounds),
            'operator_feedback_included': True,
            'scoring_scope': 'final sealed output only; no reviewer diagnostics or prior-version results added',
        }
        save(destination / 'run_receipt.json', receipt)
        rows.append({'task_id': task, 'run_root': str(destination), 'source_seal': str(sealed_path), 'source_seal_sha256': sha256_file(sealed_path), 'seal_entries_verified': len(seal['manifest']), 'output': output, 'finding_count': validation['registered_findings']['count']})
    assert len(rows) == 5
    code_paths = [BENCH / 'registry.json'] + [p for p in (BENCH / 'evaluation').rglob('*') if p.is_file() and '__pycache__' not in p.parts] + [BENCH / 'agents/workspace_integrity.py']
    code = {str(p.relative_to(BENCH)): sha256_file(p) for p in sorted(code_paths)}
    save(ROOT / 'source-manifest.json', {'at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'scorer': 'unmodified vendored TruthInsightBench V1.0', 'benchmark_root': str(BENCH), 'evaluator_files': code, 'runs': rows})
    cmd = [sys.executable, '-B', str(BENCH / 'evaluation/evaluate.py')]
    for row in rows:
        cmd += ['--run-root', row['run_root']]
    cmd += ['--work-dir', str(ROOT / 'work'), '--judge-model', 'qwen3.8-max', '--dry-run']
    with (ROOT / 'prepare.log').open('w') as log:
        subprocess.run(cmd, check=True, stdout=log, stderr=subprocess.STDOUT)
    print(json.dumps({'status': 'READY', 'runs': len(rows), 'findings': sum(x['finding_count'] for x in rows), 'seal_entries_verified': sum(x['seal_entries_verified'] for x in rows)}))

if __name__ == '__main__':
    main()
