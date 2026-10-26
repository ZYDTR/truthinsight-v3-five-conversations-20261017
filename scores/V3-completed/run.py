"""Run the unchanged official scorer; credentials exist only in child environment."""
from pathlib import Path
import datetime
import json
import os
import subprocess

ROOT = Path(__file__).resolve().parent
EVALUATOR = ROOT.parents[1] / 'TruthInsightBench/evaluation/evaluator'

def main():
    assert (ROOT / 'work/cohort.json').is_file(), 'Run prepare.py first.'
    assert not (ROOT / 'work/final/final_scoring_result.json').exists(), 'Final score already exists.'
    env = dict(os.environ)
    for key in ['DRY_RUN', 'SCORING_RUN_FILTER', 'MERGE_BASE_RESULT_PATH']:
        env.pop(key, None)
    env.update({
        'JUDGE_ENDPOINT': 'http://10.0.0.217:4000/v1/chat/completions',
        'JUDGE_MODEL': 'qwen3.8-max',
        'JUDGE_API_KEY': (Path.home() / '.local/share/litellm-local-relay/upstream.key').read_text().strip(),
        'JUDGE_CONCURRENCY': '4', 'CLOSURE_CONCURRENCY': '3',
        'SCORING_COHORT_PATH': str(ROOT / 'work/cohort.json'),
        'SCORING_OUT_DIR': str(ROOT / 'work/score'),
        'CLOSURE_BASE_SCORE_PATH': str(ROOT / 'work/score/scoring_result.json'),
        'CLOSURE_COHORT_PATH': str(ROOT / 'work/cohort.json'),
        'CLOSURE_OUT_DIR': str(ROOT / 'work/final'),
        'JUDGE_AUDIT_DIR': str(ROOT / 'calls'),
        'NODE_OPTIONS': '--import=' + str(ROOT / 'observe-fetch.mjs'),
    })
    for stage, module in [('score', 'score_cohort.mjs'), ('closure', 'finalize_scores.mjs')]:
        if stage == 'score' and (ROOT / 'work/score/scoring_result.json').exists():
            continue
        with (ROOT / (stage + '.log')).open('a') as log:
            log.write('\nSTART ' + datetime.datetime.now(datetime.timezone.utc).isoformat() + '\n')
            log.flush()
            result = subprocess.run(['/opt/homebrew/bin/node', str(EVALUATOR / module)], env=env, stdout=log, stderr=subprocess.STDOUT)
        (ROOT / (stage + '-exit.json')).write_text(json.dumps({'at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'returncode': result.returncode}, indent=2) + '\n')
        if result.returncode:
            raise SystemExit(result.returncode)
    print('SCORED ' + str(ROOT / 'work/final/final_scoring_result.json'))

if __name__ == '__main__':
    main()
