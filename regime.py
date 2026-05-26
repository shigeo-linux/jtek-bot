import numpy as np
import pandas as pd
from hmmlearn.hmm import GaussianHMM

# Regime → (holding, emoji)
REGIME_MAP = {
    'bull':     ('JTEK', '🟢'),
    'sideways': ('VOO',  '🟡'),
    'bear':     ('SGOV', '🔴'),
}


def build_features(df: pd.DataFrame) -> np.ndarray:
    """
    Three features that separate equity regimes cleanly:
      1. 5-day log return     — short-term momentum (less noisy than daily)
      2. 20-day realised vol  — regime volatility level
      3. Price vs 200d SMA    — long-term trend, z-scored
    All z-scored so HMM sees comparable scales.
    """
    close = df['close']

    ret5  = np.log(close / close.shift(5))
    vol20 = np.log(close / close.shift(1)).rolling(20).std() * np.sqrt(252)
    trend = (close - close.rolling(200).mean()) / close.rolling(200).std()

    feat = pd.DataFrame({'ret5': ret5, 'vol20': vol20, 'trend': trend})
    feat = feat.dropna()

    # Z-score each column to equalise influence
    feat = (feat - feat.mean()) / feat.std()
    return feat.values.astype(np.float64), feat.index


def fit_hmm(features: np.ndarray, n_states: int = 3,
            n_restarts: int = 20) -> GaussianHMM:
    best_model, best_score = None, -np.inf
    rng = np.random.default_rng(42)
    for _ in range(n_restarts):
        seed = int(rng.integers(0, 99999))
        try:
            m = GaussianHMM(
                n_components=n_states,
                covariance_type='diag',   # diag avoids degenerate full-cov solutions
                n_iter=500,
                tol=1e-4,
                random_state=seed,
            )
            m.fit(features)
            score = m.score(features)
            if score > best_score:
                best_score, best_model = score, m
        except Exception:
            continue
    return best_model


def label_states(model: GaussianHMM) -> dict[int, str]:
    """
    Rank states by (trend_z - vol20_z): rewards positive long-term trend,
    penalises high volatility. Gives bull/sideways/bear that aligns with
    JTEK (calm uptrend) / VOO (neutral) / SGOV (volatile downturn).
    """
    trend_z = model.means_[:, 2]   # feature 2 = price vs 200d SMA
    vol_z   = model.means_[:, 1]   # feature 1 = realised vol
    score   = trend_z - vol_z      # high trend + low vol = bull
    order   = np.argsort(score)
    return {order[0]: 'bear', order[1]: 'sideways', order[2]: 'bull'}


def infer_regime(model: GaussianHMM, features: np.ndarray,
                 labels: dict[int, str]) -> dict:
    states     = model.predict(features)
    posteriors = model.predict_proba(features)

    current_state = int(states[-1])
    regime        = labels[current_state]
    confidence    = float(posteriors[-1, current_state])

    probs = {'bull': 0.0, 'sideways': 0.0, 'bear': 0.0}
    for idx, name in labels.items():
        probs[name] += float(posteriors[-1, idx])

    history = []
    for i in range(-10, 0):
        s   = int(states[i])
        lbl = labels[s]
        history.append({
            'regime':     lbl,
            'holding':    REGIME_MAP[lbl][0],
            'confidence': float(posteriors[i, s]),
        })

    return {
        'regime':     regime,
        'holding':    REGIME_MAP[regime][0],
        'emoji':      REGIME_MAP[regime][1],
        'confidence': confidence,
        'p_bull':     probs['bull'],
        'p_sideways': probs['sideways'],
        'p_bear':     probs['bear'],
        'history':    history,
    }
