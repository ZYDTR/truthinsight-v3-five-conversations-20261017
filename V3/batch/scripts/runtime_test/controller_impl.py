import argparse,hashlib,json,shutil,subprocess,sys,time,uuid,os
from datetime import datetime,timezone
from pathlib import Path
import requests
E=Path(__file__).resolve().parents[2];SOURCE_E=E.parents[1];BASE=SOURCE_E.parents[1];ENV=Path(json.loads((E/'.local/active.json').read_text())['environment']);D='/usr/local/bin/docker';MODEL='qwen3.7-flash'
TASKS={'Chemistry_02_photoionization_delay':'chemistry','Physics_04_temporal_delay_transition':'physics','Astronomy_02_gravity_spectral_structure':'astronomy','EarthScience_01_glacial_fluvial_erosion':'earth','Neuro_02_calcium_response_regions':'neuro','probe':'probe','probe-wired':'probe'}
def stamp():return datetime.now(timezone.utc).isoformat()
def save(p,v):p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n');p.chmod(0o600)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def hashes(root):return {str(p.relative_to(root)):sha(p) for p in sorted(root.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}
def cfg():return json.loads((ENV/'ready.json').read_text())
def assignment(task=None):
 registry=json.loads((E/'control/ownership.json').read_text())
 sid=os.environ.get('OPENCODE_SESSION_ID','')
 entries=[x for x in registry['bindings'] if x['operator_session_id']==sid and x['state']=='active']
 if len(entries)!=1:raise RuntimeError('Unknown or revoked operator session')
 a=entries[0]
 if task is not None and task!=a['task_id']:raise RuntimeError('This operator owns exactly one task')
 return a

def prepare(task):
 assignment(task)
 run=E/'runs'/task
 if run.exists():raise RuntimeError('Run already exists')
 run.mkdir(parents=True);(run/'rounds').mkdir();(run/'private').mkdir();(run/'snapshots').mkdir()
 user=json.loads((ENV/'private/users.json').read_text())[TASKS[task]];cid=assignment(task)['conversation_id'];conv=ENV/'runtime_state/worker_data/users'/user['user_code']/'conversations'/('conv-'+cid);project=conv/'project'
 initial=run/'workspace'
 if task.startswith('probe'):
  initial.mkdir();(initial/'probe-input.csv').write_text('id,value\na,11\nb,17\nc,23\nd,31\n')
  prompt='这是独立非科研接线探针，不计正式任务。请读取 CLAUDE.md、context/INDEX.md 和共享 scientific-evidence Skill，然后根据用途读取委派与独立复核模块。请从 probe-input.csv 独立计算 value 总和及行数，委派一个原生 general-purpose 子 Agent 独立从此 CSV 重算，不让它派生 Agent；在委派中说明项目路径、需要读取的上下文、独立写入目录和验收条件。主 Agent 与子 Agent 分别保存可运行脚本和结果，主 Agent 读取子产物后比较。最终把证据路径和比较记录写入 output/probe-report.md。此目录没有科研题目文件，不能据此搜索其他工作区。'
  (initial/'LaunchPrompt.md').write_text(prompt)
 else:
  src=BASE/'runs'/task/'workspace'
  shutil.copytree(src,initial,ignore=shutil.ignore_patterns('output','__pycache__','*.pyc'))
  prompt=(initial/'LaunchPrompt.md').read_text()
 # Actual runtime UUID is resolved by the standard neutral warmup before seeding.
 # Current shared context must remain byte-identical to frozen subject.
 frozen=json.loads((ENV/'freeze.json').read_text())['subject'];assert hashes(SOURCE_E/'subject')==frozen
 manifest={'operator_session_id':assignment(task)['operator_session_id'],'task_id':task,'conversation_id':cid,'runtime_conversation_id':'conv-'+cid,'user_code':user['user_code'],'username':user['username'],'project':str(project),'created_at':stamp(),'input_hashes':hashes(initial),'shared_hashes':hashes(SOURCE_E/'subject/project'),'model':MODEL,'max_turns':500,'max_rounds':40,'environment':str(ENV),'state':'PREPARED'}
 save(run/'run.json',manifest);save(run/'private/auth.json',{'token':user['token']});(run/'first-message.md').write_text(prompt)
 print(json.dumps({'task':task,'prepared':str(run),'conversation_id':cid}),flush=True)
 return run
def seed(task):
 assignment(task)
 run=E/'runs'/task;m=json.loads((run/'run.json').read_text());project=Path(m['project']);project.mkdir(parents=True,exist_ok=True)
 shutil.copytree(run/'workspace',project,dirs_exist_ok=True);shutil.copytree(SOURCE_E/'subject/project',project,dirs_exist_ok=True)
 labels=['--label','codex.test=true','--label','codex.run_id='+ENV.name,'--label','codex.owner=/root/shared_v31_five_operators','--label','codex.cleanup=required']
 subprocess.run([D,'run','--rm',*labels,'--user','root','-v',str(ENV/'runtime_state/worker_data')+':/data',ENV.name+'-worker:candidate','chown','-R','10001:10001','/data/users/'+m['user_code']],check=True,capture_output=True)
 m['seeded_at']=stamp();m['state']='SEEDED';save(run/'run.json',m)
class Client:
 def __init__(self,run):
  self.run=Path(run);self.m=json.loads((self.run/'run.json').read_text());assert self.m['operator_session_id']==assignment(self.m['task_id'])['operator_session_id'];self.s=requests.Session();self.s.trust_env=False;self.s.headers['Authorization']='Bearer '+json.loads((self.run/'private/auth.json').read_text())['token'];self.base=cfg()['api_base'];self.prefix='/api/agent-runtime/conversations/'+self.m['conversation_id']
 def req(self,method,path,**kw):
  r=self.s.request(method,self.base+path,timeout=kw.pop('timeout',(15,120)),**kw)
  if not r.ok:
   p=self.run/'private'/('http-error-'+uuid.uuid4().hex[:6]+'.txt');p.write_bytes(r.content);raise RuntimeError(f'HTTP {r.status_code}: {path}; evidence={p}')
  return r
 def status(self):return self.req('GET',self.prefix+'/runtime-status').json()
def verify_ready(task):
 assignment(task)
 run=E/'runs'/task;m=json.loads((run/'run.json').read_text());project=Path(m['project'])
 changed=[p for p,h in m['input_hashes'].items() if not (project/p).is_file() or sha(project/p)!=h]
 shared=[p for p,h in m['shared_hashes'].items() if not (project/p).is_file() or sha(project/p)!=h]
 models=set()
 for p in (project.parent/'state/claude/projects').rglob('*.jsonl'):
  for line in p.read_text().splitlines():
   r=json.loads(line);model=(r.get('message') or {}).get('model')
   if r.get('type')=='assistant' and model and model!='<synthetic>':models.add(model)
 proof={'at':stamp(),'input_changed':changed,'shared_changed':shared,'actual_models':sorted(models),'passed':not changed and not shared and models=={MODEL}}
 save(run/'verify-seed.json',proof);assert proof['passed'], 'Input/shared integrity or actual model mismatch'
 frozen=E/'operator-bundle/manifest.json'
 if frozen.exists():
  fp=json.loads(frozen.read_text())
  for rel,h in fp['adapted_scripts_sha256'].items():assert sha(E/rel)==h, 'Frozen operator adapter changed: '+rel
 return proof

def send(task,input_path=None,warmup=False):
 assignment(task)
 if (E/'runs'/task/'sealed.json').exists():raise RuntimeError('Run is sealed; further sends forbidden')
 if not warmup:verify_ready(task)
 run=E/'runs'/task;c=Client(run);pre={'data':{'conversation_state':{'can_accept_input':True}},'pre_creation_warmup':True} if warmup else c.status();save(run/'pre-send-status.json',pre);assert pre['data']['conversation_state']['can_accept_input'], 'Conversation cannot accept input';rounds=[p for p in (run/'rounds').iterdir() if p.is_dir() and p.name!='000-warmup'];n=len(rounds)+1
 if n>40:raise RuntimeError('round budget')
 folder=run/'rounds'/('000-warmup' if warmup else f'{n:03d}');folder.mkdir();content=json.loads((BASE/'config/policy.json').read_text())['warmup_message'] if warmup else Path(input_path or run/'first-message.md').read_text();(folder/'input.md').write_text(content);payload={'content':content,'idempotency_key':ENV.name+'-qwen-v31-'+task+'-'+folder.name,'runtime_options':{'max_turns':1 if warmup else 500}};save(folder/'request.json',payload);save(folder/'sent.json',{'at':stamp()});start=time.monotonic();cursor=0;terminal=None;errors=[]
 try:
  receipt=c.req('POST',c.prefix+'/messages',json=payload,timeout=(15,60)).json();save(folder/'receipt.json',receipt);rid=receipt['data']['run_id'];print(json.dumps({'task':task,'round':n,'run_id':rid,'started':stamp()}),flush=True)
  with (folder/'events.jsonl').open('a') as ef,(folder/'events.sse').open('a') as sf:
   while terminal is None:
    if time.monotonic()-start>14400:raise TimeoutError('Observation window exceeded; inspect and cancel explicitly, never resend blindly')
    try:
     r=c.req('GET',c.prefix+'/runs/'+rid+'/events/stream',params={'after_sequence':cursor},headers={'Accept':'text/event-stream'},stream=True,timeout=(15,90));r.encoding='utf-8'
     with r:
      pending=[]
      for line in r.iter_lines(decode_unicode=True):
       sf.write(line+'\n');sf.flush()
       if line:pending.append(line);continue
       raw='\n'.join(x[5:].lstrip(' ') for x in pending if x.startswith('data:'));pending=[]
       if not raw or raw=='[DONE]':continue
       row=json.loads(raw);ef.write(json.dumps(row,ensure_ascii=False)+'\n');ef.flush()
       if isinstance(row.get('sequence'),int):cursor=max(cursor,row['sequence'])
       if row.get('type') in ['run.completed','run.failed','run.canceled']:
        terminal=row['type'];break
    except Exception as e:
     errors.append({'at':stamp(),'type':type(e).__name__,'error':str(e)});save(folder/'stream-errors.json',errors);time.sleep(3)
    if terminal is None:
     st=c.status();save(folder/'latest-status.json',st)
     data=st.get('data',{})
     if data.get('conversation_state',{}).get('can_accept_input') and data.get('status') in ['completed','failed','canceled']:terminal='status.'+data['status']
  for _ in range(60):
   st=c.status();save(folder/'status.json',st)
   if st.get('data',{}).get('conversation_state',{}).get('can_accept_input'):break
   time.sleep(1)
 finally:
  save(folder/'execution.json',{'finished_at':stamp(),'seconds':time.monotonic()-start,'terminal':terminal,'cursor':cursor,'stream_errors':errors})
 if warmup:
  st=c.status()['data'];m=c.m;m['runtime_conversation_id']=st['runtime_conversation_id'];m['project']=str(ENV/'runtime_state/worker_data/users'/m['user_code']/'conversations'/st['runtime_conversation_id']/'project');save(run/'run.json',m)
  seed(task)
 collect(task)
 print(json.dumps({'task':task,'round':n,'terminal':terminal,'seconds':round(time.monotonic()-start,1)}),flush=True)
def collect(task):
 assignment(task)
 run=E/'runs'/task;m=json.loads((run/'run.json').read_text());project=Path(m['project']);conv=project.parent;destination=run/'snapshots'/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+uuid.uuid4().hex[:5]);destination.mkdir()
 shutil.copytree(project,destination/'project',symlinks=True)
 # Original JSONL, actual appended system prompt and runtime state preserved.
 for rel in ['state/claude/projects','state/home/.agent-runtime/system-prompts']:
  src=conv/rel
  if src.exists():shutil.copytree(src,destination/rel,symlinks=True)
 meta=ENV/'runtime_state/users'/m['user_code']/'conversations'/m['runtime_conversation_id']
 if meta.exists():shutil.copytree(meta,destination/'runtime-metadata',symlinks=True)
 missing=[p for p,h in m['input_hashes'].items() if not (project/p).is_file() or sha(project/p)!=h]
 shared=[p for p,h in m['shared_hashes'].items() if not (project/p).is_file() or sha(project/p)!=h]
 models={};files=[]
 for p in sorted((destination/'state').rglob('*.jsonl')):
  files.append(str(p.relative_to(destination)))
  for line in p.read_text(errors='replace').splitlines():
   try:r=json.loads(line)
   except:continue
   model=(r.get('message') or {}).get('model')
   if r.get('type')=='assistant' and model:models[model]=models.get(model,0)+1
 proof={'task':task,'snapshot':str(destination),'at':stamp(),'input_changed':missing,'shared_changed':shared,'jsonl_files':files,'model_counts':models,'manifest':hashes(destination)};save(destination/'collection.json',proof)
 if not task.startswith('probe') and any((run/'rounds').glob('[0-9][0-9][0-9]')):
  p=subprocess.run([sys.executable,'-B',str(run/'workspace/validate_output.py'),str(destination/'project/output'),'--receipt',str(destination/'submission_validation.json')],capture_output=True,text=True)
  (destination/'validator.stdout').write_text(p.stdout);(destination/'validator.stderr').write_text(p.stderr);proof['validator_returncode']=p.returncode
  if (destination/'submission_validation.json').exists():proof['validation']=json.loads((destination/'submission_validation.json').read_text())
 for p in destination.rglob('*'):
  if p.is_file():p.chmod(0o600)
  elif p.is_dir():p.chmod(0o700)
 destination.chmod(0o700)
 save(run/'latest-collection.json',proof)
 print(json.dumps({k:proof[k] for k in ['task','snapshot','input_changed','shared_changed','model_counts']}|{'validator_returncode':proof.get('validator_returncode')}),flush=True)
