# Move the Chains

A play-calling game built on real NFL 3rd and 4th downs. You see the down, distance, score and the defensive look the offense saw before the snap, make the call, then see what really happened and how often that call actually works.

- **Daily 10**: the same ten snaps for everyone each day, with a film-room recap and a shareable score.
- **Free play**: real snaps, filterable by team.
- **4th down**: go for it, punt or kick, graded by win probability.

## Put it online (free, about 5 minutes)

1. Create a new public repository on GitHub, for example `move-the-chains`.
2. Upload everything in this folder (keep the folder structure, including `.github`).
3. In the repo, go to **Settings → Pages**, set **Source** to "Deploy from a branch", choose `main` and `/ (root)`, and save.
4. Your game will be live at `https://<your-username>.github.io/move-the-chains/` within a minute or two.

## Weekly updates

`.github/workflows/refresh.yml` runs every Tuesday morning. It downloads the latest nflverse data, re-grades every snap and commits a new `index.html`, so last weekend's games show up automatically. To run it right away, open the **Actions** tab, pick "Weekly data refresh" and click **Run workflow**.

Each player's Daily 10 is locked in when they start it, so a refresh never swaps snaps out from under someone mid-game.

## How the grading works

- **3rd and 4th downs (Run, Pass, Play-action):** every graded snap from 2022 on is grouped by distance and defenders in the box, with goal-to-go snaps grouped separately. The right call is the one that converted most often in that look. Small samples are pulled toward the average, play-action is compared against regular passes, and calls within 3 points of the best also count. Looks where all three calls are within 3 points are toss-ups and don't count.
- **4th-down decisions:** each choice is scored by the offense's chance to win afterward, using a win-probability model trained on nflverse play-by-play, real conversion rates by distance, real field-goal make rates by distance and average net punts by field position. Only decisions where one choice is at least 1.5 points better are graded.
- These are observational numbers. Teams pick calls for reasons the data can't see.

## Rebuild by hand

```
pip install -r pipeline/requirements.txt
bash pipeline/run_all.sh
```

## Data

Play-by-play, participation and FTN charting from [nflverse](https://github.com/nflverse/nflverse-data). Defensive alignments on the field are drawn from each snap's real box count and personnel, not tracked player positions.
