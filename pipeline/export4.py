import pandas as pd, numpy as np, json, re
f=pd.read_pickle('fourth_eval.pkl')
TH=0.015
clear=f[f.margin>=TH].copy()
summ={'n':int(len(f)),'clear':int(len(clear)),'match':round(float((clear.ch==clear.best).mean()),3)}
for b in ['go','punt','kick']:
    c=clear[clear.best==b]; summ['best_'+b]={'n':int(len(c)),'coach_same':round(float((c.ch==b).mean()),3)}
# by distance: how often model says go vs coaches went (clear + all)
summ['by_dist']={}
for d in ['1','2-3','4-6','7+']:
    s=f[f.db==d]; summ['by_dist'][d]={'n':int(len(s)),'model_go':round(float((s.best=='go').mean()),3),'coach_go':round(float((s.ch=='go').mean()),3)}
print(json.dumps(summ,indent=1))
rng=np.random.default_rng(11); parts=[]
for b in ['go','punt','kick']:
    c=clear[clear.best==b]
    w=np.where(c.ch==c.best,1.0,2.5); w=w/w.sum()
    parts.append(c.iloc[rng.choice(len(c),size=min(500,len(c)),replace=False,p=w)])
deal=pd.concat(parts).sample(frac=1,random_state=5)
def ptype(r):
    if r.ch!='go': return None
    if r.play_type=='run' and r.qb_scramble==1: return 'scramble'
    if r.play_type=='run': return 'run'
    if r.sack==1: return 'sack'
    if r.interception==1: return 'int'
    if r.complete_pass==1: return 'complete'
    return 'inc'
out=[]
for r in deal.itertuples():
    pa=str(r.is_play_action).lower()=='true'
    c = None if r.ch!='go' else ('run' if (r.play_type=='run' and r.qb_scramble!=1) else ('pa' if pa else 'pass'))
    succ = int((r.first_down==1) or (r.td_team==r.posteam)) if r.ch=='go' else (int(r.field_goal_result=='made') if r.ch=='kick' else None)
    out.append({'o':r.posteam,'d':r.defteam,'s':int(r.season),'st':r.season_type,'wk':int(r.week),'q':int(r.qtr),'t':str(r.time),
      'dn':4,'ds':int(r.ydstogo),'yl':int(r.yardline_100),'os':int(r.posteam_score),'dsc':int(r.defteam_score),
      'wp':round(float(r.wp),3),'g':round(float(r.wp_go),3),'p':None if r.wp_punt!=r.wp_punt else round(float(r.wp_punt),3),
      'k':None if r.wp_kick!=r.wp_kick else round(float(r.wp_kick),3),'pc':round(float(r.pconv),3),'pm':None if r.pmake!=r.pmake else round(float(r.pmake),3),
      'best':r.best,'ch':r.ch,'ok':succ,'c':c,'pt':ptype(r),'y':int(r.yards_gained) if r.yards_gained==r.yards_gained else 0,
      'ay':None if r.air_yards!=r.air_yards else int(r.air_yards),'pl':r.pass_location if isinstance(r.pass_location,str) else None,
      'rl':r.run_location if isinstance(r.run_location,str) else None,'sn':str(r.is_qb_sneak).lower()=='true',
      'kd':None if r.kick_distance!=r.kick_distance else int(r.kick_distance),
      'fm':'gun','wr':3,'te':1,'rb':1,'bx':7,'db':5,'dl':4,'desc':re.sub(r'\s+',' ',str(r.desc)).strip()})
json.dump({'summary':summ,'plays':out,'threshold':TH},open('fourth_data.json','w'),separators=(',',':'))
print(len(out),'4th-down snaps', pd.Series([p['best'] for p in out]).value_counts().to_dict(), 'coach matched:', round(np.mean([p['best']==p['ch'] for p in out]),2))
