# JTEK/VOO/SGOV Rotation Bot

Daily Telegram signal bot that uses a 3-state Hidden Markov Model to detect equity market regimes and recommend which ETF to hold.

## Strategy

| Regime | Hold | Logic |
|--------|------|-------|
| 🟢 Bull | JTEK | Low volatility + positive trend above 200-day SMA |
| 🟡 Sideways | VOO | Neutral conditions — broad market exposure |
| 🔴 Bear | SGOV | High volatility + negative trend — park in T-bills |

**JTEK** — JPMorgan U.S. Tech Leaders ETF (actively managed, high-beta tech)  
**VOO** — Vanguard S&P 500 ETF  
**SGOV** — iShares 0-3 Month Treasury Bond ETF (~4-5% yield, near-cash)

## How it works

The HMM is trained on **3 years of daily VOO data** using three z-scored features:
1. **5-day log return** — short-term momentum
2. **20-day realised volatility** — regime volatility level
3. **Price vs 200-day SMA** — long-term trend signal

States are ranked by `trend_z − vol_z`: rewards calm uptrends (→ JTEK), penalises volatile downtrends (→ SGOV).

A systemd timer fires daily at **22:00 Oslo time** (after US market close). It sends:
- A **regime change alert** if the current regime differs from yesterday — with the specific ETF to switch into
- A **daily summary** with current regime, probabilities, and last 10 days of history

## Installation

```bash
cd jtek-bot
bash install.sh
```

The install script will:
- Install Python dependencies (`yfinance`, `hmmlearn`, `pandas`, `numpy`, `requests`)
- Prompt for your Telegram bot token and chat ID
- Install and enable a systemd user timer

## Manual test run

```bash
python3 runner.py
```

## Logs

```bash
tail -f ~/.config/jtek-bot/jtek-bot.log
systemctl --user status jtek-bot.timer
```

## Config

Edit `~/.config/jtek-bot/config.json` to adjust lookback window, HMM restarts, or Telegram credentials.

## Requirements

- Python 3.10+
- `yfinance`, `hmmlearn`, `pandas`, `numpy`, `requests`
