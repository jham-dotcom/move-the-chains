"""Download nflverse play-by-play, participation and FTN charting for 2022 through the current season."""
import sys, os, datetime, urllib.request, urllib.error
out = sys.argv[1] if len(sys.argv) > 1 else "data"
os.makedirs(out, exist_ok=True)
today = datetime.date.today()
season = today.year if today.month >= 9 else today.year - 1
B = "https://github.com/nflverse/nflverse-data/releases/download"
files = {"pbp_{y}.csv.gz": "pbp/play_by_play_{y}.csv.gz",
         "part_{y}.csv": "pbp_participation/pbp_participation_{y}.csv",
         "ftn_{y}.csv": "ftn_charting/ftn_charting_{y}.csv"}
for y in range(2022, season + 1):
    for local, remote in files.items():
        dest = os.path.join(out, local.format(y=y))
        try:
            urllib.request.urlretrieve(f"{B}/{remote.format(y=y)}", dest)
            print("got", dest)
        except urllib.error.HTTPError as e:
            print("missing", remote.format(y=y), e.code)  # participation can lag a season; build.py handles it
