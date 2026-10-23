"""Set up and launch the local UI from an extracted project, including first use."""
from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import subprocess
import sys


def environment_python(root: Path) -> Path:
    return root / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def prepare_environment(root: Path) -> Path:
    requirements = root / "requirements.txt"
    if not (root / "app.py").is_file() or not requirements.is_file():
        raise RuntimeError("Projektdateien fehlen. Bitte das gesamte ZIP entpacken, nicht nur die Startdatei.")
    python = environment_python(root)
    if not python.is_file():
        print("Erster Start: Die lokale Python-Umgebung wird eingerichtet.", flush=True)
        subprocess.run([sys.executable, "-m", "venv", str(root / ".venv")], check=True, cwd=root)
    marker = root / ".venv" / ".redactor-requirements.sha256"
    wanted = hashlib.sha256(requirements.read_bytes()).hexdigest()
    previous = marker.read_text(encoding="ascii").strip() if marker.is_file() else ""
    ready = False
    if previous == wanted:
        result = subprocess.run(
            [str(python), "-c", "import streamlit, spacy, pymupdf, de_core_news_md"],
            cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        ready = result.returncode == 0
    if not ready:
        print("Benoetigte Pakete werden installiert/geprueft. Beim ersten Start ist Internet noetig; dies kann einige Minuten dauern.", flush=True)
        subprocess.run(
            [str(python), "-m", "pip", "install", "--disable-pip-version-check", "-r", str(requirements)],
            check=True, cwd=root,
        )
        marker.write_text(wanted, encoding="ascii")
    return python


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="PDF-Redactor einrichten und lokal starten")
    parser.add_argument("--setup-only", action="store_true", help="Nur die lokale Umgebung einrichten")
    parser.add_argument("--no-browser", action="store_true", help="Browser nicht automatisch oeffnen")
    parser.add_argument("--port", type=int, default=8501, help="Lokaler Port, Standard 8501")
    args = parser.parse_args(argv)
    if not 1 <= args.port <= 65535:
        parser.error("Port muss zwischen 1 und 65535 liegen.")
    root = Path(__file__).resolve().parent
    try:
        python = prepare_environment(root)
        if args.setup_only:
            print("Einrichtung abgeschlossen.", flush=True)
            return 0
        print(f"PDF-Redactor startet unter http://127.0.0.1:{args.port}", flush=True)
        print("Dieses Fenster offen lassen. Beenden mit Strg+C.", flush=True)
        return subprocess.run(
            [str(python), "-m", "streamlit", "run", str(root / "app.py"),
             "--server.address", "127.0.0.1", "--server.port", str(args.port),
             "--server.headless", "true" if args.no_browser else "false",
             "--browser.gatherUsageStats", "false"],
            cwd=root,
        ).returncode
    except KeyboardInterrupt:
        return 0
    except subprocess.CalledProcessError as error:
        print(f"Einrichtung/Start fehlgeschlagen (Exit {error.returncode}). Bitte die Meldung darueber pruefen. Fuer die Ersteinrichtung ist Internet noetig.", file=sys.stderr)
        return 1
    except (OSError, RuntimeError) as error:
        print(f"Start nicht moeglich: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
