"""Verify final score provenance and summarize without changing any score."""
from pathlib import Path
from collections import Counter
import datetime
import hashlib
import json
import statistics

ROOT = Path(__file__).resolve().parent
def read(path):
    return json.loads(path.read_text())
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    source = read(ROOT / 'source-manifest.json')
    final_path = ROOT / 'work/final/final_scoring_result.json'
    final = read(final_path)
    assert final['status'] == 'scored' and final['model'] == 'qwen3.8-max'
    assert len(final['run_results']) == 5
    assert final['cohort_sha256'] == sha(ROOT / 'work/cohort.json')
    bench = Path(source['benchmark_root'])
    changed = [relative for relative, digest in source['evaluator_files'].items() if sha(bench / relative) != digest]
    assert not changed, changed
    assert final['scorer_sha256'] == sha(bench / 'evaluation/evaluator/score_cohort.mjs')
    assert final['closure_scorer_sha256'] == sha(bench / 'evaluation/evaluator/finalize_scores.mjs')
    seal_count = 0
    for run in source['runs']:
        seal_path = Path(run['source_seal'])
        assert sha(seal_path) == run['source_seal_sha256']
        seal = read(seal_path)
        for relative, digest in seal['manifest'].items():
            assert sha(Path(seal['snapshot']) / relative) == digest, relative
            seal_count += 1
        receipt = read(Path(run['run_root']) / 'run_receipt.json')
        workspace = Path(run['run_root']) / 'workspace'
        for p in workspace.rglob('*'):
            if p.is_file():
                assert sha(p) == sha(Path(seal['snapshot']) / 'project' / p.relative_to(workspace))
    request_files = sorted((ROOT / 'calls').glob('*.request.json'))
    models = Counter()
    statuses = Counter()
    tokens = Counter()
    reasoning_present = 0
    attempts = []
    for p in request_files:
        request = read(p)['payload']
        assert request['model'] == 'qwen3.8-max'
        assert request['enable_thinking'] is False
        assert request['chat_template_kwargs']['enable_thinking'] is False
        prefix = p.name.removesuffix('.request.json')
        meta = read(p.with_name(prefix + '.meta.json'))
        statuses[str(meta.get('status', 'transport_error'))] += 1
        body = p.with_name(prefix + '.response.txt')
        if meta.get('status') == 200:
            value = read(body)
            models[value.get('model')] += 1
            message = value['choices'][0]['message']
            reasoning_present += bool(message.get('reasoning_content') or message.get('reasoning'))
            for k in ['prompt_tokens', 'completion_tokens', 'total_tokens']:
                tokens[k] += value.get('usage', {}).get(k, 0)
        attempts.append({'id': prefix, **meta})
    assert set(models) == {'qwen3.8-max'} and reasoning_present == 0
    results = []
    for row in final['run_results']:
        assert all(len(f['actions']) == 29 for f in row['findings'])
        results.append({'task_id': row['task_id'], 'score_0_100': row['run']['run_score_0_100'], 'finding_count': len(row['findings']), 'distinct_finding_count': row['run']['distinct_discovery_count'], 'top_discovery_quality_0_80': row['run']['top_discovery_quality_0_80'], 'yield_bonus_0_10': row['run']['yield_bonus_0_10'], 'target_recovery_0_10': row['run']['hidden_target_recovery_0_10'], 'false_claim_penalty_0_10': row['run']['deterministic_false_claim_penalty_0_10']})
    result = {'verified_at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'scope': 'V3.1 five final operator-assisted submissions', 'judge_model': final['model'], 'thinking_enabled': False, 'final_score_file': str(final_path), 'final_score_sha256': sha(final_path), 'scores': results, 'mean_score_0_100': round(statistics.mean(r['score_0_100'] for r in results), 2), 'seal_entries_unchanged': seal_count, 'evaluator_files_unchanged': len(source['evaluator_files']), 'scoring_call_count': len(request_files), 'response_models': dict(models), 'http_status_counts': dict(statuses), 'responses_with_reasoning_content': reasoning_present, 'usage_excluding_preflight': dict(tokens), 'closure_summary': read(ROOT / 'work/final/base_to_final_comparison.json')['summary'], 'all_attempts': attempts, 'limitations': ['Single Qwen3.8 Max judge pass; no manual score adjustments.', 'Final answers include operator feedback and are not first-autonomous-turn results.', 'Do not compare directly against historical scores produced by a different judge model.', 'Official evaluator uses text evidence and whitelisted numeric operations; a score is not exhaustive scientific validation.']}
    (ROOT / 'verified-summary.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k:v for k,v in result.items() if k != 'all_attempts'}, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
