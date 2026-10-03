"""Manuelle Schwaerzbereiche: Parser fuer Eingaben wie '1;20;30;80;40' (Prozent der Seite)."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class Region:
    page: int | None  # 1-basiert, None = alle Seiten
    x0: float         # Anteile 0..1 von links/oben
    y0: float
    x1: float
    y1: float


def parse_regions(text: str) -> list[Region]:
    """Zeile: Seite;links;oben;rechts;unten  (Prozent, Seite = Zahl oder * fuer alle). '#' = Kommentar."""
    out: list[Region] = []
    for no, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split(";")]
        if len(parts) != 5:
            raise ValueError(f"Zeile {no}: erwartet 'Seite;links;oben;rechts;unten', gefunden: '{line}'")
        pg = parts[0].lower()
        if pg in ("*", "alle"):
            page = None
        elif pg.isdigit() and int(pg) >= 1:
            page = int(pg)
        else:
            raise ValueError(f"Zeile {no}: Seite muss eine Zahl ab 1 oder * sein, nicht '{parts[0]}'")
        try:
            x0, y0, x1, y1 = (float(p.replace(",", ".")) for p in parts[1:])
        except ValueError:
            raise ValueError(f"Zeile {no}: Prozentwerte muessen Zahlen sein: '{line}'") from None
        if not all(0 <= v <= 100 for v in (x0, y0, x1, y1)):
            raise ValueError(f"Zeile {no}: Prozentwerte muessen zwischen 0 und 100 liegen")
        if x0 >= x1 or y0 >= y1:
            raise ValueError(f"Zeile {no}: links < rechts und oben < unten erforderlich")
        out.append(Region(page, x0 / 100, y0 / 100, x1 / 100, y1 / 100))
    return out
