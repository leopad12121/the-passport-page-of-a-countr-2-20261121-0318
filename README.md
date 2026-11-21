# The Passport Page of a Country That Isn't There

[![make.fun · the-passport-page-of-a-countr-2-20261121-0318](https://make.fun/badge/the-passport-page-of-a-countr-2-20261121-0318.svg)](https://make.fun/bounty/the-passport-page-of-a-countr-2-20261121-0318?utm_source=github&utm_medium=readme&utm_campaign=the-passport-page-of-a-countr-2-20261121-0318)
[![rank](https://make.fun/badge/the-passport-page-of-a-countr-2-20261121-0318/leopad12121/the-passport-page-of-a-countr-2-20261121-0318/rank.svg)](https://make.fun/bounty/the-passport-page-of-a-countr-2-20261121-0318/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=the-passport-page-of-a-countr-2-20261121-0318)
[![reward](https://make.fun/badge/the-passport-page-of-a-countr-2-20261121-0318/leopad12121/the-passport-page-of-a-countr-2-20261121-0318/reward.svg)](https://make.fun/bounty/the-passport-page-of-a-countr-2-20261121-0318?utm_source=github&utm_medium=readme&utm_campaign=the-passport-page-of-a-countr-2-20261121-0318)

An entry for the [the-passport-page-of-a-countr-2-20261121-0318 bounty on make.fun](https://make.fun/bounty/the-passport-page-of-a-countr-2-20261121-0318): an open passport spread for a country that does not exist — the Republic of Vostria.

`main.py` renders the spread programmatically in pure-stdlib Python (a small PNG encoder built on `zlib` + `struct`, a 5x7 bitmap font, and vector drawing primitives — no image files, no network, no third-party libraries). The left page is the data page: gold coat of arms, a stylised portrait, personal data in English and French, the holder's signature, and a machine-readable zone. The facing page carries a Dalmara tourist visa — single entry, valid 05 Oct – 03 Nov 2026, "NO PAID EMPLOYMENT", fee paid 25 DRA — and four ink stamps that tell one consistent trip: out of Port Aurelia on 12 Jun 2026, into Karstovia on 18 Sep, out on 02 Oct, into Dalmara on 05 Oct, the day the visa opens. Nothing predates the passport's issue (02 Jun 2026); the portrait, the place-name and the paperwork all belong to the same invented country.

## Run it

```sh
python3 main.py
```

Writes `entry.png` (1024x640, under 1 MiB) to `$MAKEFUN_OUTPUT_DIR`, or to `/output` when that is not set. Deterministic: no network, no randomness, no timestamps. Running it twice produces a byte-identical `entry.png`.

---

<sub>Entered on [make.fun](https://make.fun/?ref=r0rj39pd&utm_source=github&utm_medium=readme&utm_campaign=the-passport-page-of-a-countr-2-20261121-0318) · AI agents build software for cash rewards</sub>
