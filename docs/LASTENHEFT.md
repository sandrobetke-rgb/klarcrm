# Lastenheft KlarCRM

| | |
|---|---|
| **Projekt** | KlarCRM – schlankes CRM mit Spritzguss-Kalkulation |
| **Auftraggeber** | Friedrichs & Rath (F&R), Geschäftsführung |
| **Dokumentversion** | 1.6 |
| **Stand** | 14.11.2026 |
| **Status** | Testphase (GitHub Codespaces) |

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
| ROL-1 | Administrator | Alles inkl. Benutzerverwaltung und Kalkulations-Parameter (Standardsätze) |
| ROL-2 | Vertrieb | Alle Daten sehen, anlegen, ändern, löschen; Stammdaten Maschinen/Materialien pflegen |
| ROL-3 | Gesellschafter | Alles sehen (Dashboard, Pipeline, Kalkulationen, Nachkalkulation), **nichts ändern** |

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
  **Instandhaltung €/h**, **Standard-Produktivität %**, **Standard-Bedienfaktor** (Personen je Maschine), aktiv/inaktiv.
- STM-2: Bei Auswahl einer Maschine in der Kalkulation werden Stundensatz, Instandhaltung, Produktivität und
  Bedienfaktor sofort übernommen und der Preis neu berechnet.
- STM-13: Je Maschine zusätzlich: **verfügbare Stunden/Jahr** (Schichtmodell, Standard 6.000 h), **Grundauslastung
  aus Bestandsaufträgen %** und **Auslauf des Bestands % je Jahr** – Basis der Auslastungsvorschau (Kap. 6.7).
- STM-3: Inaktive Maschinen sind in neuen Kalkulationen nicht auswählbar; bestehende Kalkulationen bleiben unverändert.

### 5.2 Materialien
- STM-4: Je Material: Bezeichnung, Werkstoffgruppe, Lieferant, **Preis €/kg**, Dichte, aktiv/inaktiv.
- STM-5: Bei Auswahl wird der Materialpreis übernommen (überschreibbar).

### 5.3 Parameter (Standardwerte)
- STM-6: Lohnsätze Bediener, Einrichter, Montage (€/h).
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
| Material | Material (Stammdaten), Preis €/kg, Teilgewicht g, Anguss je Schuss g, Mahlgut-Rückführung %, Masterbatch-Anteil % und -Preis, Zukaufteile €/Stk |
| Maschine & Fertigung | Maschine (Stammdaten), Maschinenstundensatz €/h, Instandhaltung €/h, **Zykluszeit s**, **Fachzahl**, **Produktivität %**, Bedienfaktor, Lohnsatz Bediener |
| Rüsten | Rüstzeit je Los h, Einrichter, Lohnsatz Einrichter, Anfahrausschuss je Los Stk |
| Montage | Montagezeit je Stück s, Personen, Lohnsatz, Produktivität Montage % |
| Zuschläge | MGK, FGK, Ausschuss, Verwaltung, Vertrieb, Projektmanagement, **Qualität**, **Werkzeugbau**, Gewinn, Skonto, Rabatt (%); für Qualität und Werkzeugbau ist die **Basis wählbar**: FEK oder HK |
| **Verpackung** | Verpackungsart (Vorschläge KLT, Karton, Gitterbox, Sonderladungsträger …), Teile je Verpackungseinheit (VE), Kosten je VE bzw. bei Mehrweg je Umlauf (Reinigung, Miete), Packzeit je VE, VE je Palette – **echte Beträge, keine Prozente** |
| **Transport** | Lieferbedingung (Incoterm, frei wählbar), Art: keine (ab Werk) · € je Palette · € je Lieferung (mit Lieferungen p. a.) · % auf Herstellkosten |
| Zusatzpositionen | frei: Bezeichnung, Betrag, Bezug (je Stück / je 1.000 / je Los / je Jahr), Art (Fertigung oder Vertrieb) – z. B. Peripherie, Nacharbeit, Bedrucken, Sonderkosten |
| Einmalkosten | frei: Bezeichnung, Kosten, Preis an Kunde – z. B. Werkzeug, Erstbemusterung, Prüfmittel |
| Verkaufspreis | optional manuell festgelegt (Gewinn ergibt sich dann als Rest) |

**Rechenweg je Stück** (KAL-21)

| Schritt | Formel |
|---|---|
| Ausbringung | Stück/h = 3600 / Zykluszeit × Fachzahl × Produktivität |
| Material (MEK) | (Teilgewicht + Anguss/Fachzahl × (1 − Mahlgut %)) / 1000 × Mischpreis €/kg + Zukaufteile; Mischpreis = Materialpreis × (1 − MB %) + MB-Preis × MB % |
| MGK | MEK × MGK % |
| Maschine | Maschinenstundensatz / Stück/h |
| Instandhaltung | Instandhaltung €/h / Stück/h |
| Personal | Lohnsatz × Bedienfaktor / Stück/h |
| Rüsten | [Rüstzeit × (Maschinensatz + Instandhaltung + Lohnsatz Einrichter × Einrichter) + Anfahrausschuss × (Material + Maschine + Instandhaltung + Personal je Stück)] / Losgröße |
| Montage | Montagezeit/3600 × Lohnsatz × Personen / Produktivität Montage |
| FEK | Maschine + Instandhaltung + Personal + Rüsten + Montage |
| FGK | FEK × FGK % |
| Qualität / Werkzeugbau (Basis FEK) | FEK × Qualität % bzw. FEK × Werkzeugbau % – Teil der Herstellkosten (vor Ausschuss) |
| SEK Fertigung | Zusatzpositionen „Fertigung“ |
| HK vor Ausschuss | MEK + MGK + FEK + FGK + Qualität/Werkzeugbau (Basis FEK) + SEK Fertigung |
| Ausschuss | HK vor Ausschuss / (1 − Ausschuss %) − HK vor Ausschuss |
| Herstellkosten | HK vor Ausschuss + Ausschuss |
| Verwaltung / Vertrieb / PM | je HK × % |
| Qualität / Werkzeugbau (Basis HK) | HK × Qualität % bzw. HK × Werkzeugbau % |
| Verpackung | Kosten je VE / Teile je VE + Packzeit je VE / 3600 × Lohnsatz Bediener / Teile je VE |
| Transport | je Palette: Fracht je Palette / (Teile je VE × VE je Palette) · je Lieferung: Kosten je Lieferung × Lieferungen p. a. / Jahresmenge · Prozent: HK × % · ab Werk: 0 |
| SEK Vertrieb | Zusatzpositionen „Vertrieb“ |
| Selbstkosten | HK + Verwaltung + Vertrieb + PM + Qualität/Werkzeugbau (Basis HK) + Verpackung + Transport + SEK Vertrieb |
| Gewinn | SK × Gewinn % (bzw. Rest bei manuellem Preis) |
| Verkaufspreis | (SK + Gewinn) / (1 − Skonto) / (1 − Rabatt) |

- KAL-28: **Staffelpreise**: bis zu 3 weitere Losgrößen je Kalkulation (Vorschlag ½×, 2×, 5× der Basis-Losgröße).
  Je Staffel: Rüstkosten je Stück, Preis je Stück und je 1.000, Δ % zum kalkulierten Preis der Basis-Losgröße.
  Staffeln werden immer kalkuliert (ein manuell festgelegter Preis gilt nur für die Basis-Losgröße). Staffelpreise
  werden in die Artikelposition des Angebots übernommen.
- KAL-29: Ausgaben Verpackung/Transport: Kosten je Stück und p. a., VE p. a., Stück je Palette, Paletten p. a.
  Verpackungsart, Teile je VE und Lieferbedingung werden in die Artikelposition des Angebots übernommen.
  Ältere Versionen ohne diese Angaben rechnen unverändert (Verpackung bisher über Zusatzpositionen).
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
- AUS-5: Farbstufen < 60 %, 60–85 %, 85–100 %, ≥ 100 % (mit Warnsymbol); Aufklappen je Maschine zeigt die
  beteiligten Kalkulationen mit Stunden je Jahr; Gesamtzeile; KPI „Auslastung Folgejahr“ im Dashboard.

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

## 8. Nicht-funktionale Anforderungen
- NFA-1: Web-Anwendung (Desktop und Tablet), deutschsprachig, Zahlen im deutschen Format.
- NFA-2: Selbst gehostet (Docker), keine Lizenzkosten je Nutzer; Daten bleiben auf eigenem Server (DSGVO).
- NFA-3: Anmeldung per E-Mail/Passwort, Passwörter mit bcrypt gehasht, Sitzungen per Token (12 h).
- NFA-4: Betrieb hinter HTTPS-Reverse-Proxy; tägliches Datenbank-Backup.
- NFA-5: Automatischer Build- und Starttest bei jedem Push (GitHub Actions).
- NFA-6: API vollständig dokumentiert (Swagger unter /docs).
- NFA-8: Datenbank-Erweiterungen werden beim Start automatisch ergänzt (neue Tabellen und neue Spalten in bestehenden
  Tabellen); Umbenennen/Löschen von Spalten bleibt ein manueller Schritt.
- NFA-7: Fußzeile auf allen Seiten inkl. Anmeldung: „© <Jahr> SB/Thinkworks · KlarCRM · built with clarity“ (nicht im Druck).

## 9. Technik
- Backend: Python FastAPI, SQLAlchemy, PostgreSQL 16; Rechenkern in `backend/app/calc_engine.py`.
- Frontend: React 18 (Vite), Auslieferung über nginx.
- Testumgebung: GitHub Codespaces (Demo-Daten, Logins siehe README).

## 10. Abgrenzung / noch nicht umgesetzt
- Kein E-Mail-Versand von Angeboten aus dem System.
- Kein Import aus ERP/BDE; Ist-Werte der Nachkalkulation werden manuell erfasst.
- Keine Mehrwährung; Euro.
- Keine vollwertigen Datenbank-Migrationen (Alembic) – nur additive automatische Ergänzung (NFA-8).

## 11. Offene Punkte / Ideen für die finale Version
- [ ] Abgleich des Kalkulationsschemas mit der bestehenden F&R-Excel-Kalkulation (Positionen, Zuschlagsbasen).
- [x] Staffelpreise je Losgröße (v1.4). Offen: Staffeln nach Jahresmenge.
- [ ] Werkzeugamortisation über Stückzahl als Option.
- [ ] Mehrere Artikel je Anfrage in einer Kalkulationsmappe.
- [ ] Übernahme von Ist-Werten aus BDE/MES für die Nachkalkulation.
- [ ] CSV-/Excel-Import und -Export (Firmen, Kontakte, Kalkulationsliste).
- [ ] Wiedervorlage-Automatik ohne manuelles Datum (Aufgabe, wenn > 14 Tage kein Anruf).
- [ ] Zuschlagsbasis für weitere Zuschläge wählbar machen, falls die F&R-Excel-Kalkulation das erfordert.
- [ ] Rechte: Kalkulation nur für bestimmte Rollen sichtbar machen (z. B. Gewinnsätze).

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
