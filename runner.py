#!/usr/bin/env python3
"""JTEK/VOO/SGOV rotation bot — daily regime signal via Telegram."""

import sys
import os
import datetime
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config, LOG_FILE, load_state, save_state
from data import fetch_ohlcv, fetch_close
from regime import build_features, fit_hmm, label_states, infer_regime, REGIME_MAP

import requests

os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
logging.basicConfig(filename=LOG_FILE, level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s')


def send_message(token: str, chat_id: str, text: str):
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    resp = requests.post(url, json={
        'chat_id': chat_id, 'text': text, 'parse_mode': 'HTML',
    }, timeout=30)
    if not resp.ok:
        raise RuntimeError(f'Telegram error: {resp.json().get("description", resp.text)}')


def format_change_alert(prev: str, result: dict, date: str) -> str:
    prev_holding = REGIME_MAP.get(prev, ('?', '⚪'))[0]
    lines = [
        f'⚡ <b>REGIME CHANGE</b> — JTEK/VOO/SGOV',
        f'{date}',
        '',
        f'{REGIME_MAP[prev][1]} {prev.upper()} → {result["emoji"]} {result["regime"].upper()}',
        f'🔄 <b>Action: Switch {prev_holding} → {result["holding"]}</b>',
        '',
        f'Bull: {result["p_bull"]*100:.1f}%  |  '
        f'Sideways: {result["p_sideways"]*100:.1f}%  |  '
        f'Bear: {result["p_bear"]*100:.1f}%',
        f'Confidence: {result["confidence"]*100:.1f}%',
    ]
    return '\n'.join(lines)


def format_daily_summary(result: dict, prices: dict, date: str) -> str:
    lines = [
        f'📊 <b>JTEK/VOO/SGOV Daily Signal</b> — {date}',
        '',
        f'{result["emoji"]} <b>{result["regime"].upper()}</b> — '
        f'{result["confidence"]*100:.1f}% confidence',
        f'📌 Hold: <b>{result["holding"]}</b>',
        '',
        f'Bull: {result["p_bull"]*100:.1f}%  |  '
        f'Sideways: {result["p_sideways"]*100:.1f}%  |  '
        f'Bear: {result["p_bear"]*100:.1f}%',
        '',
        '<b>Prices</b>',
    ]
    for ticker, price in prices.items():
        lines.append(f'  {ticker}: ${price:.2f}')

    lines += ['', '<b>Last 10 days</b>']
    for entry in result['history']:
        regime  = entry['regime'].capitalize()
        holding = entry['holding']
        conf    = entry['confidence'] * 100
        lines.append(f'  {regime:<10} → {holding:<5}  {conf:.0f}%')

    return '\n'.join(lines)


def run():
    config = Config()
    today  = datetime.date.today().isoformat()

    if not config.telegram_token or not config.telegram_chat_id:
        logging.error('Telegram not configured — edit ~/.config/jtek-bot/config.json')
        sys.exit(1)

    try:
        logging.info('Fetching price data')
        voo_df = fetch_ohlcv('VOO',  config.lookback_days)
        jtek   = fetch_close('JTEK', 500)
        sgov   = fetch_close('SGOV', 500)

        prices = {
            'VOO':  float(voo_df['close'].iloc[-1]),
            'JTEK': float(jtek.iloc[-1]),
            'SGOV': float(sgov.iloc[-1]),
        }

        logging.info('Building features and training HMM on VOO')
        features, feat_index = build_features(voo_df)
        model    = fit_hmm(features, config.n_states, config.n_restarts)
        labels   = label_states(model)
        result   = infer_regime(model, features, labels)

        regime   = result['regime']
        logging.info(f'Regime: {regime} ({result["confidence"]*100:.1f}%)')

        state      = load_state()
        prev_regime = state.get('regime')
        changed    = prev_regime is not None and prev_regime != regime

        # Send change alert first if regime flipped
        if changed:
            alert = format_change_alert(prev_regime, result, today)
            send_message(config.telegram_token, config.telegram_chat_id, alert)
            logging.info(f'Regime change: {prev_regime} → {regime}')

        # Always send daily summary
        summary = format_daily_summary(result, prices, today)
        send_message(config.telegram_token, config.telegram_chat_id, summary)

        save_state({
            'regime':     regime,
            'holding':    result['holding'],
            'confidence': result['confidence'],
            'date':       today,
        })
        logging.info('Done')

    except Exception as e:
        logging.error(f'Error: {e}')
        try:
            send_message(config.telegram_token, config.telegram_chat_id,
                         f'⚠️ <b>JTEK Bot error</b>\n{str(e)[:200]}')
        except Exception:
            pass
        sys.exit(1)


if __name__ == '__main__':
    run()
