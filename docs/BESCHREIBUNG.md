# KlarCRM – Benutzerbeschreibung

| | |
|---|---|
| **Programm** | KlarCRM – Vertrieb, Kalkulation Spritzguss, Angebote |
| **Version** | 1.23 (Stand 17.11.2026) |
| **Für** | Vertrieb, Kalkulation, Einkauf, Geschäftsführung, Gesellschafter |

> Diese Beschreibung erklärt, **wie man mit KlarCRM arbeitet**. Die genauen Regeln und Rechenwege stehen im
> Lastenheft (Menü *Dokumentation* → *Lastenheft*). Auf jeder Seite steht oben zusätzlich eine kurze Hilfe
> „So arbeiten Sie hier“.

## 1. Der Arbeitsablauf auf einen Blick

1. **Anfrage kommt rein** → unter *Kalkulation* „+ Neue Anfrage / Kalkulation“ (Kunde, Artikel, Zeichnung als Dokument).
2. **Artikelanalyse / Machbarkeit** im Reiter *Artikelanalyse*: Schließkraft, Wandstärke, Machbarkeit.
3. **Kalkulieren** im Reiter *Kalkulation*: Standort, Maschine, Material, Zyklus, Personal, Zukaufteile, Werkzeug.
   Jede Speicherung ist eine neue **Version** (nachvollziehbar, nichts wird überschrieben).
4. **Freigabe**, falls nötig (Großprojekt ab 250.000 € Umsatz oder Invest, oder Marge zu niedrig) – Vier-Augen-Prinzip.
5. **Angebot erstellen / aktualisieren** → Angebot im Firmenlayout, als PDF drucken und versenden.
6. **Nachfassen**: Anrufe mit Ergebnis dokumentieren, Wiedervorlagen als Aufgaben.
7. **Gewonnen** oder **Verloren** (Verlustgrund ist Pflicht) bzw. **Kein Angebot** (mit Grund).
8. **Nachkalkulation** nach Serienstart mit Ampel.

## 2. Menü

| Menüpunkt | Wofür |
|---|---|
| Dashboard | Kennzahlen: Pipeline, Anfragen in Bearbeitung, Angebote beim Kunden, Großprojekte, Auslastung, Aufgaben |
| Pipeline | Verkaufschancen als Board (Drag & Drop) oder Liste |
| Firmen, Kontakte | Kunden, Interessenten, Lieferanten und Ansprechpartner |
| Aktivitäten | Aufgaben, Anrufe, Termine, Wiedervorlagen |
| Kalkulation | Alle Anfragen und Kalkulationen mit Status, Preis, Umsatz, letztem Anruf |
| Auslastung | Maschinenstunden der kommenden Jahre gegen die Kapazität |
| Auswertungen | Berichte nach Kunde, Maschinengröße, Verlustgründen, Vertrieb … |
| Angebote | Alle Angebote mit Status |
| Beschaffung | Anfragen an Werkzeugmacher und Lieferanten, Angebotsvergleich |
| Stammdaten | Maschinen, Standorte, Materialien, Zukaufteile, Parameter, Vorlagen |
| Änderungswünsche | Testrückmeldungen und Wünsche ans Programm mit Prüfprotokoll |
| Dokumentation | Diese Beschreibung und das Lastenheft, Download als Word |
| Protokoll | Systemprotokoll: wer hat wann welche Daten geändert (nur Admin/Freigabe/Gesellschafter) |

## 3. Kalkulation bedienen

### 3.1 Speichern
- Oben steht die **Speicherleiste**. Sie bleibt beim Scrollen sichtbar und wird **gelb**, sobald etwas geändert ist.
- „💾 Speichern (Version n)“ oder **Strg+S** speichert eine neue Version. Optional kurz notieren, was geändert wurde.
- „Verwerfen“ nimmt alle ungespeicherten Änderungen zurück. Wer die Seite mit ungespeicherten Änderungen verlässt,
  wird gefragt.

### 3.2 Zahlen eingeben
- Alle Zahlenfelder nehmen freie Eingaben an: `12,5` oder `12.5`, auch mit Tausenderpunkt `1.250,75`.
- Felder mit gelber Markierung „≠ Standard“ weichen vom Stammdatenwert ab; ein Klick auf ↺ setzt zurück.
- Rüstzeiten werden in **Minuten** eingegeben.

### 3.3 Standort wechseln
- Feld *Fertigungsstandort*: Beim Wechsel übernimmt die Kalkulation die Sätze des Standorts (Lohnsätze, Zuschläge,
  Strompreis, CO₂ …) und eine vergleichbare Maschine des Standorts.
- Von Hand eingegebene Werte bleiben stehen und werden als Hinweis aufgelistet. „Alle Sätze des Standorts übernehmen“
  ersetzt auch diese.
- Hat der Standort keine eigene Maschine, bleibt die Maschine; der Stundensatz wird mit dem **Faktor
  Maschinenstundensatz** des Standorts umgerechnet (Stammdaten → Standorte).
- *Standortvergleich* rechnet dieselbe Kalkulation für alle Standorte nebeneinander.

### 3.4 Angebot
- „→ Angebot erstellen / aktualisieren“: Es gibt **ein** offenes Angebot je Kalkulation. Ein Entwurf wird mit der
  aktuellen Version aktualisiert; ein bereits versendetes Angebot bekommt eine **Revision** (A26-0001-R1).
- Mehrere Artikel desselben Kunden: in der Kalkulationsliste anhaken → „Sammelangebot“.
- Angebote gehen nur an Kunden, Interessenten oder Partner – nie an Lieferanten.

### 3.5 Verloren / Kein Angebot
- Verloren nur mit Grund: Werkzeug zu teuer, Preis zu teuer, Projekt eingestellt, Kunde hat Projekt nicht erhalten,
  Vorrichtung zu teuer, Investition zu teuer, Lieferzeit/Kapazität, technisch nicht machbar oder Sonstiges (Freitext).
- In der Pipeline öffnet das Ziehen auf „Verloren“ automatisch diesen Dialog.

## 4. Stammdaten

- **Maschinen & Anlagen**: Stundensatz, Instandhaltung, Produktivität, Personalanteile, Standort, Schichtmodell
  (1 Schicht 1.920 h, 2 Schichten 3.840 h, 3 Schichten 5.760 h), *Bestandsmaschine* oder *Planmaschine*.
  Maschinen in offenen Kalkulationen lassen sich nicht löschen (deaktivieren). Löschen nur durch zwei Administratoren:
  Admin A stellt den Löschantrag, Admin B bestätigt.
- **Standorte**: abweichende Sätze je Standort; leeres Feld = Gruppenstandard. Erst nach „Speichern“ wirksam.
- **Parameter**: Standardwerte für neue Kalkulationen, Großprojekt- und Freigabegrenzen (Standard 250.000 €).
- Import aus Excel/CSV für Firmen, Kontakte, Maschinen, Materialien und Zukaufteile (Administratoren).

## 5. Auslastung lesen
- **Fest** = Grundauslastung aus Bestandsaufträgen + gewonnene Kalkulationen (sicher belegt).
- **Erwartet** = Fest + offene Anfragen × Wahrscheinlichkeit. **Maximal** = Fest + alle offenen zu 100 %.
- Ampel: unter 60 % frei · 60–85 % gut ausgelastet · 85–100 % knapp · ab 100 % überlastet.

## 6. Änderungswünsche und Prüfung
- Menü *Änderungswünsche*: alle Punkte aus Testrückmeldungen (z. B. REV01) mit Status.
- Status „Umgesetzt – bitte prüfen“: Zeile öffnen, **Prüfanweisung** durchgehen, **Prüfergebnis** eintragen, Status
  **Geprüft ✓** oder **Nachbessern** setzen. So entsteht ein lückenloser Nachweis (IATF 16949 / ISO 14001).
- Neue Wünsche mit „+ Änderungswunsch“ erfassen; sie bekommen automatisch eine Nummer WUN-0001 ….
- Export als CSV für Excel.

## 7. Nummern
| Vorgang | Format | Beispiel |
|---|---|---|
| Kalkulation | K + Jahr + laufende Nr. | K26-0001 |
| Angebot | A + Jahr + laufende Nr., Revision -R | A26-0001, A26-0001-R1 |
| Beschaffung | B + Jahr + laufende Nr. | B26-0001 |
| Änderungswunsch | REV01-… oder WUN- | REV01-B01, WUN-0001 |

Ältere Nummern (KA-2026-…, AN-2026-…) bleiben unverändert erhalten.

## 8. Rollen
- **Administrator**: alles, inkl. Benutzer, Parameter, Firma & Layout, Löschen (Vier Augen bei Maschinen).
- **Vertrieb**: anlegen, kalkulieren, Angebote; Stammdaten lesen.
- **Gesellschafter**: alles sehen, nichts ändern.
- Zusatzrecht „darf freigeben“ für Freigaben im Vier-Augen-Prinzip.

---
© SB/Thinkworks
