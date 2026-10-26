"""只由主线程执行：五个 OpenCode session，一人一题，派发文本完全相同。"""
import base64,json,sys,urllib.request,urllib.error,uuid
from pathlib import Path
from datetime import datetime,timezone
E=Path(__file__).resolve().parents[1]
V=E.parents[1]
ROOT=V.parents[3]
P=E/'.local/opencode'
P.mkdir(parents=True,exist_ok=True);P.chmod(0o700)
service=json.loads((Path.home()/'.local/state/opencode/service.json').read_text())
auth='Basic '+base64.b64encode(('opencode:'+service['password']).encode()).decode()
def save(p,v):
 p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n');p.chmod(0o600)
def api(path,method='GET',data=None):
 req=urllib.request.Request(service['url']+path,method=method,data=None if data is None else json.dumps(data,ensure_ascii=False).encode(),headers={'Authorization':auth,'Content-Type':'application/json'})
 try:
  with urllib.request.urlopen(req,timeout=45) as r:
   raw=r.read();return json.loads(raw) if raw else {'http_status':r.status}
 except urllib.error.HTTPError as e:
  (P/'last-http-error.txt').write_bytes(e.read());(P/'last-http-error.txt').chmod(0o600);raise RuntimeError('HTTP '+str(e.code)+'; private error saved') from None

def start():
 from activate import require_gate
 require_gate()
 proof=json.loads((E/'docs/environment-verification.json').read_text())
 assert proof['passed'], 'V3 environment verification missing'
 previous=Path(json.loads((E/'control/run-spec.json').read_text())['predecessor_gate']['batch'])
 prior=json.loads((previous/'control/ownership.json').read_text())['bindings']
 active=api('/api/session/active');save(P/'predecessor-active.json',active)
 assert not any(x['operator_session_id'] in active.get('data',{}) for x in prior), 'V2 operators still finishing; wait without interruption'
 for x in prior:
  inbox=api('/api/session/'+x['operator_session_id']+'/inbox')
  assert not inbox.get('data',[]), 'V2 operator inbox not empty'
 spec=json.loads((E/'control/run-spec.json').read_text());claim=P/'dispatch-claim.json'
 with claim.open('x') as f:json.dump({'started_at':datetime.now(timezone.utc).isoformat()},f)
 bindings=[]
 for i,task in enumerate(spec['tasks']):
  title='TruthInsight V3.1 · '+task['task_id']+' · 单题操作者 · 不评分'
  payload={'title':title,'model':{'id':spec['operator']['model']['modelID'],'providerID':spec['operator']['model']['providerID']},'location':{'directory':str(ROOT)},'permissions':[{'action':'*','resource':'*','effect':'allow'},{'action':'task','resource':'*','effect':'deny'},{'action':'agent','resource':'*','effect':'deny'}]}
  result=api('/api/session','POST',payload);save(P/('created-'+str(i)+'.json'),result)
  bindings.append({'task_id':task['task_id'],'operator_session_id':result['data']['id'],'conversation_id':str(uuid.uuid4()),'state':'active','title':title})
 assert len({a['operator_session_id'] for a in bindings})==5 and len({a['conversation_id'] for a in bindings})==5
 save(E/'control/ownership.json',{'schema':'one-operator-one-conversation-v3','bindings':bindings,'predecessor_sessions':[x['operator_session_id'] for x in prior],'model_parameter_omitted':False,'model_pinned_to_v2_actual':spec['operator']['model'],'created_at':datetime.now(timezone.utc).isoformat()})
 prompt=(E/'control/dispatch-prompt.txt').read_text()
 for i,a in enumerate(bindings):
  receipt=api('/api/session/'+a['operator_session_id']+'/prompt','POST',{'text':prompt});save(P/('receipt-'+str(i)+'.json'),receipt)
 save(E/'docs/dispatch.json',{'at':datetime.now(timezone.utc).isoformat(),'bindings':bindings,'prompt_sha256':__import__('hashlib').sha256(prompt.encode()).hexdigest(),'model_parameter_omitted':False,'model_pinned_to_v2_actual':spec['operator']['model'],'workspace':str(ROOT)})
 print(json.dumps({'dispatched':5,'bindings':bindings},ensure_ascii=False,indent=2))

def status():
 bindings=json.loads((E/'control/ownership.json').read_text())['bindings'];all_sessions=api('/api/session?limit=100');save(P/'session-tree.json',all_sessions);report=[]
 for a in bindings:
  sid=a['operator_session_id'];page=api('/api/session/'+sid+'/message?limit=100&order=desc');save(P/(sid+'-messages.json'),page);rows=page.get('data',[])
  models=[];last_tools=[]
  for r in rows:
   if r.get('type')=='assistant' and r.get('model') and r['model'] not in models:models.append(r['model'])
   for block in r.get('content',[]):
    if isinstance(block,dict) and block.get('type')=='tool':last_tools.append({'name':block.get('name'),'status':block.get('state',{}).get('status')})
  children=[r['id'] for r in all_sessions.get('data',[]) if r.get('parentID',r.get('parentId'))==sid]
  report.append({'task_id':a['task_id'],'session_id':sid,'actual_models':models,'message_count':len(rows),'recent_tools':last_tools[:3],'nested_sessions':children})
 save(E/'docs/startup-check.json',{'at':datetime.now(timezone.utc).isoformat(),'operators':report,'scope':'bounded session listing plus direct children; not a full historical audit'})
 print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':
 if sys.argv[1]=='start':start()
 elif sys.argv[1]=='status':status()
 else:raise SystemExit('start|status')
