"""Loads the trained model once and returns category probabilities."""
import json
import re
from functools import lru_cache
import joblib
from .. import config

_DEV = re.compile(r"[\u0900-\u097F]")


def detect_language(text: str) -> str:
    """Script-based: mostly Devanagari -> Hindi, otherwise English. (Hinglish/Marathi = future work.)"""
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return "English"
    dev = sum(1 for c in letters if _DEV.match(c))
    return "Hindi" if dev / len(letters) > 0.5 else "English"


class Classifier:
    def __init__(self, model_dir=config.MODEL_DIR):
        path = model_dir / "model.joblib"
        if not path.exists():
            raise RuntimeError(f"Model not found at {path}. Train it first:  python ml/src/train_baseline.py")
        self.model = joblib.load(path)
        cfg_path = model_dir / "routing_config.json"
        self.cfg = json.loads(cfg_path.read_text()) if cfg_path.exists() else {}

    def predict(self, text: str) -> dict:
        proba = self.model.predict_proba([text.strip()])[0]
        return {str(c): float(p) for c, p in zip(self.model.classes_, proba)}


@lru_cache(maxsize=1)
def get_classifier() -> Classifier:
    return Classifier()
