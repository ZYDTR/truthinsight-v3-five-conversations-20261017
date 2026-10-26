#!/usr/bin/env python3
"""Offline archival only: no model calls, network requests, or scientific reruns."""
from pathlib import Path
import collections
import csv
import datetime as dt
import hashlib
import io
import json
import os
import re
import sqlite3
import sys
import zipfile

BASE = Path(__file__).resolve().parents[1]
H = BASE.parents[1]
WS = H.parents[1]
ROOT = BASE / 'truthinsight-v3-five-conversations-20261017'
E = H / 'experiments/shared-context-v3.1-20261016'
B = E / 'batches/qwen3.7-flash-main-6d52948-20261016'
ENV = E / '.local/tibv31-9a7ed51f'
S3 = H / 'evaluations/shared-context-v31-qwen38max-nothinking-20261017'
NOW = dt.datetime.now(dt.timezone.utc).isoformat()
TASKS = [x['task_id'] for x in json.loads((B / 'control/ownership.json').read_text())['bindings']]
NAMES = dict(zip(TASKS, ['光电离延迟', '时间延迟转变', '引力谱结构', '冰川与河流侵蚀', '钙信号区域差异']))
ROOT.mkdir(parents=True, exist_ok=False)
os.chmod(BASE, 0o700)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def js(obj):
    return (json.dumps(obj, ensure_ascii=False, indent=2) + '\n').encode()

def write(rel, data):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data.encode() if isinstance(data, str) else data)
    p.chmod(0o600)
    return p

sources = []
redactions = []
excluded = []
secrets = set()
credential_key = re.compile(r'(?:api[_-]?key|access[_-]?token|refresh[_-]?token|password|secret|authorization|auth_header|encrypted_value)', re.I)

def remember(v):
    if isinstance(v, str) and len(v) >= 8 and v not in ('[REDACTED]', 'REDACTED', 'undefined') and not v.startswith(('${', '<', '/')):
        secrets.add(v.encode())

def collect(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if credential_key.search(k) or k.lower() in ('token', 'key'):
                remember(v)
            else:
                collect(v)
    elif isinstance(obj, list):
        for v in obj:
            collect(v)

for p in [ENV / 'private/users.json']:
    collect(json.loads(p.read_text()))
for p in [ENV / 'private/route.env', Path.home() / '.local/share/litellm-local-relay/upstream.key']:
    if not p.exists():
        continue
    if p.suffix == '.key':
        remember(p.read_text().strip())
    else:
        for line in p.read_text().splitlines():
            if '=' in line:
                k, v = line.split('=', 1)
                if credential_key.search(k) or 'TOKEN' in k:
                    remember(v.strip().strip('\"\''))

# Read COPY headers/cells, never emit credential values. Collect DB-contained
# credentials as exact values so their occurrences in logs are redacted too.
sql = ENV / 'private/final-database.sql'
sql_columns = []
sql_table = None
sql_inventory = []
sql_entry = None
for line in sql.open():
    if line.startswith('COPY '):
        m = re.match(r'COPY public\.([^ ]+) \((.*)\) FROM stdin;', line)
        sql_table = m[1]
        sql_columns = [x.strip().strip('"') for x in m[2].split(',')]
        sql_entry = {'table': sql_table, 'columns': sql_columns, 'rows': 0}
        sql_inventory.append(sql_entry)
    elif line.rstrip('\n') == '\\.':
        sql_table = None
    elif sql_table:
        sql_entry['rows'] += 1
        cells = line.rstrip('\n').split('\t')
        if len(cells) != len(sql_columns):
            raise ValueError('Unexpected SQL COPY row shape')
        for k, v in zip(sql_columns, cells):
            if credential_key.search(k) and v != r'\N':
                remember(v)
        if sql_table == 'system_configs':
            d = dict(zip(sql_columns, cells))
            if credential_key.search(d['key']) or 'TOKEN' in d['key']:
                remember(d.get('value'))
                remember(d.get('previous_value'))

# Patterns only target token-shaped secrets; hashes and scientific text remain.
patterns = [
    ('jwt', re.compile(rb'eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}')),
    ('api_key', re.compile(rb'\bsk-[A-Za-z0-9_-]{16,}')),
]
if secrets:
    patterns.insert(0, ('known_credential', re.compile(b'|'.join(re.escape(x) for x in sorted(secrets, key=len, reverse=True)))))

def sanitize(data, rel):
    edits = {}
    for name, pattern in patterns:
        data, count = pattern.subn(b'[REDACTED_CREDENTIAL]', data)
        if count:
            edits[name] = count
    if edits:
        redactions.append({'path': str(rel), 'replacements': edits})
    return data

def copy(p, rel):
    if p.is_symlink():
        raise ValueError('Unexpected symlink: ' + str(p))
    raw = p.read_bytes()
    packed = sanitize(raw, rel)
    write(rel, packed)
    sources.append({'path': str(rel), 'source': str(p), 'source_bytes': len(raw), 'source_sha256': sha(raw), 'bytes': len(packed), 'sha256': sha(packed), 'credential_redacted': raw != packed})

def tree(src, dest, omit=()):
    for p in sorted(src.rglob('*')):
        if not p.is_file():
            continue
        r = p.relative_to(src)
        if any(x in r.parts for x in omit):
            excluded.append({'source': str(p), 'reason': '非实验产物：运行缓存或源码版本控制元数据'})
            continue
        copy(p, Path(dest) / r)

seal_results = []
for task in TASKS:
    seal = json.loads((B / 'runs' / task / 'sealed.json').read_text())
    assert seal['state'] == 'SEALED'
    for rel, digest in seal['manifest'].items():
        p = Path(seal['snapshot']) / rel
        assert sha(p.read_bytes()) == digest, str(p)
    seal_results.append({'task_id': task, 'entries': len(seal['manifest']), 'verified': True})
print(json.dumps({'stage': 'source_seals_verified', 'entries': sum(x['entries'] for x in seal_results)}), flush=True)

tree(B, 'V3/batch')
for name in ('subject', 'docs', 'scripts'):
    tree(E / name, 'V3/experiment/' + name, omit=('__pycache__',))
for p in E.iterdir():
    if p.is_file():
        copy(p, 'V3/experiment/' + p.name)
tree(H / 'experiments/operator-control-v2', 'V3/operator-control-v2')
for p in sorted(ENV.iterdir()):
    if p.name == 'source':
        excluded.append({'source': str(p), 'reason': '通用后端源码副本；保留版本清单、构建日志、实际差异和运行产物'})
    elif p.is_dir():
        tree(p, 'V3/environment/' + p.name)
    else:
        copy(p, 'V3/environment/' + p.name)
write('V3/environment/database-table-index.json', js(sql_inventory))
print(json.dumps({'stage': 'v3_artifacts_copied', 'source_files': len(sources)}), flush=True)

# Export only the five exact owner sessions from the current OpenCode schema.
# No account/credential tables or unrelated sessions are copied.
db = WS / 'tmp/opencode_new/data/opencode/opencode.db'
conn = sqlite3.connect(f'file:{db}?mode=ro', uri=True)
conn.row_factory = sqlite3.Row
conn.execute('BEGIN')
operator_counts = {}
for task in TASKS:
    run = json.loads((B / 'runs' / task / 'run.json').read_text())
    sid = run['operator_session_id']
    prefix = Path('V3/operators') / task
    session = conn.execute('SELECT * FROM session_v2 WHERE id=?', (sid,)).fetchone()
    assert session is not None
    raw_session = dict(session)
    write(prefix / 'session.json', sanitize(js(raw_session), prefix / 'session.json'))
    rows = [dict(r) for r in conn.execute('SELECT * FROM session_message WHERE session_id=? ORDER BY seq', (sid,))]
    raw = b''.join((json.dumps(r, ensure_ascii=False) + '\n').encode() for r in rows)
    write(prefix / 'messages.raw.jsonl', sanitize(raw, prefix / 'messages.raw.jsonl'))
    decoded = [{**r, 'data': json.loads(r['data'])} for r in rows]
    write(prefix / 'messages.decoded.json', sanitize(js(decoded), prefix / 'messages.decoded.json'))
    extra = {}
    for t in ('todo', 'session_inbox', 'instruction_entry', 'instruction_state'):
        extra[t] = [dict(r) for r in conn.execute(f'SELECT * FROM {t} WHERE session_id=?', (sid,))]
    references = set(re.findall(r'(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])', json.dumps(extra)))
    blobs = []
    for digest in sorted(references):
        row = conn.execute('SELECT hash, value FROM instruction_blob WHERE hash=?', (digest,)).fetchone()
        if row is not None:
            blobs.append(dict(row))
    write(prefix / 'instruction-blobs.json', sanitize(js(blobs), prefix / 'instruction-blobs.json'))
    write(prefix / 'context-state.json', sanitize(js(extra), prefix / 'context-state.json'))
    md = [f'# {NAMES[task]} — V3 操作者记录', '', f'OpenCode session：`{sid}`。从原生 session_message 表只读导出；保留全部消息类型及工具块。', '', '[原始 JSONL](messages.raw.jsonl) · [解码 JSON](messages.decoded.json) · [会话元数据](session.json)', '']
    for r in decoded:
        d = r['data']
        md += [f'## seq {r["seq"]} · {r["type"]}', '']
        if 'text' in d:
            md += [str(d['text']), '']
        for block in d.get('content', []):
            if isinstance(block, dict) and isinstance(block.get('text'), str):
                md += [f'### {block.get("type", "text")}', '', block['text'], '']
            else:
                md += ['````json', json.dumps(block, ensure_ascii=False, indent=2), '````', '']
        if not d.get('content') and 'text' not in d:
            md += ['````json', json.dumps(d, ensure_ascii=False, indent=2), '````', '']
    write(prefix / 'transcript.md', sanitize('\n'.join(md).encode(), prefix / 'transcript.md'))
    operator_counts[task] = {'session_id': sid, 'messages': len(rows), 'types': dict(collections.Counter(r['type'] for r in rows)), 'raw_sha256_before_redaction': sha(raw), 'exported_at': NOW}
conn.rollback()
conn.close()
write('V3/operators/export-receipt.json', js({'source_database': str(db), 'source_schema': 'session_v2/session_message', 'scope': 'five exact owner sessions only', 'read_only': True, 'sessions': operator_counts}))

tree(S3, 'scores/V3-completed', omit=('__pycache__',))
scorer_manifest = json.loads((S3 / 'source-manifest.json').read_text())
for rel, digest in scorer_manifest['evaluator_files'].items():
    p = H / 'TruthInsightBench' / rel
    assert sha(p.read_bytes()) == digest, str(p)
    copy(p, 'scorer/TruthInsightBench/' + rel)
for p in (H / 'TruthInsightBench').iterdir():
    if p.is_file() and (p.name.lower().startswith(('license', 'readme')) or p.name in ('requirements.txt', 'pyproject.toml', 'package.json', 'package-lock.json')):
        if not (ROOT / 'scorer/TruthInsightBench' / p.name).exists():
            copy(p, 'scorer/TruthInsightBench/' + p.name)
write('scorer/source-binding.json', js({'unchanged_files': len(scorer_manifest['evaluator_files']), 'hashes': scorer_manifest['evaluator_files'], 'note': '评分器冻结资产完整保留，含注册表引用的其他题资产；其他题的 conversation 未打包。'}))
copy(Path(__file__), 'tools/build_archive.py')

summary = json.loads((S3 / 'verified-summary.json').read_text())
scores = {r['task_id']: r['score_0_100'] for r in summary['scores']}
jsonls = []
for p in sorted(ROOT.rglob('*.jsonl')):
    rel = str(p.relative_to(ROOT))
    count = 0
    invalid = []
    for n, line in enumerate(p.read_bytes().splitlines(), 1):
        if not line.strip():
            continue
        count += 1
        try:
            json.loads(line)
        except (ValueError, UnicodeDecodeError):
            invalid.append(n)
    jsonls.append({'path': rel, 'lines': count, 'invalid_lines': invalid, 'sha256': sha(p.read_bytes()), 'kind': 'operator' if '/operators/' in rel else ('subagent' if '/subagents/' in rel else ('main-agent' if '/projects/' in rel else 'other'))})
write('indexes/jsonl-inventory.json', js(jsonls))

task_indexes = []
score_bindings = []
for task in TASKS:
    run = json.loads((B / 'runs' / task / 'run.json').read_text())
    seal_path = B / 'runs' / task / 'sealed.json'
    seal = json.loads(seal_path.read_text())
    sr = Path('V3/batch') / Path(seal['snapshot']).relative_to(B)
    final = sr / 'project/output/Result.md'
    assert (ROOT / final).exists()
    receipt = json.loads((S3 / 'exports' / task / 'run_receipt.json').read_text())
    assert receipt['source_seal'] == str(seal_path)
    assert receipt['source_seal_sha256'] == sha(seal_path.read_bytes())
    assert receipt['source_snapshot'] == seal['snapshot']
    source_output = Path(seal['snapshot']) / 'project/output'
    export_output = S3 / 'exports' / task / 'workspace/output'
    source_hashes = {str(p.relative_to(source_output)): sha(p.read_bytes()) for p in source_output.rglob('*') if p.is_file()}
    export_hashes = {str(p.relative_to(export_output)): sha(p.read_bytes()) for p in export_output.rglob('*') if p.is_file()}
    assert source_hashes == export_hashes, task + ' grading export mismatch'
    score_bindings.append({'task_id': task, 'conversation_id': run['conversation_id'], 'source_seal_sha256': sha(seal_path.read_bytes()), 'scored_output_files': len(export_hashes), 'all_scored_files_match_sealed_output': True, 'score_0_100': scores[task], 'subject_commit': receipt['subject_commit'], 'harness_version': receipt['harness_version']})
    logs = [x for x in jsonls if x['path'].startswith('V3/batch/runs/' + task + '/') or x['path'].startswith('V3/operators/' + task + '/') or run['runtime_conversation_id'] in x['path']]
    entry = {'task_id': task, 'name': NAMES[task], 'version': 'V3 (3.1.0)', 'conversation_id': run['conversation_id'], 'runtime_conversation_id': run['runtime_conversation_id'], 'operator_session_id': run['operator_session_id'], 'sealed_at': seal['at'], 'sealed_snapshot': str(sr), 'final_report': str(final), 'raw_jsonl_paths': [x['path'] for x in logs], 'score_state': 'COMPLETED', 'final_score_0_100': scores[task], 'scientific_round_count': receipt['scientific_round_count']}
    task_indexes.append(entry)
    md = [f'# {NAMES[task]}：V3', '', f'题目：`{task}`。上下文版本：3.1.0。最终封存时间：{seal["at"]}。', '', f'- SAP conversation：`{run["conversation_id"]}`', f'- Runtime conversation：`{run["runtime_conversation_id"]}`', f'- 唯一操作者：`{run["operator_session_id"]}`', '', f'[最终 Result.md](../{final}) · [完整封存快照](../{sr}) · [全部轮次与快照](../V3/batch/runs/{task})', '', f'[执行报告](../V3/batch/runs/{task}/docs/execution-report.md) · [操作者全文](../V3/operators/{task}/transcript.md) · [封存回执](../V3/batch/runs/{task}/sealed.json)', '', f'**已有最终评分：{scores[task]} / 100**。[评分汇总](../scores/README.md) · [对应评分输入与回执](../scores/V3-completed/exports/{task})。评分导出文件与本会话最终封存产物逐文件哈希一致。', '', '## 原始 JSONL', '', '保留全部快照里的 JSONL，不按内容去重。文件数量不等于独立 Agent 数量。', '', '| 类型 | 行数 | 文件 |', '|---|---:|---|']
    for x in logs:
        md.append(f'| {x["kind"]} | {x["lines"]} | [{x["path"]}](../{x["path"]}) |')
    write('indexes/' + task + '.md', '\n'.join(md) + '\n')
assert sha((S3 / 'work/final/final_scoring_result.json').read_bytes()) == summary['final_score_sha256']
write('indexes/scoring-to-conversation-binding.json', js({'all_five_match': True, 'final_score_sha256': summary['final_score_sha256'], 'bindings': score_bindings}))

write('indexes/conversations.json', js(task_indexes))
write('indexes/source-files.json', js(sources))
write('indexes/redactions.json', js({'policy': '仅替换凭据值，原件保留不变；未删除消息、工具调用或科研产物。脱敏文件的原始与归档哈希见 source-files.json；操作者导出另有 export-receipt.json。', 'files': redactions}))
write('indexes/exclusions.json', js(excluded))
write('indexes/source-verification.json', js({'at': NOW, 'seals': seal_results, 'evaluator_files_verified': len(scorer_manifest['evaluator_files']), 'new_model_calls': 0, 'scoring_state': 'COMPLETED', 'jsonl_files': len(jsonls), 'jsonl_invalid_lines': sum(len(x['invalid_lines']) for x in jsonls)}))

score_md = ['# V3 已有评分', '', '这份评分对应包内五个 V3 conversation 的最终封存提交。实际共享上下文版本为 3.1.0。此次仅归档，没有新评分调用。', '', 'Judge：`qwen3.8-max`，thinking 关闭，原版 TruthInsightBench V1.0 评分器。', '', '[核验汇总](V3-completed/verified-summary.json) · [最终评分 JSON](V3-completed/work/final/final_scoring_result.json) · [初评到最终差异](V3-completed/work/final/base_to_final_comparison.json) · [原始调用](V3-completed/calls) · [评分与会话逐题绑定](../indexes/scoring-to-conversation-binding.json)', '', '| 题目 | 最终分 / 100 |', '|---|---:|']
for task in TASKS:
    score_md.append(f'| {NAMES[task]} | {scores[task]} |')
score_md += ['', f'平均分 **{summary["mean_score_0_100"]}**。这是含操作者反馈的最终提交评分；20 个发现中，数值复算覆盖 3 个，16 个完成检索、4 个使用冻结参考资料。`work/score/scoring_result.*` 是初评，请以 `work/final/final_scoring_result.json` 为准。', '', '五题评分导出与对应会话的最终 output 逐文件哈希一致；原始请求、返回、失败重试、复核材料与评分器均完整保留。']
write('scores/README.md', '\n'.join(score_md) + '\n')

readme = ['# TruthInsightBench V3 五题完整产物与评分', '', '**本包包含 V3 的五个 SAP conversation 及其对应的已有正式评分。** 实际共享上下文版本为 3.1.0。全部轮次、全部快照、最终科研产物、原始主子 Agent JSONL、操作者会话、环境清理前运行目录与服务日志均收入。', '', '此次仅离线归档，未新增科研运行或评分。历史过程报告中的“不评分”是当时操作者边界；最终分来自用户后来授权的独立后置评分。', '', '## 从这里看', '', '| 题目 | 全过程与 JSONL 索引 | 最终报告 | 已有分数 / 100 |', '|---|---|---|---:|']
for row in task_indexes:
    readme.append(f'| {row["name"]} | [索引](indexes/{row["task_id"]}.md) | [Result.md]({row["final_report"]}) | {row["final_score_0_100"]} |')
readme += ['', '[评分与原始调用](scores/README.md) · [全部文件清单](indexes/files.csv) · [JSONL 清单](indexes/jsonl-inventory.json) · [会话绑定](indexes/conversations.json)', '', '## 目录', '', '```text', 'V3/', '  batch/runs/<task>/      全轮次、快照、科研文件、审读/比较报告、反馈与收据', '  batch/docs/            批次进度、结果质量审读及完成记录', '  batch/.local/          root 过程审查与派发回执', '  experiment/subject/    当时冻结的 CLAUDE.md、Skill、系统提示词', '  operators/<task>/      五个操作者的原生 JSONL、可读全文及引用上下文', '  environment/           清理前运行目录、主子状态、服务日志与版本证据', '    private/             脱敏后的数据库快照与环境资料', 'scores/V3-completed/     对应正式评分、原始调用、闭环材料与评分输入', 'scorer/                  当次评分器及其 578 个冻结资产', 'indexes/                 分题索引、文件清单、来源哈希、评分绑定与脱敏记录', 'MANIFEST.sha256          除自身外的逐文件 SHA-256', '```', '', '被测主子模型：`qwen3.7-flash`；外层操作者：`windows-glm/GLM-5.3-Flash-W4A16-MTP`。共享上下文 3.1.0 冻结于 `52fff1847bec1a2f82b1abd8e23caeda979dea21`；后端 `6d529489815362eb2d6cf717e736e44936de3afc`。', '', '## 完整性与边界', '', '五题封存清单的 444 个条目已重新核验。评分所用 output 与相应最终封存 output 逐文件一致，详见 [评分绑定核验](indexes/scoring-to-conversation-binding.json)。全部快照保留，重复文件未去重。JSONL 逐行检查见 [核验记录](indexes/source-verification.json)。', '', '凭据只在打包副本中替换，原件保留。[脱敏清单](indexes/redactions.json) 与 [来源哈希](indexes/source-files.json) 可追溯变化。操作者 JSONL 完整保留消息与工具块，并附按哈希引用的上下文正文。', '', '通用后端源码副本、外部账户凭据库和其他版本的运行批次未打包；本轮已有 V2/V3 比较报告仍保留。数据库是专用实验环境的清理前快照，其中可能含环境探测记录，不计作第六道题。历史文件内绝对路径保留，新建索引用包内相对路径。', '', '解压后运行 `python3 tools/verify_archive.py` 验证逐文件哈希。ZIP 外另附压缩包 SHA-256 和核验回执。', '']
write('README.md', '\n'.join(readme))

verifier = '''from pathlib import Path
import hashlib
root = Path(__file__).resolve().parents[1]
n = 0
for line in (root / "MANIFEST.sha256").read_text().splitlines():
    digest, rel = line.split("  ", 1)
    p = root / rel
    h = hashlib.sha256()
    with p.open("rb") as f:
        for block in iter(lambda: f.read(1024*1024), b""):
            h.update(block)
    assert h.hexdigest() == digest, rel
    n += 1
print(f"PASS: {n} files")
'''
write('tools/verify_archive.py', verifier)

files = [{'path': str(p.relative_to(ROOT)), 'bytes': p.stat().st_size, 'sha256': sha(p.read_bytes())} for p in sorted(ROOT.rglob('*')) if p.is_file()]
csvout = io.StringIO()
writer = csv.DictWriter(csvout, fieldnames=['path', 'bytes', 'sha256'])
writer.writeheader()
writer.writerows(files)
write('indexes/files.csv', '\ufeff' + csvout.getvalue())
files.append({'path': 'indexes/files.csv', 'bytes': (ROOT / 'indexes/files.csv').stat().st_size, 'sha256': sha((ROOT / 'indexes/files.csv').read_bytes())})
write('MANIFEST.sha256', ''.join(f'{x["sha256"]}  {x["path"]}\n' for x in sorted(files, key=lambda x: x['path'])))

# Ensure newly authored navigation points resolve; original historical documents
# retain original paths and are not silently rewritten.
broken = []
for p in [ROOT / 'README.md', ROOT / 'scores/README.md', *sorted((ROOT / 'indexes').glob('*.md'))]:
    for link in re.findall(r'\]\(([^)]+)\)', p.read_text()):
        if '://' not in link and not (p.parent / link).exists():
            broken.append({'file': str(p.relative_to(ROOT)), 'link': link})
assert not broken, broken

# All input files remain unchanged after copy.
for entry in sources:
    assert sha(Path(entry['source']).read_bytes()) == entry['source_sha256'], entry['source']
print(json.dumps({'stage': 'copied_and_indexed', 'files': len(files) + 1, 'raw_jsonl_files': len(jsonls), 'redacted_files': len(redactions)}), flush=True)

zip_path = BASE / (ROOT.name + '.zip')
with zipfile.ZipFile(zip_path, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as z:
    for p in sorted(ROOT.rglob('*')):
        if p.is_file():
            z.write(p, ROOT.name + '/' + str(p.relative_to(ROOT)))
zip_path.chmod(0o600)
with zipfile.ZipFile(zip_path) as z:
    expected = {x['path']: x['sha256'] for x in files}
    assert len(z.namelist()) == len(files) + 1
    for rel, digest in expected.items():
        assert sha(z.read(ROOT.name + '/' + rel)) == digest, rel
    assert z.testzip() is None
zip_hash = sha(zip_path.read_bytes())
(BASE / (zip_path.name + '.sha256')).write_text(zip_hash + '  ' + zip_path.name + '\n')
receipt = {'at': dt.datetime.now(dt.timezone.utc).isoformat(), 'state': 'COMPLETE', 'scope': 'V3 (actual context 3.1.0) five complete conversations with their matching existing scores', 'archive': str(zip_path), 'archive_bytes': zip_path.stat().st_size, 'archive_sha256': zip_hash, 'archive_files': len(files) + 1, 'source_files': len(sources), 'raw_jsonl_files': len(jsonls), 'operator_sessions': 5, 'sealed_entries_verified': sum(x['entries'] for x in seal_results), 'scorer_files_verified': 578, 'archive_crc_verified': True, 'archive_entry_hashes_verified': len(files), 'source_files_unchanged': True, 'new_index_links_verified': True, 'redacted_files': len(redactions), 'new_model_calls': 0, 'scoring_state': 'COMPLETED', 'all_five_scoring_bindings_verified': True}
(BASE / 'verification.json').write_bytes(js(receipt))
print(json.dumps(receipt, ensure_ascii=False), flush=True)
