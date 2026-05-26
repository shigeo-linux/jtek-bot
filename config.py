import json
import os

CONFIG_DIR = os.path.expanduser('~/.config/jtek-bot')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.json')
STATE_FILE  = os.path.join(CONFIG_DIR, 'state.json')
LOG_FILE    = os.path.join(CONFIG_DIR, 'jtek-bot.log')

DEFAULTS = {
    'telegram_token':  '',
    'telegram_chat_id': '',
    'lookback_days':   756,   # 3 years for HMM training
    'n_states':        3,
    'n_restarts':      20,
}


class Config:
    def __init__(self):
        self._data = dict(DEFAULTS)
        os.makedirs(CONFIG_DIR, exist_ok=True)
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE) as f:
                    self._data.update(json.load(f))
            except (json.JSONDecodeError, OSError):
                pass

    def save(self):
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self._data, f, indent=2)

    def get(self, key, fallback=None):
        return self._data.get(key, fallback if fallback is not None else DEFAULTS.get(key))

    def set(self, key, value):
        self._data[key] = value

    @property
    def telegram_token(self):   return self._data.get('telegram_token', '')
    @property
    def telegram_chat_id(self): return self._data.get('telegram_chat_id', '')
    @property
    def lookback_days(self):    return int(self._data.get('lookback_days', 756))
    @property
    def n_states(self):         return int(self._data.get('n_states', 3))
    @property
    def n_restarts(self):       return int(self._data.get('n_restarts', 20))


def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def save_state(data: dict):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(data, f, indent=2)
