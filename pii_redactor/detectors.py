"""Erkennung sensibler Daten: Regex-Kandidaten + Pruefsummen-Validierung + Namen-Verbreitung."""
from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Callable, Iterable


@dataclass(frozen=True)
class Finding:
    start: int
    end: int
    type: str
    score: float
    text: str


def luhn_valid(num: str) -> bool:
    digits = [int(c) for c in num if c.isdigit()]
    if not 13 <= len(digits) <= 19:
        return False
    total = 0
    for i, d in enumerate(reversed(digits)):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def iban_valid(s: str) -> bool:
    s = re.sub(r"\s", "", s).upper()
    if not re.fullmatch(r"[A-Z]{2}\d{2}[A-Z0-9]{11,30}", s):
        return False
    if s.startswith("DE") and len(s) != 22:
        return False
    rearranged = s[4:] + s[:4]
    return int("".join(str(int(c, 36)) for c in rearranged)) % 97 == 1


def steuer_id_valid(s: str) -> bool:
    d = re.sub(r"\D", "", s)
    if len(d) != 11 or d[0] == "0":
        return False
    first10 = d[:10]
    counts = {c: first10.count(c) for c in set(first10)}
    if max(counts.values()) > 3 or len(counts) < 2:
        return False
    if sum(1 for v in counts.values() if v >= 2) < 1:
        return False
    if any(first10[i] == first10[i + 1] == first10[i + 2] for i in range(8)):
        return False
    product = 10
    for ch in first10:
        total = (int(ch) + product) % 10
        if total == 0:
            total = 10
        product = (total * 2) % 11
    check = 11 - product
    if check == 10:
        check = 0
    return check == int(d[10])


def phone_valid(s: str) -> bool:
    return 7 <= len(re.sub(r"\D", "", s)) <= 15


def _always(_: str) -> bool:
    return True


RULES: list[tuple[str, re.Pattern, Callable[[str], bool], float]] = [
    ("EMAIL", re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}"), _always, 0.95),
    ("IBAN", re.compile(r"\b[A-Z]{2}\d{2}(?:[ \-]?[A-Z0-9]{4}){2,7}(?:[ \-]?[A-Z0-9]{1,4})?\b"), iban_valid, 0.99),
    ("CREDIT_CARD", re.compile(r"(?<!\d)(?:\d[ \-]?){12,18}\d(?!\d)"), luhn_valid, 0.9),
    ("STEUER_ID", re.compile(r"(?<!\d)\d{2}[ /]?\d{3}[ /]?\d{3}[ /]?\d{3}(?!\d)"), steuer_id_valid, 0.7),
    ("PHONE", re.compile(r"(?<![\w])(?:\+|00)?\d[\d ()/\-]{6,}\d(?![\w])"), phone_valid, 0.6),
    ("DATE_OF_BIRTH", re.compile(r"(?i)(?:geb(?:oren)?\.?(?: am)?|geburtsdatum|dob)[:\s]*\d{1,2}\.\d{1,2}\.\d{2,4}"), _always, 0.9),
]


def _overlaps(a: Finding, b: Finding) -> bool:
    return a.start < b.end and b.start < a.end


def resolve_overlaps(findings: Iterable[Finding]) -> list[Finding]:
    ordered = sorted(findings, key=lambda f: (-f.score, -(f.end - f.start), f.start))
    kept: list[Finding] = []
    for f in ordered:
        if not any(_overlaps(f, k) for k in kept):
            kept.append(f)
    return sorted(kept, key=lambda f: f.start)


def _propagate_names(text: str, findings: list[Finding]) -> list[Finding]:
    """Erkannte Personennamen und mehrteilige eigene Begriffe werden im ganzen Text erneut gesucht.
    Volle Namen: Gross-/Kleinschreibung egal. Namensteile (>= 4 Buchstaben): nur Original, GROSS oder Gross."""
    sources = [f for f in findings
               if f.type == "PERSON" or (f.type == "CUSTOM_TERM" and " " in f.text.strip())]
    full: set[str] = set()
    parts: set[str] = set()
    for f in sources:
        name = " ".join(f.text.split())
        full.add(name)
        for p in name.split():
            p = p.strip(".,;:()")
            if len(p) >= 4 and p.isalpha():
                parts.add(p)
    out: list[Finding] = []
    for name in full:
        rx = re.compile(r"(?<!\w)" + r"\s+".join(re.escape(w) for w in name.split()) + r"(?!\w)", re.IGNORECASE)
        out += [Finding(m.start(), m.end(), "PERSON", 0.6, m.group()) for m in rx.finditer(text)]
    for p in parts:
        variants = {p, p.upper(), p.capitalize()}
        rx = re.compile(r"(?<!\w)(?:" + "|".join(re.escape(v) for v in sorted(variants)) + r")(?!\w)")
        out += [Finding(m.start(), m.end(), "PERSON", 0.55, m.group()) for m in rx.finditer(text)]
    return out


def detect(text: str, terms: Iterable[str] = (), types: set[str] | None = None,
           ner: Callable[[str], list[Finding]] | None = None,
           propagate: bool = True) -> list[Finding]:
    found: list[Finding] = []
    for typ, rx, validate, score in RULES:
        if types and typ not in types:
            continue
        for m in rx.finditer(text):
            if validate(m.group()):
                found.append(Finding(m.start(), m.end(), typ, score, m.group()))
    for term in terms:
        term = term.strip()
        if not term:
            continue
        for m in re.finditer(re.escape(term), text, flags=re.IGNORECASE):
            found.append(Finding(m.start(), m.end(), "CUSTOM_TERM", 0.9, m.group()))
    if ner is not None:
        found.extend(ner(text))
    resolved = resolve_overlaps(found)
    if propagate:
        resolved = resolve_overlaps(resolved + _propagate_names(text, resolved))
    return resolved
