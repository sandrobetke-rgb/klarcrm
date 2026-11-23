# KlarCRM – Benutzerbeschreibung

| | |
|---|---|
| **Programm** | KlarCRM – Vertrieb, Kalkulation Spritzguss, Angebote |
| **Version** | 1.28 (Stand 23.11.2026) |
| **Für** | Vertrieb, Kalkulation, Einkauf, Geschäftsführung, Gesellschafter |

> Diese Beschreibung erklärt, **wie man mit KlarCRM arbeitet**. Die genauen Regeln und Rechenwege stehen im
> Lastenheft (Menü *Dokumentation* → *Lastenheft*). Auf jeder Seite steht oben zusätzlich eine kurze Hilfe
> „So arbeiten Sie hier“.

## 1. Der Arbeitsablauf auf einen Blick

Alles hängt an der **Anfrage** (Menü *Anfragen*): eine Anfrage je Kunde und Projekt, darunter beliebig viele Artikel
(je Artikel eine Kalkulation) und **ein** Angebot. Die Schrittleiste oben in der Anfrage zeigt immer, was als Nächstes
dran ist.

1. **Anfrage anlegen** – *Anfragen* oder *Pipeline* → „+ Neue Anfrage“: Projektname frei, Kunde, Ansprechpartner,
   Eingang, Abgabetermin. Potenziale ohne konkrete Anfrage als „+ Lead“.
2. **Artikel erfassen** – in der Anfrage „+ Artikel / Kalkulation“ (optional mit den Werten eines anderen Artikels).
3. **Artikelanalyse** (Reiter 1 der Kalkulation): Schließkraft, Kühlzeit, Vorschlag Maschinengröße, Prüfpunkte,
   Machbarkeit. Haken „technisches Gespräch erforderlich“, wenn vorher mit dem Kunden gesprochen werden muss.
4. **Entscheidung je Artikel**: anbieten · nicht anbieten (mit Begründung) · anderer Standort · Sonstiges.
   Erst danach lässt sich kalkulieren. Die Anfrage springt in der Pipeline von „Neue Anfrage“ auf „Qualifiziert“.
5. **Kalkulieren** (Reiter 2): Standort, Maschine, Material, Zyklus, Personal, Zukaufteile, Werkzeug.
   Jede Speicherung ist eine neue **Version**.
6. **Freigabe**, falls nötig (Vier-Augen-Prinzip): Großprojekt ab 250.000 € Umsatz oder Invest, Marge zu niedrig oder
   **Artikelanalyse unvollständig**.
7. **Angebot erstellen** – in der Anfrage: ein Angebot mit allen angebotenen Artikeln (Pos. 1 Artikel, 1.1 Werkzeug,
   1.2 Sonstiges, 1.3 CO₂ …). Drucken / PDF, per E-Mail senden, Status **versendet** setzen.
8. **Angebotsverfolgung** – startet automatisch: Rücksprache mit dem Kunden spätestens nach 5 Arbeitstagen,
   Ampel grün/gelb/rot. „Rücksprache erfassen“: erreicht · niemanden erreicht (kommt am nächsten Arbeitstag wieder) ·
   wieder melden am …
9. **Verhandlung / technisches Gespräch** (Endrunde) per Pipeline, dann **Gewonnen** oder **Verloren** (Grund Pflicht).
   Änderungen nach dem Versand erzeugen eine **Revision** des Angebots (A26-0001-R1).
10. **Nachkalkulation** nach Serienstart mit Ampel.

## 2. Menü

| Menüpunkt | Wofür |
|---|---|
| Dashboard | Kennzahlen, Angebotsverfolgung mit Ampel (für alle sichtbar), Anfragen in Bearbeitung, Großprojekte, Auslastung |
| **Vertrieb** · Anfragen | Alle Anfragen und Leads – Einstieg in die tägliche Arbeit |
| Pipeline | Eine Karte je Anfrage nach Phase (Board oder Liste) |
| Kalkulationen | Alle Artikel-Kalkulationen über alle Anfragen |
| Angebote | Alle Angebote mit Status, Verfolgungsampel und letzter Rückmeldung |
| Aktivitäten | Aufgaben, Anrufe, Termine, Wiedervorlagen – auch mit Angebot verknüpft |
| Preisliste | Lebende VK-Preisliste je Kunde, Materialpreisänderungen mit Kennzeichnung, Import |
| **Kunden** · Firmen, Kontakte | Kunden, Interessenten, Lieferanten und Ansprechpartner |
| **Planung & Analyse** · Auslastung | Maschinenstunden der kommenden Jahre gegen die Kapazität |
| Auswertungen | Berichte nach Kunde, Maschinengröße, Verlustgründen, Vertrieb … |
| Beschaffung | Anfragen an Werkzeugmacher und Lieferanten, Angebotsvergleich |
| **System** · Stammdaten | Maschinen, Standorte, Materialien, Zukaufteile, Parameter, Vorlagen |
| Änderungswünsche | Testrückmeldungen und Wünsche ans Programm mit Prüfprotokoll |
| Dokumentation | Diese Beschreibung und das Lastenheft, Download als Word |
| Protokoll | Systemprotokoll: wer hat wann welche Daten geändert (Admin/Freigabe/Gesellschafter) |

## 2a. Pipeline-Phasen

| Phase | Bedeutung | Wie kommt die Karte hierhin? |
|---|---|---|
| Lead | Potenzial ohne konkrete Anfrage | von Hand („+ Lead“) |
| Neue Anfrage | Artikel da, noch nicht entschieden | automatisch |
| Qualifiziert | mind. ein Artikel zum Anbieten freigegeben | automatisch nach Entscheidung |
| Angebot | Angebot versendet | automatisch beim Status „versendet“ |
| Verhandlung / techn. Gespräch | Endrunde | von Hand (wird für die Auswertung gemerkt) |
| Gewonnen | Auftrag erhalten | von Hand oder Angebot „angenommen“ |
| Verloren | mit Pflichtgrund | von Hand (Dialog) oder Angebot „abgelehnt“ |
| Nicht angeboten | wir haben abgelehnt | Entscheidung „nicht anbieten“ für alle Artikel oder von Hand |

Die **Wahrscheinlichkeit** gilt für den ganzen Auftrag. Summen werden nicht mehr damit gewichtet.

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
- Es gibt **ein** Angebot je Anfrage mit allen angebotenen Artikeln. „Angebot erstellen / aktualisieren“ in der Anfrage
  (oder in der Kalkulation) aktualisiert einen Entwurf; ein bereits versendetes Angebot bekommt eine **Revision**.
- Positionen: 1 Artikel (mit Preisen je Lieferjahr: Jahresmenge × Stückpreis), 1.1 Werkzeug, 1.x Vorserie, 1.x Sonstiges,
  zuletzt CO₂-Fußabdruck (nur Information), dann 2 nächster Artikel. Positionsnummern sind änderbar.
- Status **versendet** startet die Angebotsverfolgung; **abgelehnt** fragt den Verlustgrund ab; **angenommen** setzt
  die Anfrage auf gewonnen.
- Mehrere Artikel desselben Kunden aus der Kalkulationsliste: anhaken → „Sammelangebot“ (führt sie in einer Anfrage zusammen).
- Angebote gehen nur an Kunden, Interessenten oder Partner – nie an Lieferanten.

### 3.5 Verloren / Kein Angebot
- Verloren nur mit Grund: Werkzeug zu teuer, Preis zu teuer, Projekt eingestellt, Kunde hat Projekt nicht erhalten,
  Vorrichtung zu teuer, Investition zu teuer, Lieferzeit/Kapazität, technisch nicht machbar oder Sonstiges (Freitext).
- In der Pipeline öffnet das Ziehen auf „Verloren“ automatisch diesen Dialog.

## 3a. Preisliste

- **Artikel**: alle Verkaufsartikel je Kunde mit Preis je Preiseinheit, Material(ien) mit Gewicht und **Preisbasis**
  (der Materialpreis, der im Preis steckt), Zukaufteilen, Planmenge, Preisbindung und Vertrag. Filter nach Kunde,
  Material, Preisbindung; Export nach Excel. Aus der Firmenseite mit „Preisliste“ direkt gefiltert.
- **Neuer Materialpreis** (Reiter *Materialpreise* → „Neuer Preis“): Preis eingeben – sofort erscheinen alle betroffenen
  Artikel mit Erhöhung je 100 Stk, neuem Preis und Jahreseffekt. „Übernehmen“ legt einen Vorgang an.
- **Kennzeichnen** im Vorgang: an Kunden weitergegeben (neuer oder vereinbarter Preis wird übernommen) · nicht
  weitergegeben, weil vertraglich gebunden · Sonstiges (Freitext). Mehrere Artikel auf einmal über Häkchen.
- Nicht weitergegebene Erhöhungen bleiben am Artikel als **offene Materialdifferenz** sichtbar.
- **Monatlich**: *Import Materialpreise* (Material-Nr., Preis €/kg) und/oder *Import Preisliste* (VK-Preise aus dem ERP
  oder die Excel-Vorlage „Annual Price Inquiry List“). Erst Vorschau, dann Übernehmen; geänderte Preise landen mit
  Historie in einem Vorgang zur Kennzeichnung.
- Rechnung: Δ je 100 Stk = (neu − Basis €/kg) × Gewicht g / 1000 × 100 × 1,08 (MGK 8 %).

## 3a. Freigaben, rote Markierungen und Wahrscheinlichkeit

- **Freigabe (Vier-Augen-Prinzip)** nur noch, wenn der Jahresumsatz ≥ 500.000 € oder das Invest ≥ 350.000 € ist.
  In der Freigabeleiste wählst du, **an wen** sie geht. Die Person bekommt eine Benachrichtigung, eine Aufgabe
  „Freigabe prüfen“ und sieht sie auf ihrer Startseite unter „Freigaben für mich“. Die Leiste zeigt, bei wem sie liegt.
- **Rot markiert** wird, was noch fehlt – Entscheidung, Artikelanalyse, Marge unter Grenze. Das sperrt nichts; nur zum
  Angebot muss jeder Artikel entschieden sein.
- **Artikelanalyse:** Ohne CAD-Wert wird die projizierte Fläche aus Länge × Breite geschätzt (Formel steht darunter).
  Vollständig ist sie, wenn alle Prüfpunkte bewertet sind und die Machbarkeit gewählt ist – die Liste zeigt ✓/✗.
- **Wahrscheinlichkeit** schätzt du je Anfrage selbst ein (oben in der Anfrage). Das Volumen wird nicht gewichtet:
  In der Anfragenliste stehen die Summen je Klasse (≥ 75 %, 50–74 %, < 50 %, nicht eingeschätzt) – ein Klick filtert.
- **Änderungswünsche:** „✓ i. O.“ oder „✗ n. i. O.“ (mit Beschreibung) direkt in der Liste; neue Wünsche gibt der Administrator frei.

## 3b. Monatsbericht für die Gesellschafter

- Menü **Monatsbericht**: Monat wählen, der Bericht entsteht aus den aktuellen Daten (Live-Stand).
- Kernzahl ist der **Neuumsatz**: Umsatz des stärksten Lieferjahres jedes gewonnenen Artikels (0,5 / 1,0 / 1,5 Mio. € →
  1,5 Mio. €), seit 1.1. aufsummiert und gegen das Jahresziel gestellt – mit %, Soll zum Monatsende und Ampel.
- Dazu: gewonnen im Monat und seit Jahresbeginn, verloren / nicht angeboten mit Gründen, offene Pipeline, was fehlt
  (überfällige Nachfassungen, fehlende Entscheidungen, Freigaben), Auslastung im Folgejahr je Maschine, Preisliste.
- Kommentar schreiben → **Stand speichern** (Zahlen werden eingefroren) → **Freigeben** → **Drucken / PDF** und selbst versenden.
- **Vertriebsziele** (Administrator): je Jahr Ziel gesamt und je Vertriebler, optional Werkzeug/Einmal.
- Die Startseite zeigt die Zielerreichung als Kachel.

## 3c. Auftrag erhalten – auch nur für einen Teil der Artikel

- Im versendeten Angebot **„Auftrag erhalten …“** (oder Status auf „angenommen“ setzen und speichern).
- Beauftragte Artikel anhaken, z. B. 2 von 10. Für den Rest einmal die Vorgabe wählen: **verloren** (mit Grund),
  **andere Variante beauftragt** (zählt nicht als Verlust) oder **noch offen** (bleibt in der Pipeline). Einzelne
  Artikel lassen sich abweichend setzen.
- Das Angebot wird „angenommen“ (alle beauftragt) oder **„teilweise beauftragt“**. Nur die beauftragten Artikel zählen
  als Neuumsatz und in der Auslastung. Offene Artikel später über „Auftrag ergänzen …“ entscheiden.

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
- Neue Wünsche mit „+ Änderungswunsch“ erfassen; sie bekommen automatisch eine Nummer WUN-0001 … und eine Bestätigung
  erscheint. Art und Bereich können aus der Liste gewählt oder frei eingegeben werden.
- Export als CSV für Excel.

## 7. Nummern
| Vorgang | Format | Beispiel |
|---|---|---|
| Anfrage / Lead | AF + Jahr + laufende Nr. | AF26-0001 |
| Kalkulation (Artikel) | K + Jahr + laufende Nr. | K26-0001 |
| Angebot | A + Jahr + laufende Nr., Revision -R | A26-0001, A26-0001-R1 |
| Beschaffung | B + Jahr + laufende Nr. | B26-0001 |
| Preisänderung (Preisliste) | PA + Jahr + laufende Nr. | PA26-0001 |
| Änderungswunsch | REV01-… oder WUN- | REV01-B01, WUN-0001 |

Ältere Nummern (KA-2026-…, AN-2026-…) bleiben unverändert erhalten.

## 8. Rollen
- **Administrator**: alles, inkl. Benutzer, Parameter, Firma & Layout, Löschen (Vier Augen bei Maschinen).
- **Vertrieb**: anlegen, kalkulieren, Angebote; Stammdaten lesen.
- **Gesellschafter**: alles sehen, nichts ändern.
- Zusatzrecht „darf freigeben“ für Freigaben im Vier-Augen-Prinzip.

---
© SB/Thinkworks
