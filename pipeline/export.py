import pandas as pd, numpy as np, json, re
q=pd.read_pickle('snaps.pkl')
K=30
order=['1','2','3-4','5-7','8-10','11+','1 goal','2 goal','3-4 goal']; boxes=['5 or fewer','6','7','8+','any']; calls=['run','pass','pa']
prior=q.groupby(['dist_b','call']).success.mean()
rates={}
for d in order:
    for b in boxes:
        if (b=='any')!=d.endswith('goal'): continue
        cell={}
        for c in calls:
            s=q[(q.dist_b==d)&(q.box_b==b)&(q.call==c)].success
            n=len(s)
            if c=='pa':   # play-action is a pass: shrink hard toward this look's straight-pass rate
                ps=q[(q.dist_b==d)&(q.box_b==b)&(q.call=='pass')].success
                p0=ps.mean() if len(ps)>=20 else prior[(d,'pass')]; k=80
            else:
                p0=prior.get((d,c),q[q.call==c].success.mean()); k=K
            cell[c]={'p':round((s.sum()+k*p0)/(n+k),3),'n':int(n),'raw':round(s.mean(),3) if n else None}
        big=[c for c in calls if cell[c]['n']>=20] or calls
        best=max(big,key=lambda c:cell[c]['p'])
        cell['best']=best
        cell['ok']=[c for c in calls if cell[best]['p']-cell[c]['p']<=0.03]
        cell['share']={c:round(cell[c]['n']/max(1,sum(cell[x]['n'] for x in calls)),3) for c in calls}
        rates[d+'|'+b]=cell
# how often teams made the model's best call
q['key']=q.dist_b+'|'+q.box_b
q['ok']=[c in rates[k]['ok'] for c,k in zip(q.call,q.key)]
summary={d:{'n':int((q.dist_b==d).sum()),'pass_share':round((q[q.dist_b==d].call!='run').mean(),3),
            'ok_share':round(q[q.dist_b==d].ok.mean(),3),
            'run':round(q[(q.dist_b==d)&(q.call=='run')].success.mean(),3),
            'pass':round(q[(q.dist_b==d)&(q.call=='pass')].success.mean(),3),
            'pa':round(q[(q.dist_b==d)&(q.call=='pa')].success.mean(),3)} for d in order}
print(json.dumps(summary,indent=0))
# deal: up to 150 snaps per offense, 25 per distance bucket, 50/50 converted/stopped
rng=np.random.default_rng(7)
def cnt(s,pos):
    if not isinstance(s,str): return 0
    return sum(int(n) for n,p in re.findall(r'(\d+)\s+([A-Z]+)',s) if p in pos)
deal=[]
for team,tq in q.groupby('posteam'):
    picked=[]
    for d in order:
        sub=tq[tq.dist_b==d]
        for sval in [0,1]:
            g=sub[sub.success==sval]
            if not len(g): continue
            w=np.where(g.ok,1.0,2.0); w=w/w.sum()
            idx=rng.choice(len(g),size=min(13 if sval==0 else 12,len(g)),replace=False,p=w)
            picked.append(g.iloc[idx])
    tp=pd.concat(picked)
    if len(tp)<150:
        rest=tq.drop(tp.index); tp=pd.concat([tp,rest.sample(min(150-len(tp),len(rest)),random_state=1)])
    deal.append(tp.sample(frac=1,random_state=2).head(150))
deal=pd.concat(deal).sample(frac=1,random_state=3)
def ptype(r):
    if r.call=='run': return 'run'
    if r.play_type=='run' and r.qb_scramble==1: return 'scramble'
    if r.sack==1: return 'sack'
    if r.interception==1: return 'int'
    if r.complete_pass==1: return 'complete'
    return 'inc'
def form(f):
    f=str(f).upper()
    return 'gun' if 'SHOTGUN' in f or 'EMPTY' in f else 'pistol' if 'PISTOL' in f else 'uc' if f not in ('NAN','') else 'gun'
out=[]
for r in deal.itertuples():
    op=str(r.offense_personnel)
    wr=cnt(op,('WR',)); te=cnt(op,('TE',)); rb=cnt(op,('RB','FB'))
    if wr+te+rb!=5: wr,te,rb=3,1,1
    dl=cnt(r.defense_personnel,('DL','DE','DT','NT'))
    if not dl: dl=4
    cov=None if not isinstance(r.defense_coverage_type,str) else r.defense_coverage_type.replace('_',' ').title().replace('2 Man','2-Man')
    out.append({'s':int(r.season),'st':r.season_type,'wk':int(r.week),'o':r.posteam,'d':r.defteam,
      'q':int(r.qtr),'t':str(r.time),'dn':int(r.down),'ds':int(r.ydstogo),'yl':int(r.yardline_100),
      'os':int(r.posteam_score),'dsc':int(r.defteam_score),'bx':int(r.box),'db':int(r.n_db) if r.n_db==r.n_db else 5,'dl':int(dl),
      'fm':form(r.offense_formation),'wr':wr,'te':te,'rb':rb,'c':r.call,'ok':int(r.success),'y':int(r.yards_gained),
      'ay':None if r.air_yards!=r.air_yards else int(r.air_yards),'pl':r.pass_location if isinstance(r.pass_location,str) else None,
      'rl':r.run_location if isinstance(r.run_location,str) else None,'pt':ptype(r),'sn':bool(r.is_qb_sneak==True or str(r.is_qb_sneak).lower()=='true'),
      'cv':cov,'mz':None if not isinstance(r.defense_man_zone_type,str) else ('Man' if 'MAN' in r.defense_man_zone_type else 'Zone'),
      'pr':None if not (r.number_of_pass_rushers==r.number_of_pass_rushers) or r.number_of_pass_rushers==0 else int(r.number_of_pass_rushers),
      'k':r.key,'desc':re.sub(r'\s+',' ',str(r.desc)).strip()})
data={'seasons':'2022–2026','team_totals':{k:int(v) for k,v in q.groupby('posteam').size().items()},'rates':rates,'summary':summary,'plays':out,'n_total':int(len(q))}
json.dump(data,open('game_data.json','w'),separators=(',',':'))
print(len(out),'plays exported', round(len(json.dumps(data))/1024),'KB')
print(pd.Series([p['c'] for p in out]).value_counts().to_dict(), 'best calls:', pd.Series([rates[p['k']]['best'] for p in out]).value_counts().to_dict())
for k in ['1|8+','2|6','2|8+','3-4|5 or fewer','5-7|6']: print(k, rates[k])
