# Changelog

Format nach [Keep a Changelog](https://keepachangelog.com/de/1.1.0/), Versionierung nach [SemVer](https://semver.org/lang/de/).

## [Unreleased]

### Behoben
- Windows-Starter richtet die lokale Python-Umgebung und das deutsche Namensmodell automatisch ein.
- PDF-Dateien werden auch bei Verarbeitungsfehlern geschlossen; fehlende Modelle werden vor der Verarbeitung verständlich gemeldet.

### Hinzugefügt
- Öffentlicher ZIP-Download, Funktionstest und Hilfe zur Einrichtung in der README.
- Regressionstests für den ersten Start und die Freigabe von PDF-Dateien.

## [1.0.0] - 2026-10-03

### Hinzugefügt
- Erkennung von IBAN, Kreditkarte, Steuer-ID, E-Mail, Telefon und Geburtsdatum mit Prüfsummen-Validierung
- Namen- und Ortserkennung mit spaCy, Verbreitung erkannter Namen im Dokument
- Dauerhafte Schwärzung mit PyMuPDF, Entfernen von Metadaten und Anhängen
- OCR für gescannte Seiten (Tesseract), Entfernen von Bildern, manuelle Bereiche mit Vorschau
- Mehrere Durchgänge und Nachprüfung mit Liste möglicher Resttreffer
- Streamlit-Oberfläche, Kommandozeile, Tests und CI
