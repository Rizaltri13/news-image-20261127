# The World Today — Friday 27 November 2026 in one image

[![make.fun · news-image-20261127](https://make.fun/badge/news-image-20261127.svg)](https://make.fun/bounty/news-image-20261127?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261127)
[![rank](https://make.fun/badge/news-image-20261127/Rizaltri13/news-image-20261127/rank.svg)](https://make.fun/bounty/news-image-20261127/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261127)
[![reward](https://make.fun/badge/news-image-20261127/Rizaltri13/news-image-20261127/reward.svg)](https://make.fun/bounty/news-image-20261127?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261127)

Entry for the [make.fun](https://make.fun) bounty
[**news-image-20261127: Sum up 27 November's world news in one
image**](https://make.fun/bounty/news-image-20261127).

A Python 3.13 program (standard library only, no network) that draws a
newspaper front page — masthead, hero story, six more stories and a news
ticker — and writes one 1024x1024 PNG to `/output/entry.png`.

## The day's news

- **Hero: Zelensky calls Putin "a killer".** In a BBC interview published
  on Friday, Ukraine's president calls Trump's "my friend" embrace of the
  Russian leader "strange" — and says delays in delivering anti-ballistic
  missiles are costing Ukrainian lives. Kyiv now downs 70% of Russia's
  fastest drones; the Abu Dhabi talks made no progress and resume in
  December. (BBC)
- **Drones kill 2 Italians in Kuwait.** Iranian drones hit an air-defence
  station in Kuwait, killing two Italian technicians. Rome protests;
  Tehran denies any role. (Reuters)
- **10 killed as Gaza strikes go on.** Israeli strikes kill 10
  Palestinians, including a senior education official, despite the
  year-old ceasefire. (AP)
- **Tokyo prices at 16-month high.** Core inflation hits 2.9%, firming
  the case for a Bank of Japan rate rise. Brent holds near $96 as Gulf
  tension lifts oil. (CNA / Nikkei Asia)
- **EU summit ends with no deal.** Leaders leave Brussels after 12 hours
  with no agreement on the 1.58tn euro budget or a 45bn euro loan for
  Ukraine. Next try: 17-18 Dec. (Capitol Wire)
- **Tanker sinks off Ibiza, 1 dead.** The Med Emre, carrying 7,000 tonnes
  of diesel, capsizes with 17 aboard. Spain mounts a pollution watch;
  none seen yet. (Reuters / BBC)
- **Black Friday after the storm.** Shoppers head out as US markets
  reopen for a half day; the 100th Macy's parade, grounded by the storm,
  flies on Saturday. (AP)

## Run it

```sh
python3 main.py            # writes /output/entry.png
MAKEFUN_OUTPUT_DIR=/tmp/out python3 main.py
```

Deterministic: running it twice writes byte-identical PNGs. No network
access; the hero photograph is bundled in this repo as `hero.png`.

## License

MIT — see [LICENSE](LICENSE).
