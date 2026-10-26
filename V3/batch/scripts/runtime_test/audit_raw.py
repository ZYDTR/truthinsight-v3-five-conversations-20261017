"""Index original JSONL for human/agent inspection; never substitutes for review."""
import json,hashlib,sys,re
from pathlib import Path
from collections import Counter
E=Path(__file__).resolve().parents[2]
def audit(task):
 run=E/'runs'/task;col=json.loads((run/'latest-collection.json').read_text());s=Path(col['snapshot']);main=[];agents=[];requests={};models=Counter();efforts=set();records=[];tool_counts=Counter();errors=[]
 for p in sorted((s/'state').rglob('*.jsonl')):
  rows=p.read_text().splitlines();ref=str(p.relative_to(s));info={'file':ref,'line_count':len(rows),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'reads':[],'delegations':[],'tools':[]}
  for i,line in enumerate(rows,1):
   try:r=json.loads(line)
   except ValueError:errors.append({'file':ref,'line':i,'parse_error':True});continue
   msg=r.get('message') or {};content=msg.get('content');typ=r.get('type'); loc=ref+':'+str(i)
   if typ=='assistant':
    if msg.get('model'):models[msg['model']]+=1
    if r.get('effort'):efforts.add(r['effort'])
    if msg.get('id'):
     prev=requests.get(msg['id'],{});u=msg.get('usage') or {}
     if u.get('input_tokens',0)+u.get('output_tokens',0)>=prev.get('input_tokens',0)+prev.get('output_tokens',0):requests[msg['id']]=u
   if isinstance(content,list):
    for b in content:
     if not isinstance(b,dict):continue
     if b.get('type')=='tool_use':
      name=b.get('name');tool_counts[name]+=1;info['tools'].append({'line':i,'name':name,'input':b.get('input')})
      if name=='Read':info['reads'].append({'line':i,**b['input']})
      if name in ['Agent','Task']:info['delegations'].append({'line':i,**b.get('input',{})})
     if b.get('type')=='tool_result' and b.get('is_error'):errors.append({'location':loc,'tool_use_id':b.get('tool_use_id'),'content':b.get('content')})
   # Store original parsed content and system records without repeated provenance fields.
   records.append({'location':loc,'type':typ,'model':msg.get('model'),'content':content if msg else r})
  (agents if '/subagents/' in '/'+ref else main).append(info)
 summaries={'task':task,'snapshot':str(s),'actual_models':dict(models),'efforts':sorted(efforts),'unique_api_messages':len(requests),'usage_dedup_sum':{k:sum((v.get(k) or 0) for v in requests.values()) for k in ['input_tokens','output_tokens','cache_read_input_tokens','cache_creation_input_tokens']},'reported_thinking_tokens':sum((v.get('output_tokens_details') or {}).get('thinking_tokens',0) for v in requests.values()),'thinking_enabled':None,'tools':dict(tool_counts),'main':main,'subagents':agents,'tool_errors':errors,'raw_jsonl_review_status':'PENDING_MANUAL_REVIEW','input_integrity':not col['input_changed'],'shared_integrity':not col['shared_changed']}
 (run/'raw-audit-index.json').write_text(json.dumps(summaries,ensure_ascii=False,indent=2)+'\n')
 (run/'private/raw-readback.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in records))
 print(json.dumps({k:summaries[k] for k in ['task','actual_models','unique_api_messages','usage_dedup_sum','reported_thinking_tokens','tools']}|{'main_jsonl':len(main),'child_jsonl':len(agents),'tool_errors':len(errors)},ensure_ascii=False,indent=2))
if __name__=='__main__':audit(sys.argv[1])
