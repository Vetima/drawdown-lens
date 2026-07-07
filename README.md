# drawdown-lens

**See the downside of any crypto asset before it hits you.**

A tiny, zero-dependency command-line tool that pulls public Binance price history
(no API key, no account, no sign-up) and answers the one question most people never
ask before they buy:

> How far down did this asset actually go — for how long — and how long did it take to recover?

Everyone stares at returns. Almost nobody looks at **drawdown**: the peak-to-trough
loss you have to *survive* to ever see those returns. `drawdown-lens` puts that number
on your screen in one command.

```
$ python3 drawdown_lens.py BTCUSDT --days 365

  drawdown-lens | BTCUSDT | 1d | 2025-07-07 -> 2026-07-06
  --------------------------------------------------------
  Worst drawdown ....... -52.97%   ################..............
    from peak .......... 2025-10-06  (124,658.54)
    to trough .......... 2026-06-30  (58,624.71)
    fall took .......... 267 days
  Longest underwater ... 273 days below a prior peak (ongoing)
  Time underwater ...... 353 of 365 days closed below a prior peak
  Right now ............ -48.81% below its high (this window)
  --------------------------------------------------------
  Returns are the story you're sold. Drawdown is the one you live through.
```

## Why drawdown?

A "+300% in a year" headline hides the fact that you might have had to sit through a
**-55% drawdown** to get there. Most people can't. They sell at the bottom, right
before the recovery — and that single behaviour, not the market, is what wrecks most
crypto portfolios.

Knowing an asset's real drawdown history changes how you size a position, how you set
expectations, and whether you can actually hold through a crash. It's the most honest
risk number there is, and it's the one nobody puts front and center.

So we open-sourced a way to see it in five seconds.

## Install

You need **Python 3.7+**. That's it. No `pip install`, no dependencies — the tool uses
only the Python standard library.

```bash
git clone https://github.com/Vetima/drawdown-lens.git
cd drawdown-lens
python3 drawdown_lens.py BTCUSDT
```

## Usage

```bash
# Last 365 days of BTC, daily candles (defaults)
python3 drawdown_lens.py BTCUSDT

# Two years of ETH
python3 drawdown_lens.py ETHUSDT --days 730

# 6 months of SOL on 4-hour candles
python3 drawdown_lens.py SOLUSDT --days 180 --interval 4h

# Everything Binance has for the pair (BTC: 2017+, includes 2018's -83%)
python3 drawdown_lens.py BTCUSDT --all

# Raw JSON, for piping into your own scripts
python3 drawdown_lens.py BTCUSDT --json
# (drawdown values in the JSON are positive magnitudes; the report adds the minus sign)
```

**Options**

| Flag | Default | Meaning |
|------|---------|---------|
| `symbol` | — | Any Binance pair, e.g. `BTCUSDT`, `ETHUSDT`, `SOLUSDT` |
| `--days` | `365` | Lookback window in days |
| `--all` | off | Ignore `--days` and use the pair's full listed history |
| `--interval` | `1d` | Candle size: `1h 2h 4h 6h 12h 1d 3d 1w` |
| `--json` | off | Print machine-readable JSON instead of the report |

**What it computes**

- **Worst drawdown** — the deepest peak-to-trough drop in the window, with the exact peak and trough dates.
- **Fall duration** — how many days the drop took.
- **Longest underwater** — the longest stretch the price stayed below a previous peak (i.e. how long holders waited to break even).
- **Time underwater** — how many of the window's candles closed below a prior peak (how much of the period holders spent losing, not just the single worst stretch).
- **Current drawdown** — how far below its window-high the asset sits right now.

All from public Binance data. Nothing is stored, nothing is sent anywhere.

## Who made this

`drawdown-lens` is built and maintained by **[Vetima](https://vetima.trade)**.

Vetima is a **non-custodial crypto trading software**: it works on *your* own exchange
account through an API key with **no withdrawal permission**, and its focus is
**drawdown protection** — cutting the depth of the falls this tool measures, instead of
chasing a magic monthly return. Your keys and your funds never leave your account.

We wrote this tool because it reflects how we think: **the downside is the part that
matters, and it should be transparent.** If that resonates, the same philosophy runs
through everything at [vetima.trade](https://vetima.trade).

## License

[MIT](LICENSE) © Vetima. Use it, fork it, ship it.

## Disclaimer

`drawdown-lens` is an educational and analytical tool. It is **not financial advice**,
not a recommendation to buy or sell anything, and past drawdown is no guarantee of
future drawdown. Markets can and do exceed their historical worst. Do your own research.
