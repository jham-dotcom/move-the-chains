import pandas as pd, numpy as np, re, sys, json
D = sys.argv[1]
cols = ['game_id','play_id','season','season_type','week','posteam','defteam','home_team','away_team','posteam_score','defteam_score',
 'qtr','game_seconds_remaining','time','down','ydstogo','yardline_100','goal_to_go','play_type','qb_dropback','qb_scramble','rush',
 'run_location','run_gap','pass_location','air_yards','yards_gained','first_down','td_team','penalty','desc','wp','epa','sack',
 'interception','complete_pass','incomplete_pass','qb_kneel','qb_spike','two_point_attempt','aborted_play','fumble_lost','shotgun',
 'wpa','kick_distance','field_goal_result','punt_blocked','score_differential','half_seconds_remaining','return_yards','punt_fake' if False else 'play_type_nfl']
frames=[]
import os
YEARS=[y for y in range(2022,2031) if os.path.exists(f'{D}/pbp_{y}.csv.gz')]
for y in YEARS:
    p = pd.read_csv(f'{D}/pbp_{y}.csv.gz', usecols=cols, low_memory=False)
    pcols=['nflverse_game_id','play_id','defenders_in_box','defense_personnel','offense_formation','offense_personnel','defense_coverage_type','defense_man_zone_type','number_of_pass_rushers']
    part = pd.read_csv(f'{D}/part_{y}.csv', low_memory=False, usecols=pcols) if os.path.exists(f'{D}/part_{y}.csv') else pd.DataFrame(columns=pcols)
    _unused = dict(usecols=['nflverse_game_id','play_id','defenders_in_box','defense_personnel','offense_formation','offense_personnel','defense_coverage_type','defense_man_zone_type','number_of_pass_rushers'])
    ftn = pd.read_csv(f'{D}/ftn_{y}.csv', low_memory=False, usecols=['nflverse_game_id','nflverse_play_id','n_defense_box','is_play_action','is_screen_pass','is_rpo','is_qb_sneak','n_blitzers','n_pass_rushers'])
    p = p.merge(part, left_on=['game_id','play_id'], right_on=['nflverse_game_id','play_id'], how='left')
    p = p.merge(ftn, left_on=['game_id','play_id'], right_on=['nflverse_game_id','nflverse_play_id'], how='left', suffixes=('','_ftn'))
    frames.append(p)
df = pd.concat(frames, ignore_index=True)
df.to_pickle('allplays.pkl')
print('seasons',YEARS)
print('all plays', len(df))
q = df[(df.down.isin([3,4])) & (df.play_type.isin(['run','pass'])) & (df.penalty.fillna(0)==0)
       & (df.qb_kneel.fillna(0)==0) & (df.qb_spike.fillna(0)==0) & (df.two_point_attempt.fillna(0)==0) & (df.aborted_play.fillna(0)==0)
       & (df.wp.between(0.05,0.95))].copy()
# box: prefer NGS participation, fall back to FTN charting
box = q.defenders_in_box.where(q.defenders_in_box>0, np.nan)
box = box.fillna(q.n_defense_box.where(q.n_defense_box>0, np.nan))
q['box'] = box
q = q[q.box.between(3,11)]
# call
q['is_pa'] = q.is_play_action.astype(str).str.lower().eq('true')
designed_run = (q.play_type=='run') & (q.qb_scramble.fillna(0)==0)
q['call'] = np.where(designed_run, 'run', np.where(q.is_pa, 'pa', 'pass'))
q = q[q.is_play_action.notna()]  # need FTN charting to know play-action
q['success'] = ((q.first_down==1) | (q.td_team==q.posteam)).astype(int)
# personnel -> DB count
def dbs(s):
    if not isinstance(s,str): return np.nan
    n=0
    for num,pos in re.findall(r'(\d+)\s+([A-Z]+)', s):
        if pos in ('CB','FS','SS','DB','S'): n+=int(num)
    return n
q['n_db'] = q.defense_personnel.map(dbs)
def dist_b(d):
    return '1' if d<=1 else '2' if d<=2 else '3-4' if d<=4 else '5-7' if d<=7 else '8-10' if d<=10 else '11+'
q['dist_b'] = q.ydstogo.map(dist_b)
q['box_b'] = q.box.map(lambda b: '5 or fewer' if b<=5 else '6' if b==6 else '7' if b==7 else '8+')
gl=(q.yardline_100<=q.ydstogo)&(q.ydstogo<=4)
q.loc[gl,'dist_b']=q.loc[gl,'dist_b']+' goal'
q.loc[gl,'box_b']='any'
q['zone'] = np.where(q.yardline_100<=10,'goal', np.where(q.yardline_100<=20,'red','field'))
print('graded snaps', len(q)); print(q.call.value_counts()); print(q.groupby('call').success.mean().round(3))
q.to_pickle('snaps.pkl')
