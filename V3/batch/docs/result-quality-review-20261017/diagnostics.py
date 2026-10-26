"""Read-only post-seal diagnostic review. No judge, model call, or run mutation.
Uses only frozen public inputs and final output. Writes audit results beside this script.
Different audit runtime is disclosed; this is not a new benchmark/model run.
"""
from pathlib import Path
import json, math, sys, hashlib, datetime
import numpy as np
import pandas as pd
D=Path(__file__).resolve().parent;B=D.parent.parent
P={r.name:Path(json.loads((r/'sealed.json').read_text())['snapshot'])/'project' for r in (B/'runs').iterdir() if (r/'sealed.json').exists()}
R={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scoring_performed':False,'runtime':{'python':sys.version,'numpy':np.__version__,'pandas':pd.__version__},'scope':'post-seal reviewer calculations, not changes to subject or a new agent experiment'}
def ls(x,y):
 X=np.column_stack([np.ones(len(x)),x]);b=np.linalg.lstsq(X,y,rcond=None)[0];res=y-X@b;return b,float(res@res)
def spline(x,y,z):
 # Not-a-knot cubic interpolation using second derivatives; checked on a cubic polynomial and source knots.
 n=len(x);h=np.diff(x);A=np.zeros((n,n));rhs=np.zeros((n,y.shape[1]));A[0,:3]=[-h[1],h[0]+h[1],-h[0]];A[-1,-3:]=[-h[-1],h[-2]+h[-1],-h[-2]]
 for i in range(1,n-1):A[i,i-1:i+2]=[h[i-1],2*(h[i-1]+h[i]),h[i]];rhs[i]=6*((y[i+1]-y[i])/h[i]-(y[i]-y[i-1])/h[i-1])
 M=np.linalg.solve(A,rhs);i=np.clip(np.searchsorted(x,z)-1,0,n-2);w=h[i,None];u=(x[i+1,None]-z[:,None]);v=z[:,None]-x[i,None]
 return (M[i]*u**3+M[i+1]*v**3)/(6*w)+(y[i]-M[i]*w*w/6)*u/w+(y[i+1]-M[i+1]*w*w/6)*v/w
xt=np.array([0.,.3,1.,1.4,2.]);yt=(xt**3-2*xt+1)[:,None];zt=np.linspace(0,2,57);assert np.max(np.abs(spline(xt,yt,zt).ravel()-(zt**3-2*zt+1)))<1e-12
# Chemistry: reproduce exactly the phase statistic, then examine definition/reference sensitivity.
p=P['Chemistry_02_photoionization_delay'];df=pd.read_csv(p/'data/angle_energy_observations_datasets.tsv',sep='\t')
def arr(name):return df[df.dataset_path==name].pivot(index='index_0',columns='index_1',values='value').sort_index().sort_index(axis=1).to_numpy(float)
def energy(name):return df[df.dataset_path==name].sort_values('index_0').value.to_numpy(float)
x=energy('experiment/photon_energy_eV');z=energy('theory/photon_energy_eV');a=arr('experiment/phase');b=arr('theory/phase');ai=spline(x,a,z);delta=ai-b;circ=np.angle(np.exp(1j*delta));observed=json.loads((p/'output/aligned_exp_theory_comparison.json').read_text())['aligned_comparison']['phase_diff_angle_avg_mean']
chem={'spline_source_knot_error':float(np.max(abs(spline(x,a,x)-a))),'recomputed_mean_absolute_cell_phase_difference_rad':float(abs(delta).mean()),'saved_mean_rad':observed,'error_vs_saved':float(abs(abs(delta).mean()-observed)),'absolute_difference_of_angle_means_rad':float(abs(ai.mean(1)-b.mean(1)).mean()),'circular_distance_mean_rad':float(abs(circ).mean()),'mean_abs_difference_after_global_2pi_shift_rad':float(abs(delta+2*np.pi).mean()),'fraction_cell_phase_differences_above_pi':float(np.mean(abs(delta)>np.pi)),'slope_raw_rad_per_eV':float(ls(z,abs(delta).mean(1))[0][1]),'slope_circular_rad_per_eV':float(ls(z,abs(circ).mean(1))[0][1]),'interpretation':'Circular distance is a reference-sensitivity diagnostic, not a replacement scientific estimate. A physical phase-reference convention must be established before interpreting absolute unwrapped offsets.'}
assert chem['error_vs_saved']<1e-10
ac=pd.read_csv(p/'data/angular_coefficients_datasets.tsv',sep='\t');v=ac[(ac.index_0==0)&(ac.index_1==3)].copy();v['E']=v.dataset_path.str.extract(r'CoefLeg_(.*)eV')[0].astype(float);v=v.sort_values('E');chem['energy_constant_integer_branch_shift_mean_abs_rad']=float(abs(delta-2*np.pi*np.rint(np.median(delta,axis=0)/(2*np.pi))[None,:]).mean());chem['F20_order0_values']=v[['E','value']].to_dict('records');chem['F20_order0_global_min']=v.loc[v.value.idxmin(),['E','value']].to_dict();chem['max_cell_difference_to_circular_examples']=[{'angle':int(j),'raw_mean_abs':float(abs(delta[:,j]).mean()),'circular_mean_abs':float(abs(circ[:,j]).mean())} for j in [0,85,90,95,180]];R['chemistry']=chem
# Physics: inspect the effect of a search boundary on the reported equal timescales.
p=P['Physics_04_temporal_delay_transition'];base=p/'data/source_data/figures/fig3a_correlation_collapse/data';curves={f'B{i}':np.loadtxt(base/f'corr.ave_{i}.txt') for i in range(1,6)};saved=json.loads((p/'output/evidence/finding2_correlation_collapse.json').read_text())
def interp_extrap(x,xp,fp):
 y=np.interp(x,xp,fp);lo=x<xp[0];hi=x>xp[-1];y[lo]=fp[0]+(x[lo]-xp[0])*(fp[1]-fp[0])/(xp[1]-xp[0]);y[hi]=fp[-1]+(x[hi]-xp[-1])*(fp[-1]-fp[-2])/(xp[-1]-xp[-2]);return y
phys={}
for key in ['B1_vs_B4','B1_vs_B5']:
 k1,k2=key.split('_vs_');c1,c2=curves[k1],curves[k2]
 def metrics(s):
  xq=c1[:,0]*s;yy=interp_extrap(xq,c2[:,0],c2[:,1]);mask=(xq>=c2[0,0])&(xq<=c2[-1,0]);return {'scale':float(s),'correlation':float(np.corrcoef(c1[:,1],yy)[0,1]),'rmse':float(np.sqrt(np.mean((c1[:,1]-yy)**2))),'extrapolated_fraction':float(1-mask.mean()),'overlap_n':int(mask.sum()),'overlap_rmse':float(np.sqrt(np.mean((c1[mask,1]-yy[mask])**2)))}
 old=metrics(saved['collapse_pairwise'][key]['optimal_scale']);candidate=[metrics(s) for s in np.arange(.001,.1,.0001)];best=max(candidate,key=lambda x:x['correlation']);phys[key]={'reported_bound_solution':old,'expanded_search_below_0_1':best};assert abs(old['correlation']-saved['collapse_pairwise'][key]['max_correlation'])<1e-10
phys['meaning']='Same original objective, interpolation and data, only extend lower search bound. This tests whether the claimed saturation is a bound artifact; does not prove a universal law.';R['physics']=phys
# Astronomy: inspect sampling grid and what the LOO artifact actually evaluates.
p=P['Astronomy_02_gravity_spectral_structure'];df=pd.read_csv(p/'data/pass_residual_traces.tsv',sep='\t');bins=[]
for pid,g in df.groupby('pass_id'):
 t=np.sort(g.relative_time_min.to_numpy(float));dt=np.diff(t);bins.append({'pass':pid,'n':len(t),'duration_min':float(np.ptp(t)),'dt_min':float(np.mean(dt)),'dt_variation':float(np.ptp(dt)),'fft_bin_microhz':float(1e6/(len(t)*np.mean(dt)*60))})
loo=json.loads((p/'working/subagent_fft_loo/loo_results.json').read_text());R['astronomy']={'sampling':bins,'fft_spacing_range_microhz':[min(x['fft_bin_microhz'] for x in bins),max(x['fft_bin_microhz'] for x in bins)],'claimed_candidate_frequency_separation_microhz':50,'nonuniform_passes':[x['pass'] for x in bins if x['dt_variation']>1e-6],'duration_range_min':[min(x['duration_min'] for x in bins),max(x['duration_min'] for x in bins)],'loo_top_level_keys':list(loo),'inference':'Nyquist sufficiency is distinct from frequency discrimination; top-five peak occurrence is not a no-structure test. Read LOO source for claim-specific scope.'}
# Earth: controlled implementation diagnostic with identical data/filter/CR1 correction.
q,w=np.polynomial.legendre.leggauss(160)
def t_p(t,df):
 t=abs(float(t));xx=(q+1)*t/2;c=math.exp(math.lgamma((df+1)/2)-math.lgamma(df/2))/math.sqrt(df*math.pi);integral=t/2*np.dot(w,c*np.exp(-(df+1)/2*np.log1p(xx*xx/df)));return float(max(0,min(1,1-2*integral)))
assert abs(t_p(2.2281388519649385,10)-.05)<1e-10
p=P['EarthScience_01_glacial_fluvial_erosion'];er=[]
for label,name in [('Glacial','glacial_erosion_Earth.tsv'),('Fluvial','nonglacial_erosion_Earth.tsv')]:
 raw=pd.read_csv(p/'data/raw'/name,sep='\t');valid=raw[(raw['Erosion rate (mm/yr)']>0)&(raw['Time interval (yr)']>0)].copy()
 for col in ['Reference','Locality']:
  for singleton in [False,True]:
   d=valid.dropna(subset=[col]);counts=d[col].value_counts();d=d[d[col].isin(counts[counts>(0 if singleton else 1)].index)];x=np.log10(d['Time interval (yr)'].to_numpy(float));y=np.log10(d['Erosion rate (mm/yr)'].to_numpy(float));X=np.column_stack([np.ones(len(x)),x]);beta=np.linalg.lstsq(X,y,rcond=None)[0];res=y-X@beta;ids=pd.factorize(d[col])[0];g=len(set(ids));A=np.zeros((g,2));np.add.at(A,ids,X*res[:,None]);meat=A.T@A;assert np.allclose(meat,sum(np.outer(v,v) for v in A),rtol=1e-10,atol=1e-10);bad=np.full((2,2),np.sum(A*A));inv=np.linalg.inv(X.T@X);factor=(len(x)-1)/(len(x)-2)*g/(g-1);V=inv@meat@inv*factor;VB=inv@bad@inv*factor;se=float(np.sqrt(V[1,1]));seb=float(np.sqrt(VB[1,1]));seols=float(np.sqrt((res@res)/(len(x)-2)*inv[1,1]));er.append({'process':label,'cluster':col,'retain_singletons':singleton,'n':len(x),'clusters':g,'slope':float(beta[1]),'se_ols_same_sample':seols,'bad_se':seb,'bad_p':t_p(beta[1]/seb,g-1),'correct_cr1_se':se,'correct_cr1_p':t_p(beta[1]/se,g-1),'correct_se_over_ols_same_sample':se/seols})
R['earth']={'rows':er,'method':'Manual CR1 score outer-product, two equivalent matrix constructions; Student-t G-1 p via Gauss-Legendre integration; same original filter examined separately from retaining singleton clusters. No causal conclusion inferred.'}
# Neuro: design coverage / actual independent replication structure only.
p=P['Neuro_02_calcium_response_regions'];df=pd.read_csv(p/'data/cellular_calcium_response_summaries.tsv',sep='\t');r12=df[df.anatomical_region_id.isin(['region_1','region_2'])];R['neuro']={'cells':len(df),'unique_slice_labels':df.slice_id.nunique(),'batch_slice_pairs':len(df.groupby(['recording_batch_id','slice_id'])),'batch_slice_region_condition_groups':len(df.groupby(['recording_batch_id','slice_id','anatomical_region_id','condition'])),'slice_label_reuse':df.groupby('slice_id').agg(batches=('recording_batch_id','nunique'),ages=('animal_age_days','nunique')).reset_index().to_dict('records'),'slice_region_condition_groups':len(df.groupby(['slice_id','anatomical_region_id','condition'])),'region_condition_counts':df.groupby(['anatomical_region_id','condition']).size().rename('n').reset_index().to_dict('records'),'batch_design':df.groupby('recording_batch_id').agg(cells=('observation_id','size'),slices=('slice_id','nunique'),regions=('anatomical_region_id','nunique'),conditions=('condition','nunique'),min_age=('animal_age_days','min'),max_age=('animal_age_days','max')).reset_index().to_dict('records'),'r12_slices_by_condition':r12.groupby('condition').slice_id.nunique().to_dict(),'statement':'Primary headline tests in main_analysis.py use cell-level OLS/Welch without age, slice or batch in the model; leave-one-batch-out repeats these tests on retained cells, not a held-out predictive evaluation.'}
# Verify sealed manifests of all files we rely on remain intact.
checks=[]
for task,p in P.items():
 sealed=json.loads((B/'runs'/task/'sealed.json').read_text());snap=p.parent;bad=[]
 for rel,sha in sealed['manifest'].items():
  f=snap/rel
  if not f.exists() or hashlib.sha256(f.read_bytes()).hexdigest()!=sha:bad.append(rel)
 checks.append({'task':task,'manifest_entries':len(sealed['manifest']),'mismatches':bad})
R['seal_integrity']=checks
(D/'diagnostics.json').write_text(json.dumps(R,ensure_ascii=False,indent=2,default=lambda x:x.item() if hasattr(x,'item') else str(x))+'\n');print(json.dumps({k:v for k,v in R.items() if k not in ['neuro','astronomy']},ensure_ascii=False,indent=2));print('astronomy_fft_spacing',R['astronomy']['fft_spacing_range_microhz']);print('neuro_design',json.dumps(R['neuro'],ensure_ascii=False));
