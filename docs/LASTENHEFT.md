# Lastenheft KlarCRM

| | |
|---|---|
| **Projekt** | KlarCRM – schlankes CRM mit Spritzguss-Kalkulation |
| **Auftraggeber** | Friedrichs & Rath (F&R), Geschäftsführung |
| **Dokumentversion** | 1.22 |
| **Stand** | 15.11.2026 |
| **Status** | Testphase (GitHub Codespaces); Zielbetrieb: interner Server F&R |

> Dieses Lastenheft wird bei **jeder** Änderung am System mitgezogen. Neue Anforderungen, geänderte Regeln und
> umgesetzte Punkte werden in der Änderungshistorie (Kapitel 12) dokumentiert. Anforderungen tragen eine feste ID
> (z. B. `KAL-12`), damit Änderungen nachvollziehbar bleiben.

---

## 1. Ausgangslage und Ziel

F&R benötigt ein CRM für Vertrieb und Gesellschafter, das in der Funktion an Salesforce angelehnt, aber deutlich
einfacher und ohne Lizenzkosten pro Nutzer ist. Zusätzlich soll die **Angebotskalkulation für Spritzgussteile**
im selben System erfolgen, damit

- jede Anfrage mit Kalkulationsnummer, Versionen und Status transparent nachverfolgt wird,
- die kalkulierten Preise direkt in die Umsatz- und Pipeline-Übersicht einfließen,
- Verlustgründe systematisch ausgewertet werden können und
- jede gewonnene Kalkulation einer **Nachkalkulation** mit Ampel unterzogen wird.

**Leitprinzip:** maximale Transparenz – jeder Wert ist sichtbar, nachvollziehbar und überschreibbar; Abweichungen
von Standardwerten werden markiert; jede Änderung an einer Kalkulation erzeugt eine neue Version.

## 2. Nutzer und Rollen

| ID | Rolle | Rechte |
|---|---|---|
| ROL-1 | Administrator | Alles inkl. Benutzerverwaltung und Kalkulations-Parameter (Standardsätze); darf freigeben und löschen |
| ROL-2 | Vertrieb | Alle Daten sehen, anlegen, ändern, löschen; Stammdaten Maschinen/Materialien pflegen |
| ROL-3 | Gesellschafter | Alles sehen (Dashboard, Pipeline, Kalkulationen, Nachkalkulation), **nichts ändern** |

- ROL-6: Zusatzrecht **„darf Kalkulationen freigeben“** je Benutzer (z. B. Geschäftsführung, Vertriebsleitung).
- ROL-4: Rechte werden serverseitig erzwungen (HTTP 403), nicht nur in der Oberfläche.
- ROL-5: Auslegung für bis zu ca. 12 gleichzeitige Nutzer.

## 3. Systemübersicht

| Modul | Kurzbeschreibung |
|---|---|
| Dashboard | Vertriebs-KPIs, Forecast, Kalkulations-KPIs, Vergleich der Mitarbeiter |
| Firmen / Kontakte | Kunden, Interessenten, Partner, Lieferanten und Ansprechpartner |
| Pipeline | Verkaufschancen (Projekte) als Kanban-Board und Liste |
| Aktivitäten | Anrufe, Termine, E-Mails, Aufgaben, Notizen mit Fälligkeit |
| **Kalkulation** | Anfragen, Kalkulationsschema Spritzguss, Staffelpreise, Versionen, Artikelanalyse/Machbarkeit, Nachkalkulation |
| **Auslastung** | Maschinenauslastung der kommenden Jahre aus Bestand und Kalkulationen |
| **Stammdaten** | Maschinen, Materialien, Kalkulations-Parameter |
| Angebote | Angebote mit Positionen, Druck/PDF, Erzeugung aus Kalkulation |
| Benutzer | Konten, Rollen, Passwörter |
| Fußzeile | Copyright-Hinweis „© SB/Thinkworks“ auf allen Seiten |

## 4. CRM-Grundfunktionen (umgesetzt in v1.0)

- CRM-1: Firmen mit Typ (Interessent/Kunde/Partner/Lieferant), Adresse, Branche, Verantwortlichem, Notizen.
- CRM-2: Firmen-Detailseite mit Kontakten, Verkaufschancen, **Kalkulationen**, Angeboten und Aktivitätsverlauf.
- CRM-3: Kontakte mit Anrede, Position, Telefon, E-Mail, Zuordnung zur Firma.
- CRM-4: Verkaufschancen mit Phasen Lead → Qualifiziert → Angebot → Verhandlung → Gewonnen/Verloren; Wahrscheinlichkeit
  je Phase automatisch (überschreibbar); Abschlussdatum wird beim Gewinnen/Verlieren gesetzt.
- CRM-5: Pipeline als Kanban mit Drag & Drop und als Liste; Summen und gewichtete Summen je Phase.
- CRM-6: Aktivitäten mit Fälligkeit; Filter überfällig/heute/7 Tage; Abhaken in der Liste.
- CRM-7: Angebote mit automatischer Nummer (AN-JJJJ-NNNN), Positionen, Rabatt, MwSt., Duplizieren, Druckansicht (PDF).
- CRM-8: Dashboard mit offener Pipeline, Quartals-Forecast, gewonnenem Umsatz, Gewinnquote, Umsatz je Monat,
  Pipeline je Phase, Vergleich je Vertriebsmitarbeiter, anstehenden Abschlüssen; filterbar je Mitarbeiter.

## 5. Stammdaten für die Kalkulation

### 5.1 Maschinen
- STM-1: Je Maschine: Nummer, Bezeichnung, Schließkraft, Standort, **Maschinenstundensatz €/h (ohne Personal)**,
  **Instandhaltung €/h**, **Standard-Produktivität %**, **Standard-Anteil Bediener %** (intern als Faktor gespeichert, 30 % = 0,3), **Standard-Anteil Handling %** und **Automatisierung %**, aktiv/inaktiv.
- STM-2: Bei Auswahl einer Maschine in der Kalkulation werden Stundensatz, Instandhaltung, Produktivität und
  Bedienfaktor sofort übernommen und der Preis neu berechnet.
- STM-13: Je Maschine zusätzlich: **verfügbare Stunden/Jahr** (Schichtmodell, Standard 6.000 h), **Grundauslastung
  aus Bestandsaufträgen %** und **Auslauf des Bestands % je Jahr** – Basis der Auslastungsvorschau (Kap. 6.7).
- STM-14: CO₂-Stammdaten: je Material **Emissionsfaktor kg CO₂e/kg** (Cradle-to-Gate, Ziel: Lieferanten-PCF);
  je Maschine **Leistungsaufnahme kW inkl. Peripherie** und optional **Strom-Emissionsfaktor des Standorts**
  (z. B. Werk Krupka); Parameter: Strom-Emissionsfaktor (Standard 0,30 kg CO₂e/kWh), Werksemissionen Scope 1 je
  Maschinenstunde, Masterbatch, Lkw-Transport (Standard 0,10 kg CO₂e/tkm). Alle Standardwerte sind Richtwerte. CO₂ der Verpackung nur, wenn Teile je VE angegeben sind.
- STM-15: **Herleitung Maschinenstundensatz** je Maschine aus Wiederbeschaffungswert, Nutzungsdauer, kalk. Zins,
  Platzbedarf × Raumkosten, Leistungsaufnahme × Strompreis, sonstigen Fixkosten und **Umlage Kostenstelle**
  (Meister, Logistik, Peripherie …) je verfügbare Stunde; Instandhaltung €/h = Instandhaltungskosten p. a. / Stunden.
  Übersicht hergeleitet vs. aktuell mit Abweichung; Übernahme durch Administrator (wirkt auf neue Kalkulationen).
  Umlagen nur hier oder über FGK – nicht doppelt.
- STM-16: **Rohstoffpreis-Historie**: jede Preisänderung eines Materials wird mit Datum und Benutzer automatisch
  protokolliert; je Material Bezugsindex und „Preis gültig ab“.
- STM-17: **Preisgleitung**: je Material alle offenen/gewonnenen Kalkulationen (Haupt- oder weitere Komponente) mit
  Preisbasis der Version vs. aktuellem Preis, Δ Material %, €/Stk alt → neu, Wirkung p. a.; Markierung über Schwelle;
  „Neue Versionen anlegen“ erzeugt je Kalkulation eine Version mit aktuellem Preis und automatischer Änderungsnotiz.
- STM-3: Inaktive Maschinen sind in neuen Kalkulationen nicht auswählbar; bestehende Kalkulationen bleiben unverändert.
- STM-18: **Maschinenart** je Anlage: Spritzgießmaschine, Montagelinie/Montageplatz, Nachbearbeitung (Schweißen,
  Drucken, Entgraten …), Prüfstation, sonstige Anlage. Alle Arten haben dieselben Kostenfelder (Stundensatz,
  Instandhaltung, Produktivität, Bedienfaktor, kW, verfügbare Stunden, Grundauslastung) und erscheinen in der Auslastung.
  Als Hauptmaschine der Kalkulation werden nur Spritzgießmaschinen angeboten; alle Arten sind als Arbeitsgang wählbar.

### 5.2 Materialien
- STM-4: Je Material: Bezeichnung, Werkstoffgruppe, Lieferant, **Preis €/kg**, Dichte, aktiv/inaktiv.
- STM-5: Bei Auswahl wird der Materialpreis übernommen (überschreibbar).

### 5.2a Zukaufteile
- STM-19: Je Zukaufteil: interne Artikel-Nr., Bezeichnung, Lieferant, Lieferanten-Artikel-Nr., **Preis je
  Preiseinheit** (1 oder 1.000 Stück), Mengeneinheit, Mindestbestellmenge, Wiederbeschaffungszeit (Tage),
  **CO₂ kg CO₂e je Einheit**, Preis gültig ab, Notizen, aktiv/inaktiv.
- STM-20: Bei Auswahl in der Kalkulation werden Preis je Einheit (= Preis ÷ Preiseinheit) und CO₂-Wert übernommen
  und sind überschreibbar; die Werte werden mit der Version gespeichert (spätere Preisänderungen ändern keine
  gespeicherte Version).

### 5.3 Parameter (Standardwerte)
- STM-21: Zukaufteile: eigener MGK-Satz (Standard leer = wie MGK); Nebenkalkulation MGK 3 %, Qualität 1 %,
  Ausschuss 1 %, Aufschlag 0 % (Richtwerte, änderbar).
- STM-6: Lohnsätze Bediener, Einrichter, Montage, **Handling**, **Automatisierung** (€/h; Richtwerte 34 €/h und 55 €/h, änderbar).
- STM-7: Zuschläge MGK, FGK, Ausschuss, Verwaltung, Vertrieb, Projektmanagement, **Qualität**, **Werkzeugbau** (%).
- STM-8: Gewinn (Standard **7 %**), Skonto, Rabatt.
- STM-9: Fertigungs-Standards: Produktivität, Montage-Produktivität, Rüstzeit, Einrichter je Rüstvorgang, Anfahrausschuss.
- STM-10: Ampel-Schwellen der Nachkalkulation (Standard grün bis +3 %, rot ab +10 %).
- STM-12: Schwellen für **Großprojekte**: Jahresumsatz ab 500.000 € und Invest ab 500.000 € (Standard, änderbar).
- STM-11: Nur Administratoren ändern Parameter. Änderungen wirken auf **neue** Kalkulationen; gespeicherte Versionen
  enthalten ihre Werte selbst und bleiben reproduzierbar.

## 6. Kalkulation (Anfrage → Kalkulation → Angebot → Auftrag)

### 6.1 Kopfdaten einer Kalkulation
- KAL-1: Automatische **Kalkulationsnummer** KA-JJJJ-NNNN.
- KAL-2: Artikelbezeichnung, **Artikelnummer des Kunden**, eigene Artikelnummer.
- KAL-3: Kunde, **Ansprechpartner des Kunden**, verknüpfte Verkaufschance (Projekt), Verantwortlicher.
- KAL-4: Status: Anfrage, In Kalkulation, Angeboten, Verhandlung, Gewonnen, Verloren, **Kein Angebot abgegeben**,
  Zurückgestellt.
- KAL-4a: **Kein Angebot abgegeben** mit Grund: Mengen zu klein · Artikel zu klein · Artikel zu groß ·
  Keine Maschine/Kapazität · Nicht herstellbar · Technologie passt nicht · Termin nicht machbar · Sonstiges –
  plus **Freitext** zur Erläuterung. Wahrscheinlichkeit 0 %; verknüpfte Verkaufschance wird als verloren mit
  „Kein Angebot: <Grund>“ geschlossen.
- KAL-4b: **Machbarkeit** je Kalkulation: Herstellbar · Bedingt herstellbar · Anpassungen erforderlich ·
  Nicht herstellbar, mit Anmerkung (z. B. erforderliche Anpassungen).
- KAL-5: **Wahrscheinlichkeit** des Auftrags in % – beim Statuswechsel vorgeschlagen, frei änderbar.
- KAL-6: **Verlustgrund** (bei Status Verloren):
  Artikelpreis zu hoch · Werkzeug zu teuer · Investition zu teuer · Kunde hat Projekt nicht gewonnen ·
  Projekt beim Kunden eingestellt · Lieferzeit/Kapazität · Technisch nicht machbar · Sonstiges.
- KAL-7: Bemerkungsfeld, Anfragedatum, Angebotsabgabe bis, Serienstart (SOP).
- KAL-8: **Zuletzt angerufen** inkl. **Ergebnis** des letzten Anrufs – sichtbar in der Kalkulationsliste (Datum,
  Ergebnis, Gesprächsnotiz) und im Kopf jeder Kalkulation. In der Liste rot markiert, wenn eine offene Anfrage
  > 14 Tage nicht angerufen wurde.
- KAL-9: **Anrufhistorie** je Kalkulation (eigener Reiter „Anrufe“): Datum/Uhrzeit, Gesprächspartner, **Ergebnis**,
  Gesprächsnotiz/Resultat, Wiedervorlage, Benutzer. Ein Klick auf das Datum „zuletzt angerufen“ in der Liste öffnet die
  Historie direkt – so ist z. B. sichtbar, was der Anruf vom 10.10. ergeben hat.
  Ergebnisse: Nicht erreicht · Rückruf vereinbart · Kunde entscheidet noch · Preis nachverhandeln ·
  Neu kalkulieren/Änderung · Auftrag in Aussicht · Auftrag erhalten · Absage · Sonstiges.
- KAL-10: Jeder dokumentierte Anruf legt eine erledigte Aktivität „Anruf“ beim Kunden an; ist eine Wiedervorlage
  gesetzt, zusätzlich eine offene Aufgabe für den Verantwortlichen zu diesem Datum.

### 6.2 Kalkulationsschema (Zuschlagskalkulation)
Alle Eingaben sind überschreibbar. Abweichungen vom Standardwert (Maschine, Material, Parameter) werden gelb markiert
und lassen sich per Klick auf den Standard zurücksetzen (KAL-20).

**Eingaben**

| Bereich | Felder |
|---|---|
| Mengen | Jahresmenge, Losgröße, Projektlaufzeit (Jahre) |
| Material | Material (Stammdaten), Preis €/kg, Teilgewicht g, Anguss je Schuss g, Mahlgut-Rückführung %, Masterbatch-Anteil % und -Preis, **Zukaufteile-Liste** (1 … N Teile aus Stammdaten mit Menge je Artikel, € und CO₂ je Einheit) plus Zukaufteile pauschal €/Stk; **weitere Komponenten (2K/3K …)** je mit Material, €/kg, Teilgewicht, Anguss, Mahlgut, CO₂-Faktor |
| Maschine & Fertigung | Maschine (Stammdaten), Maschinenstundensatz €/h, Instandhaltung €/h, **Zykluszeit s**, **Fachzahl**, **Produktivität %**; **Personal an der Maschine in % je Maschine** mit Schnellwahl und freiem Satz: Bediener (10/20/30/50/100/120 % oder individuell, bis 300 %), Handling (0 … 100 %), Automatisierung (0 … 100 %), je Rolle eigener Lohnsatz; **Familienwerkzeug**: Werkzeuggruppe und Anteil dieses Artikels an Maschinenzeit/Rüsten % |
| Rüsten | Rüstzeit je Los h (Maschinenstillstand), Anfahrausschuss je Los Stk, Einrichter (Personen), **Einrichter-Zeit je Rüstvorgang min** (leer = gesamte Rüstzeit), Lohnsatz Einrichter, **Automatisierer-Zeit je Rüstvorgang min**, Lohnsatz Automatisierung |
| Montage & weitere Arbeitsgänge | Handmontage je Stück s, Personen, Lohnsatz, Produktivität Montage %; **weitere Arbeitsgänge 1 … N** je mit Anlage (Stammdaten), Bezeichnung, Taktzeit s, Teile je Takt, Stundensatz Anlage, Instandhaltung, Personen, Lohnsatz, Produktivität %, Rüstzeit je Los, kW |
| Zuschläge | MGK, FGK, Ausschuss, Verwaltung, Vertrieb, Projektmanagement, **Qualität**, **Werkzeugbau**, Gewinn, Skonto, Rabatt (%); für Qualität und Werkzeugbau ist die **Basis wählbar**: FEK oder HK |
| **Verpackung** | Auswahl **pauschal in % auf HK** (wenn Details unbekannt; Standard aus Parametern) **oder detailliert**: Verpackungsart (Vorschläge KLT, Karton, Gitterbox, Sonderladungsträger …), Teile je Verpackungseinheit (VE), Kosten je VE bzw. bei Mehrweg je Umlauf (Reinigung, Miete), Packzeit je VE, VE je Palette |
| **Transport** | Lieferbedingung (Incoterm, frei wählbar), Art: keine (ab Werk) · € je Palette · € je Lieferung (mit Lieferungen p. a.) · **pauschal in % auf Herstellkosten** (Standard aus Parametern) |
| Zusatzpositionen | frei: Bezeichnung, Betrag, Bezug (je Stück / je 1.000 / je Los / je Jahr), Art (Fertigung oder Vertrieb) – z. B. Peripherie, Nacharbeit, Bedrucken, Sonderkosten |
| Einmalkosten | frei: Bezeichnung, Kosten, Preis an Kunde – z. B. Werkzeug, Erstbemusterung, Prüfmittel; je Position wählbar **„auf Stückpreis umlegen“** (Amortisation) mit Stückzahl (Standard Jahresmenge × Laufzeit) |
| Verkaufspreis | optional manuell festgelegt (Gewinn ergibt sich dann als Rest) |

**Rechenweg je Stück** (KAL-21)

| Schritt | Formel |
|---|---|
| Ausbringung | Stück/h = 3600 / Zykluszeit × Fachzahl × Produktivität |
| Material (MEK) | (Teilgewicht + Anguss/Fachzahl × (1 − Mahlgut %)) / 1000 × Mischpreis €/kg + Σ weitere Komponenten (gleiche Formel je Komponente) + Zukaufteile; Mischpreis = Materialpreis × (1 − MB %) + MB-Preis × MB %; Zukaufteile = Σ (Menge × € je Einheit) der Liste + Pauschale |
| MGK | MEK × MGK % |
| Maschine | Maschinenstundensatz / Stück/h × Familienanteil (Instandhaltung, Personal, Rüsten ebenso) |
| Instandhaltung | Instandhaltung €/h / Stück/h |
| Personal | je Rolle eigene Zeile: Bediener = Lohnsatz Bediener × Anteil % / Stück/h; Handling = Lohnsatz Handling × Anteil % / Stück/h; Automatisierung = Lohnsatz Automatisierung × Anteil % / Stück/h |
| Rüsten | [Rüstzeit × (Maschinensatz + Instandhaltung) + Einrichter-Zeit × Lohnsatz Einrichter × Einrichter + Automatisierer-Zeit × Lohnsatz Automatisierung + Anfahrausschuss × (Material + Maschine + Instandhaltung + Personal je Stück)] / Losgröße; Ausweis je Los aufgeteilt nach Maschinenstillstand, Einrichter, Automatisierung, Anfahrausschuss |
| Montage | Montagezeit/3600 × Lohnsatz × Personen / Produktivität Montage |
| Arbeitsgang n | Lauf: (Satz Anlage + Instandhaltung + Lohnsatz × Personen) / Stück je h, Stück je h = 3600 / Takt × Teile je Takt × Produktivität; Rüsten: Rüstzeit × (Satz Anlage + Instandhaltung + Lohnsatz × 1 Einrichter) / Losgröße |
| MGK Zukaufteile (optional) | Zukaufteile (ohne Nebenkalkulation) × eigener MGK-Satz; sonst gemeinsam mit Material × MGK % |
| Zukaufteile Nebenkalkulation (optional) | siehe KAL-28j; wird zu den Selbstkosten addiert; Gewinn % nur auf die Selbstkosten der Hauptkalkulation |
| Jahresabschläge (optional) | manueller Anlaufpreis: Jahr 1 = eingegebener Preis, Jahr y ≥ 2 = Serienpreis × k × Faktor y (k siehe KAL-28k); sonst Faktor Jahr 1 = 1; Jahr y = 1 − Abschlag y % (Bezug Jahr 1) bzw. Vorjahresfaktor × (1 − Abschlag y %) (Bezug Vorjahr); vorab eingerechnet: Preis Jahr y = Preisanteil × n / Σ Faktoren × Faktor y – getrennt für Hauptanteil und Zukaufteile-Nebenkalkulation |
| Grenzkosten (KAL-28m) | [Material + Zukauf + (Personal + Instandhaltung) + kW × (1/Stück je h + Rüstzeit/Los) × €/kWh + (Einrichter- + Automatisierer-Kosten je Los)/Los + Anfahrteile/Los × (Material + Personal + Instandhaltung) + Montage + Σ Arbeitsgänge variabel] / (1 − Ausschuss) + Zukauf NK/(1 − Ausschuss NK) + Verpackung + Transport; DB = Preis − Grenzkosten |
| FEK | Maschine + Instandhaltung + Personal + Rüsten + Montage + Σ Arbeitsgänge |
| FGK | FEK × FGK % |
| Qualität / Werkzeugbau (Basis FEK) | FEK × Qualität % bzw. FEK × Werkzeugbau % – Teil der Herstellkosten (vor Ausschuss) |
| SEK Fertigung | Zusatzpositionen „Fertigung“ |
| HK vor Ausschuss | MEK + MGK + FEK + FGK + Qualität/Werkzeugbau (Basis FEK) + SEK Fertigung |
| Ausschuss | HK vor Ausschuss / (1 − Ausschuss %) − HK vor Ausschuss |
| Herstellkosten | HK vor Ausschuss + Ausschuss |
| Verwaltung / Vertrieb / PM | je HK × % |
| Qualität / Werkzeugbau (Basis HK) | HK × Qualität % bzw. HK × Werkzeugbau % |
| Verpackung | pauschal: HK × Verpackung % · detailliert: Kosten je VE / Teile je VE + Packzeit je VE / 3600 × Lohnsatz Bediener / Teile je VE |
| Transport | je Palette: Fracht je Palette / (Teile je VE × VE je Palette) · je Lieferung: Kosten je Lieferung × Lieferungen p. a. / Jahresmenge · Prozent: HK × % · ab Werk: 0 |
| SEK Vertrieb | Zusatzpositionen „Vertrieb“ |
| Selbstkosten | HK + Verwaltung + Vertrieb + PM + Qualität/Werkzeugbau (Basis HK) + Verpackung + Transport + SEK Vertrieb |
| Gewinn | SK × Gewinn % (bzw. Rest bei manuellem Preis) |
| Werkzeugamortisation | Σ Preise der umzulegenden Einmalkosten / Amortisationsstückzahl – **ohne Gewinnaufschlag** zum Preis addiert |
| Verkaufspreis | (SK + Gewinn + Werkzeugamortisation) / (1 − Skonto) / (1 − Rabatt) |

- KAL-28: **Staffelpreise**: bis zu 3 weitere Losgrößen je Kalkulation (Vorschlag ½×, 2×, 5× der Basis-Losgröße).
  Je Staffel: Rüstkosten je Stück, Preis je Stück und je 1.000, Δ % zum kalkulierten Preis der Basis-Losgröße.
  Staffeln werden immer kalkuliert (ein manuell festgelegter Preis gilt nur für die Basis-Losgröße). Staffelpreise
  werden in die Artikelposition des Angebots übernommen.
- KAL-29a: Pauschale Standardsätze in den Parametern: Verpackung 1,5 % und Transport 2,0 % auf HK (änderbar).
  Neue Kalkulationen starten mit Verpackung pauschal; Transport startet mit „ab Werk“, der %-Satz ist vorbelegt.
  Teile je VE und VE je Palette bleiben auch im Pauschalmodus optional (für Paletten, Lieferungen, CO₂).
- KAL-29: Ausgaben Verpackung/Transport: Kosten je Stück und p. a., VE p. a., Stück je Palette, Paletten p. a.
  Verpackungsart, Teile je VE und Lieferbedingung werden in die Artikelposition des Angebots übernommen.
  Ältere Versionen ohne diese Angaben rechnen unverändert (Verpackung bisher über Zusatzpositionen).
- KAL-28a: **Staffelpreise nach Jahresmenge** (bis zu 3): gleiche Abrufhäufigkeit, d. h. Lose pro Jahr bleiben
  gleich und die Losgröße wächst mit der Menge; Ausweis Losgröße, €/Stk, €/1.000, Umsatz p. a., Δ %; im Angebot.
- KAL-28g: **Weitere Arbeitsgänge (1 … N Anlagen)**: Montagelinie, Ultraschallschweißen, Tampondruck, Prüfstation
  u. a. je Artikel; Werte aus den Stammdaten vorbelegt und überschreibbar; je Arbeitsgang Ausweis €/Stk, Stück je h
  und Stunden p. a. sowie eigene Zeile „Arbeitsgang: …“ im Kalkulationsschema. FGK, Ausschuss und alle folgenden
  Zuschläge wirken wie bei der Spritzgießmaschine. Stunden fließen in die Auslastung der jeweiligen Anlage (AUS-6).
- KAL-28h: **Zukaufteile-Liste**: beliebig viele Zukaufteile je Artikel mit Menge; Zeile „Zukaufteile (n Pos.)“ im
  Schema, MGK wirkt darauf; CO₂ der Zukaufteile fließt in den Fußabdruck (Kap. 6.8).
- KAL-28i: **Eigener MGK-Satz für Zukaufteile** (optional; leer = MGK-Satz Material): eigene Zeile „MGK Zukaufteile x %“
  im Schema, Material behält seinen MGK-Satz. Standard in den Parametern (STM-21).
- KAL-28j: **Nebenkalkulation teurer Zukaufteile** (optional je Zukaufteil per Haken „Nebenkalk.“): Diese Teile
  laufen nicht durch die volle Kalkulation (kein MEK-Anteil, keine FGK, kein Ausschuss der Hauptkalkulation, keine
  VwGK/VtGK/PM, keine %-Verpackung/Transport, kein Gewinn-%), sondern nur durch eine kleine Nebenkalkulation:
  Einstand E = Σ Menge × € je Einheit; MGK = E × MGK-NK %; Qualität = E × Qualität-NK %;
  Ausschuss = (E + MGK + Qualität) / (1 − Ausschuss-NK %) − (E + MGK + Qualität);
  SK-NK = E + MGK + Qualität + Ausschuss (eigene Zeile „Zukaufteile Nebenkalkulation“ vor den Selbstkosten);
  optionaler Aufschlag = SK-NK × Aufschlag-NK % (Standard 0 %, fließt in den Gewinn). Skonto/Rabatt wirken auf den
  Gesamtpreis. CO₂ der Teile wird unverändert im Fußabdruck berücksichtigt. Ausweis der Nebenkalkulation je Stück
  und p. a. in der Kalkulation.
- KAL-28k: **Serienpreis je Lieferjahr (Anlaufpreis & Jahresabschläge)**:
  - **Preis Jahr 1** wahlweise „= kalkulierter Serienpreis“ oder **„manuell (Anlaufpreis)“**; bei manuell gilt ab Jahr 2
    der kalkulierte Serienpreis × Faktor des Jahres (übliche Praxis bei F&R).
  - Tabelle je Lieferjahr (Anzahl = Projektlaufzeit, max. 15): Abschlag **entweder** als „% ggü. Vorjahr“ **oder** als
    „% vom Serienpreis“ (z. B. 100 / 98 / 96) eingeben – die andere Spalte rechnet mit (2 % ggü. Vorjahr ↔ 98 %).
    Gespeichert wird als % vom Serienpreis; ältere Versionen mit Bezug „Vorjahr“ rechnen unverändert und werden beim
    Bearbeiten umgestellt. Jahre ohne Eintrag bleiben auf dem Vorjahreswert. Abschläge typisch bis Jahr 3 … 5.
  - **Abschläge vorab draufschlagen** (Erwartung der Automobilkunden, damit kein Minusgeschäft entsteht), Standard an,
    in beiden Varianten von Jahr 1; der Serienpreis wird mit einem Faktor k angehoben:
    „Ø Laufzeit = Kalkulation“: k = Anzahl Jahre / Σ Faktoren (Durchschnitt der Jahre = kalkulierter Preis);
    „letztes Jahr ≥ Kalkulation“: k = 1 / kleinster Faktor (kein Jahr unter dem kalkulierten Preis); „nein“: k = 1.
    Bei manuellem Anlaufpreis gilt k für die Jahre 2 … n.
  - Je Jahr Ausweis der **Marge gegen die Selbstkosten**; Warnung „Minusgeschäft in Jahr …“, wenn ein Jahr unter den
    Selbstkosten liegt.
  - **Zukaufteile in der Nebenkalkulation** haben eigene Spalten (eigene Abschläge, z. B. 0 %).
  - Ausweis: €/Stk je Jahr in der Eingabetabelle und Ergebniskarte „Serienpreis je Lieferjahr“ mit Umsatz; im Angebot
    Preis Jahr 1 als Positionspreis und Preisentwicklung je Jahr im Positionstext.
- KAL-28l: **Vorserienpreis** für Kleinstmengen: Vorserienmenge, Losgröße (leer = eine Lieferung), optional eigene
  Rüstzeit, Produktivität und Ausschuss (leer = wie Serie) und Aufschlag %. Gerechnet wird die vollständige Kalkulation
  mit diesen Werten (Jahresmenge = Vorserienmenge, ohne Werkzeugamortisation, ohne Staffeln/Abschläge). Ausweis mit
  Δ % zur Serie; im Angebot als eigene Position „Vorserienpreis“ mit Menge und Preis je 1.000. Optional **fester
  Vorserienpreis (manuell)**: gilt dann im Angebot; kalkulierter Vorserienpreis, Selbstkosten und Marge bleiben als
  Orientierung sichtbar (Warnfarbe bei negativer Marge).
- KAL-28m: **Grenzkostenkalkulation (direkte Artikelkosten)** läuft in jeder Kalkulation mit – Überblick für
  Verhandlungen, nicht im Angebot. Enthalten: Material inkl. Komponenten, Zukaufteile (Nebenkalkulation zum
  Einstand inkl. deren Ausschuss), Personal an der Maschine (Bediener, Handling, Automatisierung), Instandhaltung,
  Energie (kWh je Stück × Strompreis, Maschine und Arbeitsgänge), Rüsten nur Personal (Einrichter, Automatisierer)
  plus Anfahrteile (Material + variable Fertigung), Handmontage, weitere Arbeitsgänge (Personal, Instandhaltung),
  Ausschuss (Satz der Kalkulation), Verpackung und Transport. Nicht enthalten: Maschinenstundensatz (Abschreibung,
  Zinsen, Raum, Umlage), MGK/FGK, Qualität/Werkzeugbau %, VwGK, VtGK, PM, Gewinn, Einmalkosten.
  Ausweis: Grenzkosten je Stück und je 1.000, Deckungsbeitrag je Stück (€ und %) und p. a., Aufteilung des Preises
  (Grenzkosten / Fix- und Gemeinkosten / Gewinn), Preisuntergrenze kurz- (Grenzkosten) und langfristig (Selbstkosten);
  DB p. a. auch je Lieferjahr. Neues Eingabefeld Strompreis €/kWh (Vorgabe aus Parametern).
- KAL-28b: **Mehrkomponenten**: Material, CO₂, Gewicht und Schussgewicht aller Komponenten; im Angebot „A + B (2K)“.
- KAL-28c: **Familienwerkzeug**: Maschinen-, Instandhaltungs-, Personal- und Rüstkosten, Maschinenstunden
  (Auslastung) und Energie-CO₂ anteilig; Summe der Anteile aller Artikel der Gruppe = 100 % (Hinweis).
- KAL-28d: **Werkzeugamortisation**: umgelegte Einmalkosten erscheinen nicht als Einmalumsatz, zählen aber zum
  Invest; Ausweis €/Stk, € je 1.000, Gesamtbetrag, Stückzahl; im Angebot „inkl. Werkzeugamortisation …“.
- KAL-28e: **Kopieren** einer Kalkulation (aktuelle Version → neue Kalkulation, Status Anfrage, Herkunft vermerkt)
  und **Vorlagen** („Als Vorlage speichern“; bei „Neue Anfrage“ auswählbar; Verwaltung unter Stammdaten).
- KAL-28f: **Preisgleitklausel** im Angebot: Materialbasis €/kg mit Stand und Index; Anpassung bei Änderung über
  der Schwelle (Parameter, Standard ± 5 %).
- KAL-27: Standard: Qualität 1,5 % auf HK, Werkzeugbau 2 % auf FEK (Parameter). Ältere Versionen ohne diese Werte
  rechnen unverändert mit 0 % weiter (Reproduzierbarkeit, KAL-31).

**Ausgaben**
- KAL-22: Jede Position je **Stück, je 100, je 1.000** und als Anteil am Preis in %.
- KAL-23: Kennzahlen: Verkaufspreis, Jahresumsatz, Gewinn p. a., Marge, Projektumsatz (× Laufzeit), Einmalumsatz,
  Umsatz 1. Jahr gesamt, Stück/h (theoretisch und real), Maschinenstunden p. a., Materialbedarf kg p. a.,
  Rüstkosten je Los, Lose p. a., Schussgewicht.
- KAL-24: Warnhinweise bei fehlender Ausbringung/Losgröße und wenn der Preis unter den Selbstkosten liegt.
- KAL-25: Die Berechnung erfolgt **live** beim Eingeben (Server-Rechenkern, eine Quelle der Wahrheit).
- KAL-26: Druckansicht der Kalkulation.

### 6.3 Versionen
- KAL-30: Jede gespeicherte Änderung erzeugt eine **neue Version** (V1, V2, …) mit Änderungsnotiz, Benutzer, Zeitpunkt.
- KAL-31: Versionen sind unveränderlich und enthalten alle Eingaben und Ergebnisse (reproduzierbar, auch wenn sich
  Stammdaten später ändern).
- KAL-32: Jede ältere Version kann als Basis geladen und als neue Version weiterbearbeitet werden.
- KAL-33: **Versionsvergleich** A/B: geänderte Eingaben und Auswirkung auf Preis, Selbstkosten, Marge, Stück/h,
  Umsatz, Gewinn, Einmalumsatz, Maschinenstunden (absolut und %).

### 6.3a Artikelanalyse / Machbarkeit (eigener Reiter)
- ANA-1: Eingaben: Werkstoffgruppe (PP, ABS, PC/ABS, PC, PA6, PA66, POM, PBT, TPE, sonstige), Länge/Breite/Höhe,
  projizierte Fläche je Kavität inkl. Anguss (cm²), Wandstärke min./max., längster Fließweg, Sicherheitsfaktor
  Schließkraft (Standard 1,2), Nebenzeit. Fachzahl, Zykluszeit und Maschine kommen aus der aktuellen Version.
- ANA-2: Werkstoffkennwerte als Richtwerte je Gruppe, einzeln überschreibbar: Werkzeuginnendruck, max. Verhältnis
  Fließweg/Wandstärke, Temperaturleitfähigkeit, Masse-, Werkzeug-, Entformungstemperatur.
- ANA-3: Berechnung (Richtwerte, ersetzen keine Füllsimulation):
  | Größe | Formel |
  |---|---|
  | Schließkraft t | Fläche cm² × Fachzahl × Innendruck bar / 1000 × Sicherheitsfaktor |
  | Fließweg/Wandstärke | längster Fließweg / min. Wandstärke, Vergleich mit Werkstoffgrenze |
  | Kühlzeit s | s² / (π² · a) · ln(8/π² · (T_Masse − T_Wkz) / (T_Entf − T_Wkz)), s = max. Wandstärke |
  | Zyklus-Richtwert s | Kühlzeit × 1,35 + Nebenzeit |
- ANA-4: **Passende Maschinen** (Schließkraft ≥ Bedarf), kleinste passende markiert; Hinweis, wenn gewählte Maschine zu
  klein oder deutlich überdimensioniert ist; Hinweis „keine Maschine vorhanden“, wenn Bedarf > größte Maschine.
- ANA-5: **Checkliste** (Bewertung offen/ok/kritisch/n. a. + Anmerkung): Zeichnung/3D-Daten, Entformungsschrägen,
  Hinterschnitte/Schieber, Einlegeteile, Toleranzen, Oberfläche/Sichtteil, Wandstärken, Anspritzpunkt/Werkzeugkonzept,
  Materialfreigabe/Normen, Montage/Nachbearbeitung, Prüfmittel, Verpackung/Logistik.
- ANA-6: **Machbarkeitsvorschlag**: nicht herstellbar (keine Maschine groß genug) → Anpassungen erforderlich
  (Fließweg kritisch, Maschine zu klein, Zykluszeit deutlich unter Richtwert, kritische Checklistenpunkte) →
  bedingt herstellbar (Hinweise oder offene Punkte) → herstellbar. Der Benutzer übernimmt oder wählt selbst (KAL-4b).

### 6.4 Übernahme in Umsatzübersicht und Angebot
- KAL-40: Kalkulation kann mit einer Verkaufschance verknüpft oder per Klick eine Verkaufschance anlegen.
- KAL-41: Bei aktivierter Synchronisation übernimmt die Verkaufschance automatisch: Volumen = Summe (Jahresumsatz +
  Einmalumsatz) aller verknüpften Kalkulationen; Wahrscheinlichkeit (bei einer Kalkulation direkt, bei mehreren
  umsatzgewichtet); Phase entsprechend Status; Verlustgrund als Text.
- KAL-42: **Angebot aus Kalkulation**: erzeugt ein Angebot mit Artikelposition (Jahresmenge × Stückpreis, Kunden-
  Artikelnummer, Material, Kalkulationsnummer/Version, Preis je 1.000) und je Einmalkosten-Position; Status der
  Kalkulation wechselt auf „Angeboten“.
- KAL-43: **Sammelangebot**: In der Kalkulationsliste lassen sich mehrere Artikel per Häkchen auswählen (auch über
  mehrere Seiten, „alle auf dieser Seite“). Eine Leiste zeigt Anzahl, Kunde, Umsatz p. a. und Invest der Auswahl.
  „Sammelangebot erstellen“ erzeugt **ein** Angebot mit allen Artikeln (aktuelle Version je Kalkulation):
  zuerst die Serienteile (je Artikel eine Position mit Jahresmenge × Stückpreis, Kunden-Art.-Nr., Material,
  Kalkulationsnummer/Version, Preis je 1.000, Staffelpreise), danach alle Einmalkosten mit Artikelbezug.
  Positionen nach Kalkulationsnummer sortiert.
- KAL-44: Regeln Sammelangebot: alle Artikel beim **selben Kunden** (sonst Hinweis, Schaltfläche gesperrt);
  verlorene und „kein Angebot“-Kalkulationen sind ausgeschlossen. Ansprechpartner aus der ersten Kalkulation;
  Verkaufschance nur, wenn alle Artikel zur selben Chance gehören. Status aller Artikel → „Angeboten“, verknüpfte
  Verkaufschancen werden aktualisiert.
- KAL-45: Schnellfilter „Nur <Kunde> anzeigen“ aus der Auswahl heraus, um weitere Artikel desselben Kunden zu ergänzen.
- KAL-46: **Herkunft**: Jedes aus Kalkulationen erzeugte Angebot speichert die beteiligten Kalkulationen und zeigt sie
  im Kopf (Kalkulationsnummern als Links); jede Kalkulation zeigt im Kopf, in welchen Angeboten sie enthalten ist
  (Kennzeichnung „Sammelangebot, n Artikel“).

### 6.5 Kalkulationsliste (Anfragenübersicht)
- KAL-50: Spalten: Kalk.-Nr. und Version, Artikel und eigene Art.-Nr., **Art.-Nr. Kunde**, Kunde und Ansprechpartner,
  Status und Verlustgrund, €/Stk, Menge p. a., Umsatz p. a. und Invest, Wahrscheinlichkeit und gewichteter
  Umsatz, **zuletzt angerufen**, Bemerkung, Ampel der letzten Nachkalkulation.
- KAL-51: Suche (Nummer, Artikel, Artikelnummern, Bemerkung), Filter Status und Verlustgrund, Sortierung je Spalte.
- KAL-52: Kennzahlen: offene Anfragen, nicht angerufene > 14 Tage, Potenzial (offen, gewichtet), offene
  Werkzeugumsätze, gewonnen, verloren, Trefferquote, Ampelverteilung.
- KAL-53: Auswertung **Verlustgründe** (verlorener Jahresumsatz und Anzahl je Grund).
- KAL-54: Kalkulations-KPIs auch im Dashboard (für Gesellschafter).
- KAL-59: Liste zeigt zusätzlich Machbarkeit und Grund „Kein Angebot“; Filter Machbarkeit (inkl. „nicht bewertet“)
  und Grund „Kein Angebot“; Auswertung „Kein Angebot abgegeben“ je Grund und Machbarkeitsübersicht offener Anfragen.
- KAL-55: **Großprojekte hervorheben**: Eine Kalkulation gilt als Großprojekt, wenn der Jahresumsatz ≥ Umsatz-Schwelle
  **oder** der Invest ≥ Invest-Schwelle ist (STM-12). Invest = Summe der Einmalkosten (Kosten) der aktuellen Version
  (Werkzeug, Bemusterung, Prüfmittel …).
- KAL-56: Darstellung: Kennzeichen „★ Großprojekt“ mit Begründung (Umsatz und/oder Invest), farbig hinterlegte Zeile
  bzw. Karte in Kalkulationsliste, Kalkulationskopf, Angebotsliste, Angebot, Pipeline-Board.
- KAL-57: Filter „nur Großprojekte“ in der Kalkulationsliste; Kennzahl „Großprojekte offen“ (Anzahl, Umsatz p. a.,
  Invest) in Kalkulationsliste und Dashboard.
- KAL-58: Angebote: Invest = Positionen mit Einheit „psch“ (Einmalkosten), Serienumsatz = Netto − Invest.
  Pipeline: Volumen der Verkaufschance ≥ Umsatz-Schwelle.

### 6.7 Auslastung kommende Jahre
- AUS-1: Matrix Maschine × Jahr (3, 5, 7 oder 10 Jahre) mit Auslastung in % der verfügbaren Stunden.
- AUS-2: Bestandteile je Zelle: **Bestand** (verfügbare h × Grundauslastung % × (1 − Auslauf %)^Jahr), **fest**
  (gewonnene Kalkulationen), **gewichtet** (offene Kalkulationen × Wahrscheinlichkeit), **potenziell** (offene zu 100 %).
- AUS-3: Ansichten: Fest (Bestand + gewonnen), Erwartet (+ gewichtet), Maximal (+ alle offenen).
- AUS-4: Stunden je Kalkulation = Maschinenstunden p. a. inkl. Rüsten der aktuellen Version, ab SOP (sonst ab heute
  bzw. 1. Januar Folgejahr) über die Projektlaufzeit, anteilig im Start- und Endjahr. Nicht berücksichtigt:
  verloren, kein Angebot, zurückgestellt. Kalkulationen ohne Maschine erscheinen als „ohne Maschinenzuordnung“.
- AUS-6: Auslastung umfasst alle Anlagenarten (STM-18): Stunden weiterer Arbeitsgänge (KAL-28g) werden der gewählten
  Anlage zugerechnet (Stunden p. a. = Jahresmenge / Stück je h + Lose p. a. × Rüstzeit); im Aufklappen mit Name des
  Arbeitsgangs. Arbeitsgänge ohne Anlage erscheinen unter „ohne Maschinenzuordnung“.
- AUS-5: Farbstufen < 60 %, 60–85 %, 85–100 %, ≥ 100 % (mit Warnsymbol); Aufklappen je Maschine zeigt die
  beteiligten Kalkulationen mit Stunden je Jahr; Gesamtzeile; KPI „Auslastung Folgejahr“ im Dashboard.

### 6.8 CO₂-Fußabdruck je Teil (Product Carbon Footprint)
- CO2-1: Eingaben in der Kalkulation (aus Stammdaten vorbelegt, überschreibbar): Emissionsfaktor Material und
  Masterbatch, Leistungsaufnahme Maschine, Strom-Emissionsfaktor, Werksemissionen Scope 1, CO₂ Zukaufteile je Stück,
  CO₂ Verpackung je VE (Einweg je VE, Mehrweg je Umlauf), Transportentfernung und -faktor.
- CO2-2: Rechenweg je Gutteil (kg CO₂e):
  | Quelle | Formel | Scope |
  |---|---|---|
  | Material | kg je Teil inkl. Angussanteil × Faktor (Mischung Masterbatch) / (1 − Ausschuss) + Anfahrausschuss je Los | 3 vorgelagert |
  | Strom | (kW / Stück je h / (1 − Ausschuss) + Rüstzeit × kW / Losgröße + Σ Arbeitsgänge kW × (1 / Stück je h + Rüstzeit / Losgröße)) × kg CO₂e/kWh | 2 |
  | Werksemissionen | Maschinenstunden je Teil × kg CO₂e je Maschinenstunde | 1 |
  | Zukaufteile | Pauschalwert je Stück + Σ (Menge × kg CO₂e je Einheit) der Zukaufteile-Liste | 3 vorgelagert |
  | Verpackung | kg CO₂e je VE / Teile je VE | 3 vorgelagert |
  | Transport | Teilgewicht t × km × kg CO₂e/tkm (0 bei ab Werk) | 3 nachgelagert |
- CO2-3: Ausgaben: **je Stück (g), je 1.000 Stück (kg), je Los (kg), Jahresmenge (t)**, je Lieferung, je kg Teil,
  Strom Wh je Stück und kWh p. a.; Summen **Cradle-to-Gate** und **Scope 1+2**; Aufteilung nach Quelle mit Anteil.
- CO2-4: **Ausweis im Angebot** (je Kalkulation abschaltbar): Cradle-to-Gate g CO₂e/Stück, kg je 1.000 Stück,
  davon Scope 1+2.
- CO2-5: Ältere Versionen ohne CO₂-Angaben zeigen keinen Fußabdruck; der Preis ist davon unabhängig.
- CO2-6: Abgrenzung: vereinfachter PCF ohne Zertifizierung (keine vollständige ISO 14067-Bilanz); Nutzungs- und
  End-of-Life-Phase nicht enthalten. Ausrichtung auf das bestehende F&R-Konzept (Scope 1–2 je Bauteil/Auftrag/Lieferung).

### 6.9 Auswertungen (Berichte)
- AUSW-1: Seite „Auswertungen“ mit Filtern Zeitraum (Anfragedatum, sonst Anlagedatum; Schnellwahl Jahr, Vorjahr,
  12 Monate, alle), Vertrieb und Kunde. Kennzahlen: Anfragen, offen, Angebotsquote, Trefferquote
  (gewonnen / (gewonnen + verloren)), Absagequote (kein Angebot / Anfragen), angefragter und gewonnener Jahresumsatz.
- AUSW-2: Berichte je **Maschinengröße** (Schließkraftklassen bis 100 t, 100–250 t, 250–500 t, über 500 t, ohne
  Maschine – nach der in der Kalkulation gewählten Maschine), **Kunde** (Anzahl, Anteil an Anfragen und am
  angefragten Umsatz, Trefferquote), **Absagegründe** (kein Angebot), **Verlustgründe**, **Maschine**, **Werkstoff**,
  **Vertrieb**, **Status**, **Machbarkeit**, **Monat**.
- AUSW-3: Je Bericht: Anfragen, Anteil, angeboten, gewonnen, verloren, kein Angebot, offen, Umsatz p. a. angefragt,
  Anteil Umsatz, gewonnener Umsatz, Trefferquote, Absage-/Verlustquote; Balkendiagramm umschaltbar nach Anzahl,
  Umsatz oder Absagen + Verluste.
- AUSW-4: Export je Bericht als CSV (Excel, deutsches Zahlenformat), Druck/PDF der Seite (auch „Alle Berichte“).
- AUSW-5: Lesezugriff für alle Rollen inkl. Gesellschafter.

### 6.11 Standorte der Gruppe
- STO-1: Stammdaten „Standorte“: Kürzel, Name, Land, Anschrift, Reihenfolge, aktiv. Je Standort **abweichende Sätze**
  gegenüber den Gruppen-Parametern (Matrix: Lohnsätze, Zuschläge, Zukaufteile, Verpackung/Transport pauschal,
  Gewinn/Konditionen, Fertigung, CO₂-Faktoren, Strompreis); leeres Feld = Gruppen-Standard.
- STO-2: Maschinen und Anlagen sind einem Standort zugeordnet (Maschinenstundensatz je Maschine).
- STO-3: Jede Kalkulation hat einen **Fertigungsstandort** (Teil der Version). Neue Kalkulationen erhalten den
  Standard-Standort des Benutzers (sonst den ersten Standort) und dessen Sätze. Die Maschinenauswahl zeigt die
  Maschinen des Standorts; die „≠ Standard“-Markierung bezieht sich auf die Standort-Sätze.
- STO-4: **Standortwechsel** in der Kalkulation: Standard-Sätze des bisherigen Standorts werden durch die des neuen
  ersetzt, individuell geänderte Werte bleiben; Spritzgießmaschine wird durch die kleinste vergleichbare Maschine
  (gleiche Art, Schließkraft ≥ bisher, bei Mehrkomponenten bevorzugt 2K) ersetzt, Arbeitsgänge entsprechend;
  Hinweise, wenn keine vergleichbare Maschine/Anlage vorhanden ist.
- STO-5: **Standortvergleich**: dieselbe Kalkulation (Zykluszeit, Material, Mengen gleich) für alle aktiven Standorte
  mit Maschine, Maschinen- und Lohnsatz, Stück/h, Grenzkosten, Selbstkosten, Preis, Δ % zum aktuellen Standort,
  Umsatz, CO₂ je Stück; günstigster Standort markiert; „Standort übernehmen“ stellt die Kalkulation um (speichern als
  neue Version).
- STO-6: Filter nach Standort in Kalkulationsliste, Auslastung und Auswertungen; Bericht „Standorte“.

### 6.12 Datenimport (CSV/Excel)
- IMP-1: Import für Firmen, Kontakte (Vertrieb und Administrator) sowie Maschinen, Materialien und Zukaufteile
  (nur Administrator) über „Importieren“ in der jeweiligen Liste; zusätzlich per REST-API (`/api/import/…`,
  Dokumentation unter `/api/docs`).
- IMP-2: Formate: CSV mit Semikolon, Komma oder Tab, UTF-8 oder Windows-1252; Excel .xlsx (erstes Blatt); erste Zeile =
  Überschriften; höchstens 5.000 Zeilen. Vorlage je Typ zum Herunterladen (Pflichtfelder mit *, Beispielzeile).
- IMP-3: Spalten werden anhand Bezeichnung und üblicher Synonyme automatisch zugeordnet und sind änderbar.
  Zahlen im deutschen und englischen Format, Datum TT.MM.JJJJ oder ISO, ja/nein, Auswahlwerte (Typ, Maschinenart),
  Bediener-Anteil in % oder als Faktor, Standort per Name oder Kürzel, Firma eines Kontakts per Firmenname.
- IMP-4: **Vorschau vor dem Speichern** je Zeile: neu / aktualisieren (mit geänderten Feldern) / unverändert / Fehler
  (Pflichtfeld fehlt, Wert nicht lesbar, Firma/Standort unbekannt, doppelt in der Datei). Abgleich vorhandener
  Datensätze: Firma und Material über den Namen, Kontakt über E-Mail (sonst Firma + Name), Maschine über die Nummer,
  Zukaufteil über Artikel-Nr. bzw. Bezeichnung.
- IMP-5: Übernahme nur fehlerfreier Zeilen; Aktualisieren vorhandener Datensätze abschaltbar; Ergebnis mit Anzahl neu,
  aktualisiert, übersprungen und Fehlerliste; jede Änderung im Änderungsprotokoll.

### 6.10 Beschaffung Werkzeuge, Montagelinien, Vorrichtungen, Prüfmittel
- BES-1: Menüpunkt „Beschaffung“ und Reiter „Beschaffung“ in jeder Kalkulation. Je Vorgang: Nummer (BA-Jahr-lfd. Nr.),
  Art (Spritzgießwerkzeug, Montagelinie, Vorrichtung, Prüfmittel, Sonstiges), Bezeichnung, Kalkulation, Status
  (offen, angefragt, entschieden, bestellt, abgebrochen), Angebotsabgabe bis, benötigt bis, Hinweise.
- BES-2: **Eckdaten der Anfrage**, aus der Kalkulation vorbelegt und änderbar. Werkzeug: Artikel, Kunden-/eigene
  Art.-Nr., Werkstoff (inkl. weiterer Komponenten), Teilgewicht, **Fachzahl**, **Werkzeugart** (1K/2K/Familie),
  **Heißkanal/Kaltkanal** (aus Angussgewicht), Düsen, Heißkanal-Fabrikat, Anschnitt, Ziel-Zykluszeit, Maschine und
  Schließkraft, Jahresmenge, Laufzeit, **Standzeit** (Jahresmenge × Laufzeit / Fachzahl × 1,2, gerundet), Stahl,
  Normalien, Schieber, Temperierung, Entformung, Oberfläche, Bemusterung, Unterlagen, Lieferbedingung, SOP.
  Montagelinie/Vorrichtung/Prüfmittel: Leistungsumfang, Arbeitsgänge/Stationen, Taktzeit, Verfügbarkeit, Abnahme.
- BES-3: **Werkzeuganfrage** je Lieferant als Druck/PDF im Firmenlayout (Logo, Fußzeile) mit Eckdaten, Abgabetermin
  und geforderten Angebotsangaben; **E-Mail-Entwurf** an den Ansprechpartner des Lieferanten (Zeichnung/3D-Daten
  anhängen).
- BES-4: Lieferanten aus „Firmen“ (Typ Lieferant, E-Mail des Ansprechpartners wird übernommen) oder frei erfasst;
  beliebig viele Anfragen je Vorgang (z. B. 5 – 7 Werkzeugmacher).
- BES-5: **Angebot je Lieferant**: Status, Angebots-Nr./-Datum, Preis netto, Lieferzeit bis T0/Abnahme, Fachzahl,
  Heißkanal, Stahl, Standzeit, Gewährleistung, Zahlungsbedingungen, Fertigungsort, technische Bewertung 1 – 5,
  Bemerkung.
- BES-6: **Angebotsvergleich**: Balkendiagramm und Tabelle, günstigstes Angebot markiert, Δ % zum günstigsten,
  Spanne; Kennzahlen Anzahl angefragt/mit Preis, günstigstes, gewählt.
- BES-7: **Vergabeentscheidung** mit Begründung, Datum und Entscheider (Nachweis im Protokoll); übrige Angebote
  „nicht gewählt“; Entscheidung rücknehmbar.
- BES-8: **In Kalkulation übernehmen**: Preis des gewählten Angebots wird als Kosten der passenden Einmalkosten-
  Position (sonst neue Position) in eine **neue Kalkulationsversion** übernommen, mit automatischer Änderungsnotiz
  (alt → neu, Vorgang, Lieferant, Angebot); Preis an Kunde bleibt unverändert, sofern gesetzt.
- BES-9: Dokumente je Vorgang (Zeichnung, 3D, Lieferantenangebote, Bestellung); alle Änderungen im Änderungsprotokoll.

## 7. Nachkalkulation
- NK-1: Zu jeder Kalkulation beliebig viele Nachkalkulationen (z. B. je Fertigungsauftrag oder Zeitraum) mit
  Referenz, Zeitraum, Bemerkung und Bezug auf eine Version.
- NK-2: Erfasst werden nur abweichende **Ist-Werte** (auch Verpackungs- und Frachtkosten): Zykluszeit, Fachzahl, Produktivität, Ausschuss, Materialpreis,
  Teil- und Angussgewicht, Rüstzeit, Losgröße, Montagezeit, Lohnsatz, Bedienfaktor, Maschinen- und
  Instandhaltungssatz, Zukaufteile, produzierte Menge, zusätzliche Ist-Kosten gesamt, erzielter Preis.
- NK-3: Die Ist-Rechnung nutzt **dasselbe Schema** wie die Vorkalkulation (vergleichbar).
- NK-4: Plan/Ist-Vergleich je Position inkl. Qualität und Werkzeugbau (€/Stk, Δ €/Stk, Δ %), Stück/h, Marge Ist, Ergebnis gesamt (Menge × Gewinn).
- NK-5: **Ampel**: grün bis Grün-Schwelle Abweichung der Selbstkosten, gelb bis Rot-Schwelle, rot darüber oder wenn
  der Preis die Ist-Selbstkosten nicht deckt. Schwellen in den Parametern (STM-10).
- NK-6: Live-Vorschau der Ampel vor dem Speichern.

## 7a. Freigabe, Nachweisführung und Lebensweg (IATF 16949 / ISO 14001)

### 7a.1 Freigabe-Workflow (Vier-Augen-Prinzip)
- FRG-1: Eine Kalkulation ist **freigabepflichtig**, wenn Jahresumsatz ≥ Großprojekt-Schwelle, Invest ≥
  Großprojekt-Schwelle oder Marge < Mindestmarge (Parameter, Standard 3 %).
- FRG-2: Freigabe anfordern (mit Begründung) → Benachrichtigung aller Freigabeberechtigten. Freigeben/Ablehnen nur
  durch Administratoren oder Benutzer mit Recht „darf freigeben“; **nie durch die anfragende Person** (Vier Augen).
  Ablehnung nur mit Begründung. Anfragende Person wird über die Entscheidung benachrichtigt.
- FRG-3: Die Freigabe gilt **nur für die freigegebene Version**; jede neue Version macht eine erneute Freigabe nötig.
- FRG-4: Ohne gültige Freigabe kann aus einer freigabepflichtigen Kalkulation **kein Angebot** (auch kein
  Sammelangebot) erzeugt werden.
- FRG-5: Anzeige im Kalkulationskopf (Status, Version, Personen, Zeitpunkte, Kommentare), Kennzeichen und Filter in
  der Liste, Kennzahl „Freigaben angefragt / noch nicht angefragt“.

### 7a.2 Änderungsprotokoll (Audit-Trail)
- PRT-1: Jede Anlage, Änderung und Löschung an allen Datensätzen wird automatisch protokolliert: Zeitpunkt,
  Benutzer, Aktion, Datensatz, je Feld **alter → neuer Wert**. Passwörter werden maskiert, große Strukturen
  (Kalkulationseingaben/-ergebnisse) als „geändert“ vermerkt – ihr Inhalt ist in der unveränderlichen Version gesichert.
- PRT-2: Protokolleinträge sind über die Oberfläche **nicht änderbar oder löschbar**.
- PRT-3: Gesamtprotokoll mit Filtern (Bereich, Benutzer, Zeitraum, Suche) für Administration, Gesellschafter und
  Freigabeberechtigte; je Kalkulation Reiter „Protokoll“ inkl. Versionen, Anrufe, Nachkalkulationen.
- PRT-4: Feldnamen werden im Protokoll mit deutschen Bezeichnungen angezeigt.

### 7a.3 Löschschutz / Aufbewahrung
- LSH-1: Kalkulationen, Nachkalkulationen und Firmen löschen nur Administratoren; jede Löschung steht im Protokoll.
- LSH-2: Angebote sind nur als **Entwurf** löschbar; versendete/angenommene/abgelehnte Angebote bleiben als Nachweis.
- LSH-3: Kalkulationsversionen sind unveränderlich (KAL-31).

### 7a.4 Lebenswegbetrachtung (ISO 14001, 6.1.2) – Kurzfassung je Artikel
- LWB-1: Fünf Phasen mit automatisch übernommenen Kennzahlen aus der Kalkulation und kurzen Angaben:
  **Rohstoffe** (Material/Komponenten, CO₂-Anteil; Rezyklatanteil %, biobasiert, Anmerkung) ·
  **Herstellung** (Strom Wh/Stk, Ausschuss, Mahlgut, Scope 1+2; Anmerkung) ·
  **Transport & Verpackung** (Mehrweg/Einweg, Lieferbedingung, CO₂; Anmerkung) ·
  **Nutzung** (Umweltrelevanz gering/mittel/hoch; Anmerkung) ·
  **Ende des Lebenswegs** (Monomaterial/Verbund automatisch; Recyclingfähigkeit, Verwertungsweg,
  Werkstoffkennzeichnung, Anmerkung).
- LWB-2: **Wesentlicher Umweltaspekt** = Phase mit dem höchsten CO₂-Anteil (automatisch); Feld
  Verbesserungsmaßnahme/Ziel.
- LWB-3: Optional Kurzfassung im Angebot (Rezyklatanteil, Kennzeichnung, Verwertung, Monomaterial).

### 7a.5 Zuordnung zu Normforderungen (Unterstützung, keine Zertifizierungsaussage)
| Forderung | Umsetzung in KlarCRM |
|---|---|
| IATF 16949 / ISO 9001 – Bewertung der Anforderungen an Produkte, Herstellbarkeitsanalyse | Artikelanalyse, Machbarkeit, Checkliste (ANA-1 … 6, KAL-4b) |
| Lenkung dokumentierter Information, Rückverfolgbarkeit von Änderungen | Unveränderliche Versionen, Änderungsprotokoll, Löschschutz (KAL-30 … 33, PRT, LSH) |
| Verantwortung und Befugnis, Freigaben | Rollen, Freigabeberechtigung, Vier-Augen-Prinzip (ROL, FRG) |
| ISO 14001 6.1.2 – Umweltaspekte mit Lebenswegbetrachtung | Lebenswegbetrachtung je Artikel, CO₂-Fußabdruck (LWB, CO2) |
| ISO 14001 9.1 – Überwachung, Messung | CO₂ je Teil/Jahr, Nachkalkulation mit Ist-Werten (CO2, NK) |

Hinweis: Die Software unterstützt die Nachweisführung. Ob die Prozesse normkonform sind, bewertet das Audit;
Verfahrensanweisungen (wer kalkuliert, wer freigibt, Aufbewahrungsfristen) sind im Managementsystem zu regeln.

## 7b. Arbeitsabläufe

### 7b.1 Dokumente
- DOK-1: Dokumente an **Kalkulation** (eigener Reiter), **Firma** und **Angebot**: hochladen per Auswahl oder Drag & Drop,
  mehrere Dateien gleichzeitig; Art (Zeichnung, 3D-Daten, Kundenanfrage, Lastenheft Kunde, Prüfplan/Messkonzept,
  Musterbericht/EMPB, Sonstiges), Revision/Index, Notiz; Anzeige mit Datum, Person, Größe; Download.
- DOK-2: Größenlimit (Standard 50 MB), ausführbare Dateien (.exe, .bat, .js …) gesperrt.
- DOK-3: „Entfernen“ blendet nur aus – die Datei bleibt als Nachweis gespeichert; nur hochladende Person oder
  Administrator; jede Aktion im Änderungsprotokoll. Ablage im Volume `uploads` auf dem internen Server.

### 7b.2 Benachrichtigungen
- BEN-1: Glocke in der Seitenleiste mit Zähler; Inhalte: gespeicherte Nachrichten (Freigabe angefragt / entschieden),
  laufende Hinweise (heute fällige und überfällige Aufgaben, Angebote mit Ablauf in ≤ 7 Tagen, offene Freigaben für
  Freigabeberechtigte); Klick führt zum Datensatz; „alle gelesen“; Aktualisierung jede Minute.
- BEN-2: Optional E-Mail-Versand der Nachrichten über den internen Mailserver (SMTP), wenn konfiguriert.

### 7b.3 Outlook
- OUT-1: **Kalenderabo** je Benutzer (iCalendar-Adresse mit persönlichem Schlüssel, erneuerbar): Termine, Anrufe,
  Aufgaben und Wiedervorlagen erscheinen in Outlook (inkl. Erinnerung 15 min); Abruf aus dem internen Netz.
- OUT-2: Einzelne Aktivität als .ics-Datei für Outlook.
- OUT-3: Angebot per E-Mail: öffnet Outlook mit Empfänger (Ansprechpartner), Betreff und Text in der Angebotssprache;
  das PDF wird über „Drucken / PDF“ gespeichert und angehängt.

### 7b.4 Briefkopf und Dokumente im Firmenlayout
- PDF-1: Firmeneinstellungen „Firma & Layout“ (Administrator): Firmenname, Adresse, Land, Telefon, Fax, E-Mail,
  Website, **weitere Standorte** (z. B. Werk Krupka), Handelsregister, **Sitz der Gesellschaft**, USt-IdNr.,
  **Steuernummer**, Geschäftsführung, **zwei Bankverbindungen** (Bank/IBAN/BIC), **Zertifizierungen** und optionaler
  Fußzeilen-Zusatz, Akzentfarbe, **Logo** (hochladen, entfernen, Größe klein/mittel/groß), Standardtexte
  Einleitung/Bedingungen/Grußformel je Sprache. **Live-Vorschau** des Briefkopfs auf der Einstellungsseite.
- PDF-1a: Ein gemeinsamer Briefkopf und eine gemeinsame Fußzeile für **alle Dokumente** (Angebot, Werkzeug-/
  Anlagenanfrage); leere Felder werden ausgelassen.
- PDF-2: Druckansicht DIN A4: Kopf mit Logo und Firmenname, Absenderzeile, Anschriftfeld, Angebotsdaten,
  Positionstabelle, Summen, Bedingungen, Grußformel, **Fußzeile** mit Firmen-, Register- und Bankdaten.
- PDF-3: **Sprache Deutsch/Englisch** je Angebot: Beschriftungen, Datums- und Zahlenformat, Anrede, Standardtexte;
  Sprache bereits beim Erzeugen aus Kalkulation/Sammelangebot wählbar – dann werden auch die Positionstexte
  (Material, Staffeln, Preisgleitklausel, Verpackung, Lieferbedingung, CO₂, Lebensweg) in der Sprache erzeugt.
  Beim Umschalten werden unveränderte Standardtexte mitgetauscht.

## 8. Nicht-funktionale Anforderungen
- NFA-1: Web-Anwendung (Desktop und Tablet), deutschsprachig, Zahlen im deutschen Format.
- NFA-2: Selbst gehostet (Docker) auf dem **internen Server von F&R**, keine Lizenzkosten je Nutzer; Daten und Dokumente
  bleiben im eigenen Netz (DSGVO). Keine Fremdwährung (nur Euro), Oberfläche Deutsch (Angebote zusätzlich Englisch).
- NFA-3: Anmeldung per E-Mail/Passwort, Passwörter mit bcrypt gehasht, Sitzungen per Token (12 h).
- NFA-4: Betrieb hinter HTTPS-Reverse-Proxy; tägliches Backup von Datenbank **und** Dokumenten mit Wiederherstellungstest.
- NFA-5: Automatischer Build- und Starttest bei jedem Push (GitHub Actions).
- NFA-6: API vollständig dokumentiert (Swagger unter /docs).
- NFA-8: Datenbank-Erweiterungen werden beim Start automatisch ergänzt (neue Tabellen, neue Spalten, Verbreitern von
  Textfeldern); Umbenennen/Löschen/Verkleinern bleibt ein manueller Schritt.
- NFA-9: **Rechentests**: jeder Rechenweg (Schema, Zuschläge, Staffeln, Mehrkomponenten, Familienwerkzeug,
  Amortisation, Verpackung/Transport, CO₂, Nachkalkulation, Stundensatz, Artikelanalyse) ist gegen eine
  Handrechnung automatisiert getestet; Tests laufen bei jedem Push, ein Fehler stoppt den Build.
- NFA-11: **Validierung**: Vorlage „Validierungsprotokoll und Testplan Pilot“ (Rechenvalidierung gegen die
  Excel-Kalkulation, Funktionstests, Nachweis automatischer Tests, Änderungsmanagement, Freigabe) als eigenes
  Dokument; bei Änderungen am Rechenweg erneute Prüfung und Freigabe.
- NFA-10: **Seitenhilfe**: oben auf jeder Seite eine kurze Anleitung „So arbeiten Sie hier“ (Zweck der Seite und
  Vorgehen in Schritten); auf-/zuklappbar, Zustand je Seite und Browser gemerkt; nicht im Druck.
- NFA-7: Fußzeile auf allen Seiten inkl. Anmeldung: „© <Jahr> SB/Thinkworks · KlarCRM · built with clarity“ (nicht im Druck).

## 9. Technik
- Backend: Python FastAPI, SQLAlchemy, PostgreSQL 16; Rechenkern in `backend/app/calc_engine.py`.
- Frontend: React 18 (Vite), Auslieferung über nginx.
- Testumgebung: GitHub Codespaces (Demo-Daten, Logins siehe README).

## 10. Abgrenzung / noch nicht umgesetzt
- Kein direkter E-Mail-Versand von Angeboten aus dem Server (Outlook-Entwurf über E-Mail-Link, PDF manuell anhängen).
- Kein Import aus ERP/BDE; Ist-Werte der Nachkalkulation werden manuell erfasst.
- Keine Mehrwährung (Euro) und keine tschechische Oberfläche – bewusst nicht benötigt.
- Keine vollwertigen Datenbank-Migrationen (Alembic) – nur additive automatische Ergänzung (NFA-8).

## 11. Offene Punkte / Ideen für die finale Version
- [ ] Abgleich des Kalkulationsschemas mit der bestehenden F&R-Excel-Kalkulation (Positionen, Zuschlagsbasen).
- [x] Staffelpreise je Losgröße (v1.4) und nach Jahresmenge (v1.9).
- [x] Werkzeugamortisation über Stückzahl als Option (v1.9).
- [ ] Mehrere Artikel je Anfrage in einer Kalkulationsmappe.
- [ ] Übernahme von Ist-Werten aus BDE/MES für die Nachkalkulation.
- [ ] CSV-/Excel-Import und -Export (Firmen, Kontakte, Kalkulationsliste).
- [ ] Wiedervorlage-Automatik ohne manuelles Datum (Aufgabe, wenn > 14 Tage kein Anruf).
- [ ] Zuschlagsbasis für weitere Zuschläge wählbar machen, falls die F&R-Excel-Kalkulation das erfordert.
- [ ] CO₂: Ist-Energiewerte aus BDE/Energiemonitoring in die Nachkalkulation übernehmen; CO₂-Summen je Kunde/Jahr.
- [ ] Rechte: Kalkulation nur für bestimmte Rollen sichtbar machen (z. B. Gewinnsätze).
- [ ] Aufbewahrungsfristen und Archivierung (z. B. 10 Jahre) im Managementsystem festlegen und im System abbilden.

## 12. Änderungshistorie

| Version | Datum | Änderung |
|---|---|---|
| 1.0 | 13.11.2026 | Erstversion CRM: Firmen, Kontakte, Pipeline, Aktivitäten, Angebote, Dashboard, Rollen, Docker, Codespaces-Testumgebung |
| 1.1 | 14.11.2026 | Modul **Kalkulation**: Stammdaten Maschinen/Materialien/Parameter, Zuschlagskalkulation Spritzguss (Material, MGK, Maschine, Instandhaltung, Personal, Rüsten, Montage, FGK, Ausschuss, Verwaltung, Vertrieb, Projektmanagement, Gewinn 7 % Standard), Zusatz- und Einmalkosten, Werte je Stück/100/1.000, Versionen mit Vergleich, Kalkulationsliste mit Verlustgründen und „zuletzt angerufen“, Übernahme in Verkaufschance, Angebot aus Kalkulation, Nachkalkulation mit Ampel, KPIs im Dashboard. Lastenheft eingeführt. |
| 1.2 | 14.11.2026 | Anrufhistorie mit Ergebnis je Kalkulation (KAL-8 bis KAL-10), Anzeige „zuletzt angerufen + Ergebnis“ in Liste und Kalkulationskopf, Wiedervorlage als Aufgabe; Zuschläge **Qualität** und **Werkzeugbau** mit wählbarer Basis FEK/HK (KAL-27, STM-7, Rechenweg 6.2); Copyright-Fußzeile SB/Thinkworks (NFA-7). Neue Tabelle `calculation_calls` (wird automatisch angelegt). |
| 1.3 | 14.11.2026 | **Großprojekte hervorheben** (KAL-55 bis KAL-58, STM-12): Jahresumsatz oder Invest ≥ 500.000 € (Schwellen änderbar), Kennzeichen in Kalkulationen, Angeboten und Pipeline, Filter und KPI. Fehlerbehebung: Verkaufschance aus Kalkulation übernimmt jetzt sofort das Volumen (vorher 0 €). |
| 1.4 | 14.11.2026 | **Machbarkeit** (4 Stufen + Anmerkung), Status **„Kein Angebot abgegeben“** mit Gründen und Freitext (KAL-4a/4b, KAL-59), **Artikelanalyse** mit Schließkraft, Fließweg/Wandstärke, Kühlzeit-Richtwert, passenden Maschinen, Checkliste und Machbarkeitsvorschlag (ANA-1 bis ANA-6), **Staffelpreise** für bis zu 3 Losgrößen inkl. Übernahme ins Angebot (KAL-28), **Auslastung kommende Jahre** je Maschine mit Bestand, fest, gewichtet, potenziell (AUS-1 bis AUS-5, STM-13), automatische Ergänzung neuer DB-Spalten (NFA-8). |
| 1.5 | 14.11.2026 | **Sammelangebot** aus mehreren Kalkulationen (KAL-43 bis KAL-45): Mehrfachauswahl in der Kalkulationsliste, Prüfung gleicher Kunde, ein Angebot mit allen Serienteilen und Einmalkosten; **Herkunft** Angebot ↔ Kalkulation in beide Richtungen sichtbar (KAL-46). Neue Spalte `quotes.calculation_ids` (automatisch ergänzt). Angebotspositionen zeigen mehrzeilige Texte vollständig. |
| 1.6 | 14.11.2026 | Eigener Bereich **Verpackung & Transport** mit echten Beträgen (KAL-29, Rechenweg 6.2): Kosten je VE/Umlauf, Teile je VE, Packzeit, VE je Palette; Transport ab Werk, je Palette, je Lieferung oder % auf HK; Lieferbedingung; Übernahme ins Angebot; Ist-Werte in der Nachkalkulation. |
| 1.7 | 14.11.2026 | **CO₂-Fußabdruck je Teil** (Kap. 6.8, CO2-1 bis CO2-6, STM-14): Material, Strom (Scope 2), Werksemissionen (Scope 1), Zukaufteile, Verpackung, Transport; je Stück, 1.000, Los, Jahresmenge, Lieferung; Ausweis im Angebot. Neue Stammdatenfelder (Materialfaktor, Maschinenleistung, Standort-Stromfaktor) werden automatisch ergänzt. |
| 1.8 | 14.11.2026 | Verpackung wahlweise **pauschal in % auf HK** oder detailliert; Transport pauschal in % weiterhin wählbar; Standardsätze Verpackung 1,5 % / Transport 2,0 % in den Parametern (KAL-29a). |
| 1.9 | 14.11.2026 | **Etappe 1 Profi-Kalkulation**: Mehrkomponenten 2K/3K (KAL-28b), Familienwerkzeug (KAL-28c), Werkzeugamortisation (KAL-28d), Staffeln nach Jahresmenge (KAL-28a), Kopieren und Vorlagen (KAL-28e), Preisgleitklausel im Angebot (KAL-28f), Herleitung Maschinenstundensatz inkl. Umlage Kostenstelle (STM-15), Rohstoffpreis-Historie und Preisgleitung (STM-16/17), Rechentests im Build (NFA-9). Angebotspositionen ohne Längenbegrenzung. |
| 1.10 | 14.11.2026 | **Etappe 2 Nachweisführung**: Freigabe-Workflow mit Vier-Augen-Prinzip (FRG-1 … 5, ROL-6), Änderungsprotokoll für alle Daten (PRT-1 … 4), Löschschutz (LSH-1 … 3), Lebenswegbetrachtung nach ISO 14001 6.1.2 (LWB-1 … 3), Zuordnung zu IATF 16949 / ISO 14001 (Kap. 7a.5). |
| 1.11 | 14.11.2026 | **Etappe 3 Arbeitsabläufe**: Dokumente an Kalkulation/Firma/Angebot (DOK-1 … 3), Benachrichtigungen mit optionalem SMTP (BEN-1/2), Outlook-Kalenderabo, .ics und E-Mail-Entwurf (OUT-1 … 3), Angebots-PDF im Firmenlayout mit Logo, Fußzeile, Deutsch/Englisch (PDF-1 … 3); Betrieb auf internem Server inkl. Backup von Dokumenten (NFA-2/4). |
| 1.12 | 14.11.2026 | **Montagelinie & weitere Arbeitsgänge** (KAL-28g, AUS-6): 1 … N Anlagen je Artikel mit eigenem Stundensatz, Takt, Personal, Rüsten und kW; Maschinenart in den Stammdaten (STM-18). **Zukaufteile-Stammdaten** (STM-19/20) und Zukaufteile-Liste je Kalkulation mit Menge und CO₂ (KAL-28h). Neue Tabelle `purchased_parts` und Spalte `machines.kind` werden automatisch angelegt; gespeicherte Versionen rechnen unverändert. Rechentests ergänzt. |
| 1.13 | 15.11.2026 | **Zukaufteile**: optional eigener MGK-Satz (KAL-28i) und optionale **Nebenkalkulation für teure Zukaufteile** mit eigenem MGK, Qualität, Ausschuss und optionalem Aufschlag statt voller Kalkulation (KAL-28j); Standardsätze in den Parametern (STM-21). Ohne Haken/Satz rechnen Kalkulationen wie bisher. Rechentests ergänzt; breite Tabellen in der Kalkulation scrollen jetzt waagerecht. |
| 1.14 | 15.11.2026 | **Personal in Prozent je Maschine**: Bediener mit Schnellwahl 10–120 % oder freiem Satz, zusätzlich **Mitarbeiter Handling** und **Mitarbeiter Automatisierung** (je 0 … 100 %, eigener Lohnsatz), Standards je Maschine; **Rüsten** mit eigener Einrichter-Zeit und Automatisierer-Zeit je Rüstvorgang (Minuten) und Aufschlüsselung der Rüstkosten. Neue Felder starten mit 0 bzw. leer, gespeicherte Versionen rechnen unverändert. Neue Spalten `machines.handling_pct`, `machines.automation_pct` werden automatisch angelegt. |
| 1.15 | 15.11.2026 | **Auswertungen** (Kap. 6.9, AUSW-1 … 5): Berichte nach Maschinengröße, Kunde (Anteil an Anfragen und Umsatz), Absage- und Verlustgründen, Maschine, Werkstoff, Vertrieb, Status, Machbarkeit und Monat mit Filtern, CSV und Druck. **Seitenhilfe** auf jeder Seite (NFA-10). **Jahresabschläge** mit Vorab-Einrechnung und eigenen Abschlägen für Zukaufteile der Nebenkalkulation (KAL-28k). **Vorserienpreis** für Kleinstmengen inkl. Angebotsposition (KAL-28l). Rechentests ergänzt; gespeicherte Versionen rechnen unverändert. |
| 1.16 | 15.11.2026 | **Preis Jahr 1 manuell (Anlaufpreis)**, ab Jahr 2 kalkulierter Serienpreis; Jahresabschläge als Tabelle je Lieferjahr mit zwei gekoppelten Eingabespalten („% ggü. Vorjahr“ und „% vom Serienpreis“), getrennt für Zukaufteile der Nebenkalkulation (KAL-28k). **Fester Vorserienpreis** mit kalkuliertem Wert und Marge als Orientierung (KAL-28l). Rechentests ergänzt. Darstellung: Formularspalten laufen nicht mehr über. |
| 1.17 | 15.11.2026 | **Abschläge vorab draufschlagen** auch bei manuellem Anlaufpreis, zwei Varianten (Ø Laufzeit = Kalkulation / letztes Jahr ≥ Kalkulation), Marge je Lieferjahr mit Warnung bei Minusgeschäft (KAL-28k). Rechentests ergänzt. |
| 1.18 | 15.11.2026 | **Beschaffung** (Kap. 6.10, BES-1 … 9): Vorgänge für Werkzeuge, Montagelinien, Vorrichtungen und Prüfmittel, Eckdaten aus der Kalkulation, **Werkzeuganfrage** als PDF im Firmenlayout und E-Mail-Entwurf je Lieferant, Angebotsvergleich, Vergabeentscheidung mit Begründung, Übernahme in die Kalkulation als neue Version. Neue Tabellen `procurement_requests`, `procurement_offers` (automatisch angelegt). Seitenhilfe ergänzt. |
| 1.19 | 15.11.2026 | **Briefkopf erweitert** (PDF-1, PDF-1a): Fax, weitere Standorte, Sitz, Steuernummer, zweite Bankverbindung, Zertifizierungen, Fußzeilen-Zusatz, Logogröße und Logo entfernen; Live-Vorschau; gemeinsamer Briefkopf für Angebot und Werkzeuganfrage. |
| 1.20 | 15.11.2026 | **Grenzkostenkalkulation** (KAL-28m): direkte Artikelkosten inkl. Verpackung und Transport, Deckungsbeitrag je Stück/p. a./Lieferjahr, Preisuntergrenzen; Strompreis als Eingabe. Rechentest mit Handrechnung ergänzt; gespeicherte Versionen rechnen unverändert (ohne Strompreis = ohne Energie). |
| 1.21 | 15.11.2026 | **Standorte der Gruppe** (Kap. 6.11, STO-1 … 6): Standort-Stammdaten mit abweichenden Sätzen, Maschinen je Standort, Fertigungsstandort je Kalkulation mit Standortwechsel, Standortvergleich aller Standorte, Standard-Standort je Benutzer, Filter in Liste/Auslastung/Auswertungen. Neue Tabelle `sites`, neue Spalten `machines.site_id`, `calculations.site_id`, `users.site_id` (automatisch). Bestehende Kalkulationen ohne Standort gelten als Standard-Standort. |
| 1.22 | 15.11.2026 | **Datenimport CSV/Excel** (Kap. 6.12, IMP-1 … 5) für Firmen, Kontakte, Maschinen, Materialien, Zukaufteile mit Vorlage, Spaltenzuordnung, Vorschau und Protokoll; Tests für das Einlesen ergänzt. **Validierungsprotokoll und Testplan** als Vorlage (NFA-11). Neue Abhängigkeit `openpyxl` (Excel). |
