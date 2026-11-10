import pandas as pd, numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
a=pd.read_pickle('allplays.pkl')
# ---- 1. win-probability model: learn nflverse wp from game state ----
FE=['score_differential','game_seconds_remaining','half_seconds_remaining','yardline_100','down','ydstogo','qtr']
w=a.dropna(subset=FE+['wp']); w=w[w.qtr<=4]
m=HistGradientBoostingRegressor(max_iter=300,learning_rate=.08,max_leaf_nodes=63,random_state=0)
idx=np.random.default_rng(0).random(len(w))<.85
m.fit(w.loc[idx,FE],w.loc[idx,'wp'])
from sklearn.metrics import mean_absolute_error
print('wp model MAE on held-out plays', round(mean_absolute_error(w.loc[~idx,'wp'],m.predict(w.loc[~idx,FE])),4))
def WP(sd,gs,hs,yl,dn,dist,qtr):
    X=pd.DataFrame({'score_differential':sd,'game_seconds_remaining':gs,'half_seconds_remaining':hs,'yardline_100':yl,'down':dn,'ydstogo':dist,'qtr':qtr})
    return np.clip(m.predict(X[FE]),0.001,0.999)
# ---- 2. component rates from data ----
fg=a[a.play_type=='field_goal'].dropna(subset=['kick_distance'])
fgb=fg.assign(make=(fg.field_goal_result=='made').astype(int)).groupby(fg.kick_distance.clip(18,66)).make.agg(['sum','size'])
fgb=fgb.reindex(range(18,67),fill_value=0)
# smooth with logistic fit
from sklearn.linear_model import LogisticRegression
lr=LogisticRegression().fit(fg[['kick_distance']],(fg.field_goal_result=='made').astype(int))
pmake=lambda d: lr.predict_proba(pd.DataFrame({'kick_distance':d}))[:,1]
print('FG make: 33yd',pmake([33])[0].round(3),' 45',pmake([45])[0].round(3),' 55',pmake([55])[0].round(3))
pu=a[(a.play_type=='punt')&(a.punt_blocked.fillna(0)==0)].copy()
pu['net']=pu.kick_distance.fillna(40)-pu.return_yards.fillna(0)
pu['ylb']=(pu.yardline_100//5)*5
netb=pu.groupby('ylb').net.median()
s=a[(a.down.isin([3,4]))&(a.play_type.isin(['run','pass']))&(a.penalty.fillna(0)==0)].copy()
s['succ']=((s.first_down==1)|(s.td_team==s.posteam)).astype(int)
s['g']=s.yardline_100<=s.ydstogo
conv=s.groupby([s.ydstogo.clip(1,15),'g']).succ.mean()
gain_succ=s[s.succ==1].groupby(s.ydstogo.clip(1,15)).yards_gained.mean()
def pconv(d,g):
    d=int(min(max(d,1),15)); return conv.get((d,g), conv.get((d,False)))
print('4th conv 1:',round(pconv(1,False),3),' 3:',round(pconv(3,False),3),' 1 goal:',round(pconv(1,True),3))
# ---- 3. evaluate each real 4th down ----
f=a[(a.down==4)&(a.play_type.isin(['run','pass','punt','field_goal']))&(a.penalty.fillna(0)==0)&(a.wp.between(0.05,0.95))&(a.qb_kneel.fillna(0)==0)&(a.qb_spike.fillna(0)==0)&a.wpa.notna()].copy()
f['ch']=np.where(f.play_type=='punt','punt',np.where(f.play_type=='field_goal','kick','go'))
f['db']=pd.cut(f.ydstogo,[0,1,3,6,99],labels=['1','2-3','4-6','7+']).astype(str)
f['fb']=pd.cut(f.yardline_100,[0,9,29,39,59,100],labels=['inside 10','10-29','30-39','40-59','own side']).astype(str)
f=f.dropna(subset=['score_differential','game_seconds_remaining','half_seconds_remaining'])
f=f[f.qtr<=4]
sd=f.score_differential.values; gs=f.game_seconds_remaining.values; hs=f.half_seconds_remaining.values
yl=f.yardline_100.values.astype(float); dist=f.ydstogo.values.astype(float); qtr=f.qtr.values
t=np.maximum(gs-6,0); th=np.maximum(hs-6,0)
opp=lambda sd2,yl2: 1-WP(-sd2,t,th,yl2,np.ones_like(yl2),np.full_like(yl2,10.0),qtr)
# go
goal=yl<=dist
pc=np.array([pconv(d,g) for d,g in zip(dist,goal)])
gain=np.array([max(dd, gain_succ.get(int(min(max(dd,1),15)),dd)) for dd in dist])
newyl=yl-gain; td=goal|(newyl<=0)
wp_succ=np.where(td, opp(sd+7, np.full_like(yl,70.0)), WP(sd,t,th,np.clip(newyl,1,99),np.ones_like(yl),np.minimum(10,np.clip(newyl,1,99)),qtr))
wp_fail=opp(sd, np.clip(100-yl,1,99))
wp_go=pc*wp_succ+(1-pc)*wp_fail
# field goal
kd=yl+17; pm=pmake(kd); pm=np.where(kd>66,0.0,pm)
wp_make=opp(sd+3,np.full_like(yl,70.0))
wp_miss=opp(sd,np.clip(np.where(yl+7<=20,80,100-(yl+7)),1,99))
wp_kick=pm*wp_make+(1-pm)*wp_miss
# punt
net=np.array([netb.get(int(x//5*5),40) for x in yl])
land=yl-net
oppyl=np.where(land<=0,80,100-land)
wp_punt=np.where(yl<35, np.nan, opp(sd,np.clip(oppyl,1,99)))  # nobody punts inside the 35
f['wp_go']=wp_go; f['wp_kick']=np.where(kd>66,np.nan,wp_kick); f['wp_punt']=wp_punt; f['pconv']=pc; f['pmake']=np.where(kd>66,np.nan,pm)
opts=f[['wp_go','wp_punt','wp_kick']].values
best=np.nanargmax(opts,axis=1); f['best']=np.array(['go','punt','kick'])[best]
srt=np.sort(np.nan_to_num(opts,nan=-1),axis=1); f['margin']=srt[:,-1]-srt[:,-2]
f['coach_ok']=(f.ch==f.best)|(f.margin<0.01)
f.to_pickle('fourth_eval.pkl')
print('snaps',len(f)); print(pd.crosstab(f.best,f.ch,margins=True))
clear=f[f.margin>=0.01]
print('clear decisions',len(clear),' coaches matched model',round((clear.ch==clear.best).mean(),3))
g=clear[clear.best=='go']; print('when model says go (clear):',len(g),'coaches went',round((g.ch=='go').mean(),3))
