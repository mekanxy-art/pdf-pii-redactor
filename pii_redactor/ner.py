"""Optionale Namens-/Ortserkennung mit spaCy (lokal)."""
from __future__ import annotations
from functools import lru_cache

from .detectors import Finding

DEFAULT_LABELS = {"PER": "PERSON", "LOC": "LOCATION"}
MODELS = ("de_core_news_md", "de_core_news_sm", "de_core_news_lg")


@lru_cache(maxsize=1)
def load_model():
    import spacy
    for name in MODELS:
        try:
            return spacy.load(name)
        except OSError:
            continue
    raise RuntimeError("Kein deutsches spaCy-Modell gefunden: python -m spacy download de_core_news_md")


def make_ner(nlp=None, labels=None, min_len: int = 3, score: float = 0.6):
    labels = labels or DEFAULT_LABELS

    def run(text: str) -> list[Finding]:
        model = nlp or load_model()
        out: list[Finding] = []
        step = 100_000
        for off in range(0, len(text), step):
            for ent in model(text[off:off + step]).ents:
                if ent.label_ in labels and len(ent.text.strip()) >= min_len:
                    out.append(Finding(off + ent.start_char, off + ent.end_char,
                                       labels[ent.label_], score, ent.text))
        return out

    return run
