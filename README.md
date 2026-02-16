# FotoTool 1.0

**FotoTool ist ein lokales Windows-Programm zur strukturierten Analyse, Sortierung und Wiederherstellung großer Fotosammlungen.  
Alle Verarbeitungsschritte erfolgen vollständig offline auf dem eigenen Computer – ohne Cloud, Upload oder Tracking.**

Das Ziel von FotoTool ist nicht nur das Sortieren von Bildern,  
sondern das Wiederherstellen sinnvoller Ordnerstrukturen, selbst dann, wenn Metadaten fehlen.

---

## ✨ Zentrale Funktionen

### 1. Automatische Sortierung nach Datum, Kategorie oder Ereignis

Fotos und Videos werden anhand von:

- EXIF-Aufnahmedatum (Kamera)
- Dateidatum (Fallback)
- Zeitabständen zwischen Aufnahmen (Event-Erkennung)

in eine klare Archivstruktur überführt, zum Beispiel:

Jahr → Monat → Ereignis
Land → Ort → Jahr → Monat
WhatsApp → Jahr → Monat
Screenshots → Jahr → Monat

So entsteht ein dauerhaft wartbares Fotoarchiv.

---

### 2. Wiederaufbau fehlender Metadaten aus bestehenden Ordnernamen

Ein zentrales Merkmal von FotoTool:

Wenn Bilder **kein EXIF-Datum, keine GPS-Daten oder keine Metainformationen** besitzen,  
kann FotoTool:

- vorhandene **alte Ordnerstrukturen analysieren**
- **Ordnernamen als Bedeutung erkennen**  
  (z. B. „2018 Urlaub Italien“, „Geburtstag Oma“, „Baustelle Haus“)
- diese Informationen **als Tags speichern**
- daraus anschließend eine **neue, saubere Archivstruktur erzeugen**

Damit lassen sich auch stark beschädigte oder unsortierte Sammlungen  
wieder logisch rekonstruieren.

---

### 3. GPS-basierte Ortsstruktur

Wenn Fotos **GPS-Koordinaten** enthalten, kann FotoTool:

- den **Ort automatisch bestimmen**
- daraus eine **Ordnerebene nach Land und Stadt** erzeugen
- Ereignisse geografisch gruppieren

Alle Ortsabfragen erfolgen nur optional.  
Die Verarbeitung bleibt lokal, es gibt **keine Cloud-Speicherung**.

---

### 4. Ereigniserkennung nach Zeitabständen („Events“)

FotoTool erkennt automatisch zusammengehörige Foto-Serien:

- Analyse der **zeitlichen Distanz zwischen Aufnahmen**
- neue Gruppe bei überschrittenem Zeitabstand  
  (z. B. mehrere Stunden oder Tage)
- automatische **Event-Ordner mit Datum, Ort oder Feiertag**

So entstehen logisch strukturierte Erinnerungsblöcke  
statt reiner Kalender-Ordner.

---

### 5. Analyse unsortierter Dateien

FotoTool kann komplette Verzeichnisse untersuchen und anzeigen:

- wie viele Dateien bereits korrekt einsortiert sind
- welche Bilder **ohne Datum oder Struktur** vorliegen
- welche Zielordner sinnvoll wären

Unsortierte Dateien können anschließend **gezielt verschoben oder bereinigt** werden.

---

### 6. Duplikate finden und sicher bereinigen

Über integrierte Analyse können erkannt werden:

- identische Dateien
- doppelte Backups
- unnötige Kopien

Duplikate werden zunächst in einen **Wiederherstellungs-Ordner** verschoben  
und können bei Bedarf rückgängig gemacht werden.

---

### 7. Vollständig lokale Verarbeitung

FotoTool arbeitet bewusst:

- **ohne Cloud**
- **ohne Benutzerkonto**
- **ohne Datensammlung**
- **ohne Tracking**

Alle Fotos bleiben dauerhaft unter eigener Kontrolle.

---

## Typische Einsatzszenarien

FotoTool wurde besonders für folgende Situationen entwickelt:

- jahrelang gewachsene, ungeordnete Handy-Fotos
- gemischte Backups aus verschiedenen Geräten
- verlorene Metadaten nach Kopieren oder Messenger-Export
- Wiederaufbau eines zentralen Familien-Fotoarchivs

---

## 🖥️ Systemanforderungen

- Windows 10 oder Windows 11  
- Keine zusätzliche Softwareinstallation nötig  
- Internet nur optional für Ortsnamen-Auflösung bei GPS

---

## 📥 Download

Die aktuelle Version findest du hier:

**→ GitHub Releases**  
https://github.com/Heinz-Creator/FotoTool/releases

Einfach die **Setup-Datei oder EXE** herunterladen und starten.

---

## 🚀 Schnellstart

1. Programm starten  
2. Import-Ordner auswählen (z. B. Handy-Fotos)  
3. Ziel-Archiv wählen  
4. **Simulation prüfen (optional)**  
5. **Sortieren starten**

FotoTool organisiert deine Bilder automatisch.

---

## 🔒 Datenschutz

FotoTool folgt einem einfachen Prinzip:

**Deine Fotos gehören dir.**

Deshalb:

- keine Internetübertragung  
- keine Telemetrie  
- keine versteckten Dienste  

---

## 🐞 Fehler melden & Feedback

**→ GitHub Issues**  
https://github.com/Heinz-Creator/FotoTool/issues

Bitte kurz beschreiben:

- Was passiert ist  
- Was passieren sollte  
- Deine Windows-Version  

---

## 📜 Lizenz & verwendete Software

FotoTool nutzt Open-Source-Komponenten wie:

- ExifTool  
- Czkawka  
- Pillow  

Die vollständigen Lizenztexte findest du im Programm unter **„Lizenzen“**.

---

## 👤 Autor

Andreas Heinig  
Privates Softwareprojekt zur nachhaltigen Organisation digitaler Erinnerungen.

---

## 🧭 Projektstatus

**Version 1.0 – Erste stabile GUI-Version mit Events, Analyse und Duplikat-Bereinigung**

Geplant für kommende Versionen:

- weitere Stabilitäts- und Performance-Verbesserungen  
- erweiterte Analyse unsortierter Dateien  
- zusätzliche Automatisierungen im Archiv-Workflow  

---

*Ein kleines Tool, gebaut aus einem einfachen Gedanken:*  
**Fotos sollten sich selbst sortieren.**
