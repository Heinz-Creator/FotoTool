# FotoTool 1.0

**FotoTool ist ein lokales Windows-Programm zur strukturierten Analyse, Sortierung und Wiederherstellung großer Fotosammlungen.
Alle Verarbeitungsschritte erfolgen vollständig offline auf dem eigenen Computer – ohne Cloud, Upload oder Tracking.

Das Ziel von FotoTool ist nicht nur das Sortieren von Bildern,
sondern das Wiederherstellen sinnvoller Ordnerstrukturen, selbst dann, wenn Metadaten fehlen.

---

## ✨ Zentrale Funktionen

### 1. Automatische Sortierung nach Aufnahmedatum

Fotos und Videos werden anhand von:

* EXIF-Aufnahmedatum (Kamera)
* Dateidatum (Fallback)

in eine klare Archivstruktur überführt:

```
Jahr → Monat → Ereignis / Kategorie
```

So entsteht ein dauerhaft wartbares Fotoarchiv.

---

### 2. Wiederaufbau fehlender Metadaten aus bestehenden Ordnernamen

Ein besonderes Merkmal von FotoTool:

Wenn Bilder **kein EXIF-Datum, keine GPS-Daten oder keine Metainformationen** besitzen,
kann FotoTool:

* vorhandene **alte Ordnerstrukturen analysieren**
* **Ordnernamen als Bedeutung erkennen**
  (z. B. „2018 Urlaub Italien“, „Geburtstag Oma“, „Baustelle Haus“)
* diese Informationen **in die Bild-Metadaten zurückschreiben**
* daraus anschließend eine **neue, saubere Archivstruktur erzeugen**

Damit lassen sich auch stark beschädigte oder unsortierte Sammlungen
wieder logisch rekonstruieren.

---

### 3. GPS-basierte Ortsstruktur

Wenn Fotos **GPS-Koordinaten** enthalten, kann FotoTool:

* den **Ort automatisch bestimmen**
* daraus eine **Ordnerebene nach Land / Stadt / Ort** erzeugen
* Ereignisse geografisch gruppieren

So entstehen z. B.:

```
2022 → 07 → Italien → Rom
2023 → 05 → Deutschland → Berlin
```

Alle Ortsabfragen erfolgen nur optional und können lokal bleiben.

---

### 4. Ereigniserkennung nach Zeitabständen („Events“)

FotoTool erkennt automatisch zusammengehörige Foto-Serien.

Dazu wird:

* die **zeitliche Distanz zwischen Aufnahmen** analysiert
* eine neue Gruppe begonnen, wenn ein definierter Abstand überschritten wird
  (z. B. mehrere Stunden oder Tage)

Ergebnis:

* einzelne **Urlaube, Feiern oder Ausflüge** werden als eigene Ereignisse erkannt
* jedes Ereignis kann einen **automatischen Ordnernamen** erhalten
* große Zeiträume werden logisch strukturiert statt nur nach Datum sortiert

Das entspricht der natürlichen Erinnerung des Menschen –
nicht nur einer reinen Kalenderstruktur.

---

### 5. Analyse unsortierter Dateien

FotoTool kann komplette Verzeichnisse untersuchen und ermitteln:

* wie viele Dateien bereits korrekt einsortiert sind
* welche Bilder **ohne Datum oder Struktur** vorliegen
* welche Zielordner sinnvoll wären

Damit wird sichtbar, **wo im Archiv noch Chaos existiert**.

---

### 6. Duplikate finden und bereinigen

Über integrierte Analyse können:

* identische Dateien
* ähnliche Bilder
* doppelte Backups

erkannt und entfernt werden.

Das reduziert Speicherbedarf und verhindert Mehrfach-Archive.

---

### 7. Vollständig lokale Verarbeitung

FotoTool arbeitet bewusst:

* **ohne Cloud**
* **ohne Benutzerkonto**
* **ohne Datensammlung**
* **ohne Internetzwang**

Alle Fotos bleiben dauerhaft unter eigener Kontrolle.

---

## Typische Einsatzszenarien

FotoTool wurde besonders für folgende Situationen entwickelt:

* jahrelang gewachsene, ungeordnete Handy-Fotos
* gemischte Backups aus verschiedenen Geräten
* verlorene Metadaten nach Kopieren oder Messenger-Export
* Wiederaufbau eines zentralen Familien-Fotoarchivs

---

## 🖥️ Systemanforderungen

* Windows 10 oder Windows 11
* Keine Installation zusätzlicher Software nötig
* Keine Internetverbindung erforderlich (außer optional für Ortsnamen über GPS)

---

## 📥 Download

Die aktuelle Version findest du hier:

**→ GitHub Releases:**
https://github.com/Heinz-Creator/FotoTool/releases

Einfach die **FotoTool.exe** herunterladen und starten.

---

## 🚀 Schnellstart

1. Programm starten
2. Import-Ordner auswählen (z. B. Handy-Fotos)
3. Ziel-Archiv wählen
4. **Sortieren starten**

Fertig.
FotoTool organisiert deine Bilder automatisch.

---

## 🔒 Datenschutz

FotoTool folgt einem einfachen Prinzip:

**Deine Fotos gehören dir.**

Deshalb:

* keine Übertragung ins Internet
* keine Telemetrie
* keine versteckten Dienste

---

## 🐞 Fehler melden & Feedback

Wenn etwas nicht funktioniert oder du eine Idee hast:

**→ GitHub Issues:**
https://github.com/Heinz-Creator/FotoTool/issues

Beschreibe dort kurz:

* Was passiert ist
* Was passieren sollte
* Deine Windows-Version

---

## 📜 Lizenz & verwendete Software

FotoTool nutzt Open-Source-Komponenten wie:

* ExifTool
* Czkawka
* Pillow

Die vollständigen Lizenztexte findest du im Programm unter **„Lizenzen“**.

---

## 👤 Autor

Andreas Heinig 
Privates Softwareprojekt zur nachhaltigen Organisation digitaler Erinnerungen.

---

## 🧭 Projektstatus

**Version 1.0 – Erste öffentliche Veröffentlichung**

Geplant für kommende Versionen:

* Stabilitäts-Updates
* Verbesserte Analyse unsortierter Dateien
* Weitere Automatisierungen

---

*Ein kleines Tool, gebaut aus einem einfachen Gedanken:*
**Fotos sollten sich selbst sortieren.**
