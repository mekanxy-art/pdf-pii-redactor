# Prüfung aus Sicht eines neuen Nutzers: 24.10.2026

Das öffentliche ZIP von `mekanxy-art/pdf-pii-redactor` wurde ohne Anmeldung heruntergeladen und in einen neuen Ordner entpackt. Die geprüfte Anwendung entspricht Commit `1f57984a07d84962a664cc2c05f87ba829661737`.

- Keine vorhandene `.venv` im entpackten Projekt benutzt. Python 3.12 war auf dem Windows-Rechner bereits installiert.
- `start_redactor.bat --setup-only` hat eine neue Umgebung, die Pakete und das deutsche Modell erfolgreich eingerichtet.
- Danach dieselbe Startdatei mit `--no-browser --port 8570` ausgeführt. Der Browser wurde für den automatisierten Test separat geöffnet.
- Drei echte Browserabläufe erfolgreich: Text-PDF mit E-Mail/IBAN, automatische Namenserkennung ohne eigene Begriffe und eine gescannte PDF mit OCR plus eigenem Namen.
- In jedem Ablauf: PDF auswählen, Verarbeitung auslösen und Ergebnis herunterladen. Anschließend Ergebnisdateien erneut geöffnet und Text geprüft: Zielbegriffe entfernt, anderer Text erhalten. Bei OCR wurde die Ergebnisdatei erneut per OCR geprüft.
- Die 36 Tests aus dem öffentlichen Download bestanden ohne Überspringen. Ein ergänzter Integrationstest mit dem tatsächlich installierten deutschen Modell erhöht den Testsatz auf 37; auch dieser bestand.
- Der GitHub-Testlauf für den geprüften Anwendungscommit war erfolgreich: https://github.com/mekanxy-art/pdf-pii-redactor/actions/runs/40029235326

## Voraussetzungen und Grenzen der Aussage

Internet für die erste Einrichtung; installiertes Python 3.12. Für den OCR-Test waren Tesseract und die Sprachen `deu`/`eng` bereits auf dem Rechner vorhanden. Diese zusätzliche Systemsoftware wird vom Starter nicht installiert. Es wurde kein fabrikneuer Windows-Rechner getestet.

Geprüft wurden synthetische Dokumente. Die Prüfung belegt diese Abläufe, keine Fehlerfreiheit für beliebige PDFs oder vollständige Erkennungsqualität. Der aktuelle CI-Status steht unter GitHub Actions. macOS wurde nicht separat geprüft.
