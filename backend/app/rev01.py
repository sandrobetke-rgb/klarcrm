"""Änderungsprotokoll REV01 (Testrückmeldung „REV01 Verbesserungsmaßnahmen CRM“, Nov. 2026).

Wird beim Start in die Tabelle change_requests übernommen (nur fehlende Codes, vorhandene Einträge bleiben
unverändert – Status und Prüfergebnisse aus der Oberfläche werden nie überschrieben).
Felder: code, Bereich, Art (fehler/wunsch/doku), Priorität, Phase, Titel, Anforderung, Status, Umsetzung, Prüfanweisung,
Kapitel-Kürzel (Hinweis). Die Anforderungen selbst stehen im Lastenheft Kap. 13 unter derselben Nummer.
"""

U = "umgesetzt"   # umgesetzt, wartet auf Prüfung durch den Anwender
O = "offen"

ITEMS = [
    # ---------------------------------------------------------------- Fehler (Phase 1)
    ("REV01-B01", "Kalkulation", "fehler", "hoch", 1, "Änderungen in der Kalkulation werden nicht gespeichert / kein Speichern-Knopf sichtbar",
     "Wenn man in einer Kalkulation etwas ändert, wird dieses nicht gespeichert, es gibt auch keinen Button „Speichern“.", U,
     "Ursache: Der Knopf „Als Version n speichern“ stand nur oben in der Versionsleiste und war beim Scrollen nicht mehr zu sehen; "
     "beim Verlassen der Seite gingen Änderungen ohne Warnung verloren. Lösung: Speicherleiste bleibt beim Scrollen oben stehen, "
     "färbt sich bei ungespeicherten Änderungen gelb, Knopf heißt „💾 Speichern (Version n)“, Strg+S speichert, Warnung beim Verlassen.",
     "Kalkulation öffnen, Zykluszeit ändern, nach unten scrollen → Leiste bleibt sichtbar und gelb. Strg+S drücken → neue Version. "
     "Wert ändern und auf „Pipeline“ klicken → Rückfrage erscheint.", "KAL-29"),
    ("REV01-B02", "Kalkulation / Standorte", "fehler", "hoch", 1, "Standortwechsel ändert die Stundensätze nicht",
     "Wenn ich in der Kalkulation die verschiedenen Standorte auswähle, dann ändern sich die Stundensätze nicht.", U,
     "Ursache: Kalkulationen von vor der Standortpflege tragen die Gruppen-Standardsätze; diese wurden als „von Hand eingegeben“ "
     "erkannt und deshalb beibehalten. Außerdem blieb der Maschinenstundensatz gleich, wenn am Zielstandort keine Maschine hinterlegt ist. "
     "Lösung: Ein Satz gilt als Standard, wenn er dem Gruppenwert oder dem Wert irgendeines Standorts entspricht → wird ersetzt. "
     "Wirklich von Hand eingegebene Werte werden angezeigt und lassen sich mit „Alle Sätze des Standorts übernehmen“ ebenfalls ersetzen. "
     "Neuer Standortparameter „Faktor Maschinenstundensatz“ (%) für Standorte ohne eigene Maschinen. "
     "Standort-Matrix: Speichern-Knopf zeigt ungespeicherte Änderungen an (Werte wirken erst nach dem Speichern).",
     "Stammdaten › Standorte: Lohnsatz Bediener eines Standorts auf 30 setzen, Speichern. Kalkulation öffnen, Standort wechseln → "
     "Lohnsatz Bediener zeigt 30. Faktor Maschinenstundensatz 80 % setzen → Maschinenstundensatz sinkt beim Wechsel auf 80 %.", "STM-19, STM-22"),
    ("REV01-B03", "Angebot", "fehler", "hoch", 1, "Aus einer Kalkulation entstehen 2 Angebote, wenn eine neue Version erstellt wird",
     "Es werden aus einer Kalkulation 2 Angebote erstellt, wenn jemand eine neue Version erstellt.", U,
     "„Angebot erstellen / aktualisieren“: Gibt es zur Kalkulation ein offenes Angebot im Entwurf, wird dieses mit der aktuellen Version "
     "aktualisiert (gleiche Nummer). Ist es bereits versendet, entsteht eine Revision (z. B. A26-0001-R1) und das alte Angebot wird „ersetzt“. "
     "Ein zweites eigenständiges Angebot entsteht nicht mehr.",
     "Kalkulation → Angebot erstellen (A26-…). Neue Version speichern → erneut „Angebot erstellen / aktualisieren“ → gleiche Angebotsnummer, "
     "Preis aktualisiert. Angebot auf „versendet“ setzen, neue Version, erneut → Revision -R1, altes Angebot „ersetzt“.", "ANG-12"),
    ("REV01-B04", "Angebot", "fehler", "mittel", 1, "Lieferanten dürfen im Angebot nicht auswählbar sein",
     "Lieferanten dürfen in Angeboten nicht auswählbar sein.", U,
     "Auswahl Firma in Angeboten, Kalkulationen und Verkaufschancen zeigt nur Kunden, Interessenten und Partner. "
     "Das Backend lehnt Angebote an Lieferanten ab.", "Angebot öffnen → Firmenliste enthält keine Firma vom Typ Lieferant.", "ANG-13"),
    ("REV01-B05", "Allgemein", "fehler", "hoch", 1, "Zahlen nur über kleine Pfeile änderbar – freie Eingabe nötig",
     "Man kann die Zahlen nur über die kleinen Pfeile hoch/runter verändern, man muss diese aber frei eingeben können.", U,
     "Alle Zahlenfelder sind jetzt Textfelder mit Zahlenprüfung: freie Eingabe mit Komma oder Punkt (12,5 · 1.250,75), keine Pfeile, "
     "Zwischenstände wie „12,“ bleiben stehen.", "In Kalkulation, Stammdaten und Angebot Werte wie 12,5 und 1.250,75 eintippen → wird übernommen.", "NFA-12"),

    # ---------------------------------------------------------------- Maschinen
    ("REV01-M01", "Stammdaten Maschinen", "wunsch", "hoch", 1, "Maschine in offener Kalkulation nicht löschbar (Warnung)",
     "Maschinen dürfen nicht löschbar sein, wenn diese von einer offenen Kalkulation genutzt werden (Warnung).", U,
     "Löschen prüft alle offenen Kalkulationen (Hauptmaschine und Arbeitsgänge) und verweigert mit Liste der Kalkulationsnummern; "
     "stattdessen deaktivieren.", "Maschine aus einer offenen Kalkulation löschen → Hinweis mit Kalkulationsnummern.", "STM-23"),
    ("REV01-M02", "Stammdaten Maschinen", "wunsch", "mittel", 1, "Bestandsmaschinen und Planmaschinen (nur für Kalkulation) unterscheiden",
     "Unterscheidung zwischen bestehenden Maschinen und Maschinen nur für Kalkulation (Neue Maschinen, Freitext-Maschinen).", U,
     "Neues Feld „Bestand / Planung“: Bestandsmaschine oder Planmaschine/Neuanlage (nur für Kalkulation), in der Liste als Badge sichtbar.",
     "Maschine als Planmaschine anlegen → Badge „Planmaschine“, in der Kalkulation wählbar.", "STM-23"),
    ("REV01-M03", "Stammdaten Maschinen", "wunsch", "mittel", 1, "Löschen nur durch Admin im Vier-Augen-Prinzip",
     "Löschen nur über Workflow durch Admin / 4-Augen-Prinzip.", U,
     "Admin 1 stellt den Löschantrag (Badge „Löschantrag“), ein zweiter Admin bestätigt die Löschung; Antrag kann zurückgezogen werden. "
     "Alles im Protokoll.", "Mit Admin A „Löschen“ → Löschantrag. Mit Admin A erneut → nur Zurückziehen möglich. Mit Admin B → Löschung.", "STM-23"),

    # ---------------------------------------------------------------- Pipeline / Anfrage / Angebot (Phase 2)
    ("REV01-P01", "Pipeline", "wunsch", "hoch", 2, "Pipeline mit allen Anfragen und Potenzialen, Phasen automatisch",
     "Neue Anfrage = Lead (automatisch, vor Freigabe zur Kalkulation); Lead = manuell, potenzielle Neukunden ohne Anfrage; "
     "Qualifiziert = Anfrage zur Kalkulation freigegeben (automatisch); Angebot (automatisch); Verhandlung/technisches Gespräch = Endrunde "
     "(auswerten, wie viele gewonnene/verlorene Projekte in der Endrunde waren); Gewonnen; Verloren mit Pflichtgrund. "
     "Unter „Neue Anfrage“ bei Verkaufschance frei eingeben können.", U,
     'Pipeline-Phasen Lead · Neue Anfrage · Qualifiziert · Angebot · Verhandlung/techn. Gespräch · Gewonnen · Verloren (+ „Nicht angeboten“). Eine Karte je Anfrage. Neue Anfrage → Qualifiziert (Entscheidung „anbieten“) → Angebot (Angebot versendet) laufen automatisch. Verhandlung markiert die Endrunde (Dashboard: gewonnen/verloren aus der Endrunde). „+ Neue Anfrage“ mit freier Eingabe von Projekt, Kunde, Eingang, Abgabetermin.',
     'Pipeline: „+ Neue Anfrage“ anlegen → Karte unter Neue Anfrage. Artikel anlegen, „anbieten“ entscheiden → Karte springt auf Qualifiziert. Angebot versenden → Angebot. Karte auf Verhandlung ziehen → Endrunde.', "PIP"),
    ("REV01-P02", "Anfrage / Artikelanalyse", "wunsch", "hoch", 2, "Entscheidung je Anfrage vor Kalkulationsstart",
     "Jede Anfrage braucht vor Kalkulationsstart eine Entscheidung, bis dahin unter Leads: Artikel wird angeboten · nicht angeboten mit "
     "Begründung · angeboten anderer Standort · Sonstiges (Freitext).", U,
     'Je Artikel Entscheidung vor Kalkulationsstart: anbieten · nicht anbieten (Begründung Pflicht) · anderer Standort (Kalkulation wird mit dessen Sätzen neu angelegt) · Sonstiges (Freitext). Ohne Entscheidung lässt sich keine Version speichern; die Anfrage bleibt unter „Neue Anfrage“. „Alle offenen anbieten“ in der Anfrage.',
     'Neuen Artikel anlegen, Wert ändern, speichern → Hinweis „Entscheidung fehlt“. Entscheidung „anbieten“ → speichern geht. „Nicht anbieten“ ohne Begründung → nicht möglich.', "KAL"),
    ("REV01-P03", "Artikelanalyse", "wunsch", "hoch", 2, "Artikelanalyse vor der Kalkulation, Maschinengröße vorschlagen, „technisches Gespräch erforderlich“",
     "Nach der Analyse Option „technisches Gespräch erforderlich“; Maschinengröße in der Artikelanalyse vorschlagen; Analyse vor Kalkulation. "
     "Vor „Angebot erstellen“ prüfen, ob die Artikelanalyse vollständig ist – sonst Freigabe-Workflow an den Vorgesetzten.", U,
     'Artikelanalyse ist Reiter 1 vor der Kalkulation, mit Vorschlag Maschinengröße (Schließkraftklasse und kleinste vorhandene Maschine) und Haken „technisches Gespräch erforderlich“ (markiert die Anfrage, legt Aufgabe an). Unvollständige Analyse (offene Prüfpunkte oder keine Machbarkeit) ist Freigabegrund – Angebot erst nach Freigabe durch den Vorgesetzten.',
     'Artikelanalyse mit offenen Prüfpunkten speichern → Freigabeleiste „Artikelanalyse unvollständig“. Angebot erstellen → Hinweis Freigabe erforderlich. Haken techn. Gespräch → Badge in der Anfrage + Aufgabe.', "ANA"),
    ("REV01-P04", "Angebot", "wunsch", "hoch", 2, "Angebotskopf mit n Kalkulationen (Angebotserstellung)",
     "Angebotskopf mit Kunde und Ansprechpartner, darunter n Kalkulationen/Artikel. Erst Kopf anlegen, dann Kalkulationen darunter; "
     "weitere Kalkulationen im Angebot wählen. Eine Anfrage × Kalkulationen. Angebotsliste mit Status und letzter Rückmeldung/Anruf.", U,
     'Neuer Menüpunkt „Anfragen“: Anfrage (AF26-0001) mit Kunde, Ansprechpartner, Eingang, Abgabetermin; darunter n Artikel/Kalkulationen und genau ein Angebot mit n Positionen (Revisionen -R1). Schrittleiste zeigt den Stand. Angebotsliste mit Status, Verfolgungsampel und letzter Rückmeldung. Bestehende Kalkulationen wurden nach Angebot gruppiert übernommen.',
     'Anfrage mit zwei Artikeln anlegen, beide entscheiden, Angebot erstellen → ein Angebot mit Pos. 1 und 2. Angebote-Liste: Spalten Verfolgung und letzte Rückmeldung.', "ANG"),
    ("REV01-P05", "Pipeline / Kalkulation", "wunsch", "hoch", 1, "Verloren nur mit Pflichtgrund (Vorauswahl + Freitext)",
     "Wenn etwas verloren geht und wir es in der Pipeline verschieben, muss immer zwingend der Grund rein. Vorauswahl: Werkzeug zu teuer, "
     "Preis zu teuer, Projekt eingestellt, Kunde hat Projekt nicht erhalten, Vorrichtung zu teuer, Sonstiges (Freitext).", U,
     "Pipeline: Ziehen auf „Verloren“ öffnet Pflichtdialog mit Vorauswahl, bei „Sonstiges“ Freitext Pflicht. Kalkulation: Status „Verloren“ "
     "nur mit Grund (Backend prüft), neues Feld „Begründung Verlust“. Liste der Gründe angepasst (Vorrichtung zu teuer neu).",
     "Karte in der Pipeline auf „Verloren“ ziehen → Dialog; ohne Grund nicht möglich. Kalkulation auf Verloren ohne Grund → Fehlermeldung.", "PIP-6, KAL-30"),
    ("REV01-P06", "Aufgaben", "wunsch", "hoch", 2, "Automatische Angebotsverfolgung mit Ampel",
     "Automatische Aufgabe „Angebotsverfolgung“: Rücksprache Kunde spätestens 5 Tage nach Angebot, mit Ampel. Bei Status „versendet“ startet "
     "der Timer mit Erinnerung. Ohne Reaktion rot, sichtbar für alle inkl. Gesellschafter. „Niemanden erreicht“ → Aufgabe kommt am nächsten "
     "Tag wieder, außer „wieder melden am …“.", U,
     'Status „versendet“ startet die Aufgabe „Angebotsverfolgung“ mit Frist 5 Arbeitstage (Parameter). Ampel grün/gelb/rot auf Dashboard (für alle sichtbar inkl. Gesellschafter), in Anfrage, Angebot, Angebotsliste und Aktivitäten. Rücksprache erfassen: erreicht · niemanden erreicht (Wiedervorlage nächster Arbeitstag, Zähler) · wieder melden am …',
     'Angebot auf versendet → Hinweis mit Rücksprachetermin. Dashboard › Angebotsverfolgung → „Rücksprache“ → „Niemanden erreicht“ → Fälligkeit nächster Arbeitstag, gelb.', "AKT"),
    ("REV01-P07", "Aktivitäten", "wunsch", "mittel", 2, "Aktivität mit Angebot verknüpfen bzw. aus dem Angebot anlegen",
     "Verlinkung zu einem Angebot oder aus dem Angebot heraus eine Aktivität erstellen.", U,
     'Aktivitäten haben ein Feld „Angebot“; im Angebot Bereich „Aktivitäten zum Angebot“ mit „+ Aktivität“; Anfrage zeigt alle Aktivitäten.',
     'Angebot öffnen → „+ Aktivität“ → erscheint im Angebot und in der Anfrage.', "AKT"),
    ("REV01-P08", "Angebotsdruck", "wunsch", "hoch", 2, "Positionsstruktur und Staffelpreise je Lieferjahr in einer Spalte",
     "Staffelpreise in einer Spalte: Jahr 1, Jahr 2 … inkl. Jahresmenge × Preis. Positionen: Pos 1 Artikel, 1.1 Werkzeug, 1.2 Sonstiges, "
     "1.3 CO₂-Fußabdruck (wenn ausgewählt), Pos 2 nächster Artikel usw.", U,
     'Angebotspositionen: 1 Artikel mit Serienpreis je Lieferjahr (Jahresmenge × Stückpreis = Betrag) · 1.1 Werkzeug · 1.x Vorserie · 1.x Sonstiges · letzte Unterposition CO₂-Fußabdruck (nur Information, ohne Preis) · 2 nächster Artikel. Positionsnummer im Angebot änderbar.',
     'Angebot zu einem Artikel mit Werkzeug und CO₂ erstellen → Druckansicht prüfen.', "ANG"),
    ("REV01-P09", "Wahrscheinlichkeit", "wunsch", "mittel", 2, "Wahrscheinlichkeit = Auftrag kommt insgesamt, keine Umsatzgewichtung",
     "Wahrscheinlichkeit bedeutet die Wahrscheinlichkeit, dass der gesamte Auftrag kommt; die gewichtete Minderung des Umsatzes ist nicht sinnvoll.", U,
     'Wahrscheinlichkeit = Auftrag kommt insgesamt; gilt für alle Artikel der Anfrage. Keine gewichteten Summen mehr in Pipeline und Dashboard (stattdessen „davon ≥ 50 % Wahrscheinlichkeit“).',
     'Pipeline und Dashboard: keine „gewichtet“-Angaben mehr.', "KAL"),

    ("REV01-X03", "Änderungswünsche", "fehler", "hoch", 2, "Neue Änderungswünsche speichern, Art und Bereich frei eingeben",
     "Wichtig ist, wenn ich neue Änderungen im Änderungsantrag eingebe, dass diese auch gespeichert werden können und ich auch einen "
     "Freitext auswählen kann für die Art etc.", U,
     "Nach dem Speichern erscheint eine Bestätigung mit Nummer (WUN-0001 …); blendet ein aktiver Filter den neuen Eintrag aus, wird das "
     "angezeigt und lässt sich mit „Filter zurücksetzen“ aufheben. Art und Bereich: Vorschlagsliste mit freier Eingabe.",
     "Änderungswünsche › Kachel „Umgesetzt“ anklicken (Filter) → „+ Änderungswunsch“ mit Art „Schulung“ (frei) speichern → Meldung „angelegt“, Hinweis auf Filter.", "DOK"),

    ("PRL-01", "Preisliste", "wunsch", "hoch", 3, "Lebende VK-Preisliste mit Materialpreisänderung, Kennzeichnung und monatlichem Import",
     "Preisliste ins CRM einbauen: alle VK-Artikel inkl. Material erfassen, lebendes Dokument, Import, Filter nach Kunden. Neue "
     "Materialpreise eingeben → betroffene Artikel sehen und kennzeichnen, ob weitergegeben. Einmal im Monat Import der Preise mit "
     "Prüfung, wo sich Preise verändert haben, Historie und Markierung: an Kunden weitergegeben / trotz Erhöhung nicht weitergegeben, "
     "weil vertraglich gebunden / Sonstiges (Freitext).", U,
     "Menü Preisliste: Artikel je Kunde (Material 1–n mit Gewicht und Preisbasis, Zukaufteile, Planmenge, Preisbindung/Vertrag), Filter "
     "Kunde/Material/Preisbindung/offene Differenz, Export Excel. Materialpreise: „Neuer Preis“ mit Sofort-Vorschau der betroffenen "
     "Artikel (Δ je PE, neuer Preis, Jahreseffekt) → Vorgang PA26-…; je Artikel kennzeichnen (einzeln oder mehrere). Import Preisliste "
     "(F&R-Vorlage erkannt) und Import Materialpreise mit Vorschau; Historie je Artikel und Material.",
     "Preisliste › Materialpreise › PP „Neuer Preis“ 1,95 → Liste prüfen → Übernehmen → im Vorgang zwei Artikel „vertraglich gebunden“, "
     "einen „weitergegeben“ → Artikel zeigt neuen Preis und Historie. Import der Vorlage mit drei Zeilen.", "Kap. 14"),
    ("PRL-02", "Preisliste", "wunsch", "mittel", 3, "Jährliche Preisrunde je Kunde („Annual Price Inquiry List“) aus der Preisliste erzeugen",
     "Aus den gespeicherten Artikeln je Kunde die Jahrespreisliste füllen (Materialdifferenz, NK-Zuschlag, Ratio, Zukaufteile, "
     "Jahreseffekte) und als Excel zum Versand ausgeben; vorgemerkt für das nächste große Update.", O, None, None, "Kap. 14"),

    # ---------------------------------------------------------------- Kalkulation (Phase 3)
    ("REV01-C01", "Zukaufteile", "wunsch", "hoch", 3, "Zukaufteile: Stück je Bauteil, Freitext, Lieferant, Staffelmengen mit Jahresbedarf",
     "Stück je Bauteil (z. B. 4 Buchsen); Freitext-Name, Lieferant, bis zu n Staffelmengen mit Berechnung der benötigten Mengen pro Jahr.", O, None, None, "KAL"),
    ("REV01-C02", "Mengen", "wunsch", "hoch", 3, "Mengen je Lieferjahr mit Stunden und Materialbedarf",
     "Mengen Jahr 1 / Jahr 2 … mit Stunden und Materialbedarf; Jahres- und Projektübersicht Umsatz aus den Mengen.", O, None, None, "KAL"),
    ("REV01-C03", "Material", "wunsch", "hoch", 3, "Material als Freitext (auch Masterbatch) mit Staffelpreisen und Einkaufsmengen-Vorschlag",
     "Material-Freitext (auch Masterbatch), automatisch in Stammdaten speichern, Lieferant, Angebotsnummer, Staffelpreise inkl. Vorschlag "
     "der Einkaufsmenge pro Jahr.", O, None, None, "KAL"),
    ("REV01-C04", "Losgröße", "wunsch", "mittel", 3, "Vorschlag optimale Losgröße = Jahresmenge / 12 (außer erstes Serienjahr)",
     "Optimale Losgröße vorschlagen = Jahresmenge/12, außer im ersten Serienjahr (manuell). Verpackungsimport?", O, None, None, "KAL"),
    ("REV01-C05", "Serienpreis", "wunsch", "mittel", 3, "Serienpreis je Lieferjahr: 5 Jahre Standard, weitere ergänzbar",
     "Serienpreis je Lieferjahr: standardmäßig 5, weitere hinzufügbar.", O, None, None, "KAL"),
    ("REV01-C06", "Werkzeug", "wunsch", "hoch", 3, "Werkzeug: Lieferzeit FOT, PPAP, SOP ins Angebot; Werkzeugblatt je Artikel",
     "Lieferzeit FOT, PPAP, SOP müssen ins Angebot. Ein Werkzeugblatt je Artikel (Konstruktion/CNC, Abmustern/Prüfbericht, Druck-/Temperaturfühler, "
     "Heißkanal, Werkzeugkosten extern, Angebotspreis, Baumuster/EMPB/PPAP in Wochen, Werkzeugstandzeit, Vergleich Werkzeugangebote WZB 1–4).",
     O, None, None, "KAL"),
    ("REV01-C07", "Kalkulation", "wunsch", "mittel", 3, "Kalkulation duplizieren mit geänderter Fachzahl",
     "Kalkulation duplizieren, z. B. 4-fach statt 2-fach Werkzeug → Zuhaltung, Werkzeugkosten, Fachzahl ändern sich.", O,
     "Teilweise vorhanden: Knopf „Kopieren“ in der Kalkulation. Geführter Dialog „Variante mit anderer Fachzahl“ folgt.", None, "KAL"),
    ("REV01-C08", "Risikoanalyse", "wunsch", "hoch", 3, "Risikoanalyse zu jedem Bauteil",
     "Projekt-Risikoklassifikation mit 13 Fragen (neuer Kunde, neues Produkt, neues Material, neue Anlagen, neue Technologie, Automatisierung, "
     "Lieferschwierigkeiten, Qualitätsprobleme, neuer Lieferant Zukaufteile, Vertragsbasis, Designänderungen, Source Change, Invest > 10.000 €) "
     "und Einstufung hoch > 60 % / mittel 35–60 % / niedrig < 35 %; Klassifizierung Fertigungsprozess und Lieferkette.", O, None, None, "KAL"),
    ("REV01-C09", "Anlagen", "wunsch", "mittel", 3, "Blatt Stundensatz für zusätzliche Anlagen (noch nicht vorhanden)",
     "Kalkulationsblatt für neue/zusätzliche Anlagen: Zeit je Stück, Verfügbarkeit, Nutzungsdauer, Invest extern/F&R, Abschreibung, Finanzierung, "
     "Betriebskosten, Instandhaltung, Overhead-Zuschlag, Gesamt-Stundensatz, Prüfung Kapazitäten (Liquidität, Fläche, Personal).", O, None, None, "STM"),
    ("REV01-C10", "Kickoff", "wunsch", "mittel", 3, "Kickoff automatisch aus allen Daten bei Auftragsbestätigung",
     "Kickoff automatisch aus allen Daten erzeugen, wenn der Mitarbeiter den Auftrag bestätigt.", O, None, None, "KAL"),

    # ---------------------------------------------------------------- Beschaffung
    ("REV01-E01", "Beschaffung", "wunsch", "mittel", 4, "Beschaffung für Material, Zukaufteile, Verpackung … mit Staffeln, Bezug zur Kalkulationsnummer",
     "Auch Material und Zukaufteile mit 1–n Staffelmengen/Preisen; Bezug zu einer Kalkulationsnummer; Werkzeugangebote der Lieferanten "
     "zum Vergleich ablegen; Lieferantenanfragen für Werkzeuge, Rohmaterial, Zubehörteile, Verpackung (je in Staffeln), Vorrichtungen, "
     "Montageanlagen, Prüfmittel, Kameras, Laser, Sonstiges.", O,
     "Teilweise vorhanden: Beschaffung für Werkzeuge/Montagelinien/Vorrichtungen/Prüfmittel mit Bezug zur Kalkulation.", None, "BES"),

    # ---------------------------------------------------------------- Stammdaten / Standorte / Einheiten
    ("REV01-S01", "Firmen", "wunsch", "niedrig", 1, "Branchen als Vorauswahl mit Freitext",
     "Branchen vorgeben mit Freitext: Automotive, Energie & Batterie, Wasser & Sanitär, Heizung, Lüftung & Klima, Automatisierung & "
     "Elektrotechnik, Rüstung, Drohnentechnik, Smart Home, Sonstiges.", U,
     "Feld Branche mit Vorschlagsliste, eigene Eingabe weiterhin möglich.", "Firma bearbeiten → Branche: Liste erscheint, eigener Text möglich.", "FIR-2"),
    ("REV01-K01", "Auslastung", "wunsch", "mittel", 1, "Kapazität je Anlage über Schichtmodell",
     "Max. Stunden je Anlage über Schichten wählbar: 3 Schichten 24 h × 240 Tage, 2 Schichten 16 h × 240, 1 Schicht 8 h × 240.", U,
     "Feld „Schichtmodell“ je Maschine: setzt verfügbare Stunden automatisch (1.920 / 3.840 / 5.760 h).",
     "Maschine bearbeiten → 2 Schichten → verfügbare Stunden 3.840.", "AUS-7"),
    ("REV01-K02", "Auslastung", "doku", "niedrig", 1, "Erklären: wann ist die Auslastung „zu fest“ / zu voll",
     "Wann wird die Auslastung zu fest?", U,
     "Seitenhilfe Auslastung erklärt: Fest = Bestand + gewonnen; Erwartet = + offene × Wahrscheinlichkeit; Maximal = + alle offenen. "
     "Ampel: < 60 % frei, 60–85 % gut, 85–100 % knapp, ≥ 100 % überlastet.", "Auslastung öffnen → Hilfe oben lesen.", "AUS-1"),
    ("REV01-U01", "Einheiten", "wunsch", "niedrig", 1, "Rüstzeit in Minuten statt Stunden",
     "Rüstzeit je Los in h, aber Einrichterzeit in min → alles auf Minuten.", U,
     "Rüstzeit je Los und Rüstzeit Vorserie werden in Minuten eingegeben und angezeigt (Kalkulation, Parameter, Standorte); "
     "intern weiter in Stunden gespeichert – bestehende Kalkulationen bleiben unverändert.",
     "Kalkulation → Rüstzeit zeigt z. B. 120 min statt 2 h.", "KAL-31"),
    ("REV01-N01", "Nummernkreise", "wunsch", "mittel", 1, "Sprechende Nummern A26-0001 und K26-0001",
     "Sprechende Nummern: Angebote A26-0001, Kalkulationen K26-0001 (Jahr vorangestellt).", U,
     "Neue Angebote A26-0001 (Revisionen -R1), neue Kalkulationen K26-0001, Beschaffungsanfragen B26-0001. Bestehende Nummern bleiben.",
     "Neue Kalkulation und neues Angebot anlegen → Nummern im neuen Format.", "NFA-13"),
    ("REV01-F01", "Freigabe", "wunsch", "hoch", 1, "Freigabe-Workflow ab 250.000 € Invest oder Umsatz",
     "Workflow für Angebote mit Invest > 250.000 € / Umsatz > 250.000 € (aktuell 500.000 €).", U,
     "Grenzwerte Großprojekt/Freigabe auf 250.000 € gesetzt (Parameter, bestehende Installationen werden einmalig umgestellt, "
     "sofern dort noch 500.000 € stand).", "Stammdaten › Parameter › Großprojekte: 250.000 €.", "KAL-20"),

    # ---------------------------------------------------------------- Dashboard / Berichte (Phase 4)
    ("REV01-D01", "Dashboard", "wunsch", "mittel", 1, "Kachel „Offene Angebote und Anfragen / Kalkulationen offen“ missverständlich",
     "„Offene Angebote und Anfragen / Kalkulationen offen“ ist missverständlich.", U,
     "Getrennt in „Anfragen in Bearbeitung“ (noch ohne Angebot) und „Angebote beim Kunden“ – auf Dashboard und Kalkulationsseite.",
     "Dashboard ansehen.", "DAS-1"),
    ("REV01-D02", "Dashboard", "fehler", "mittel", 1, "Großprojekte-Kachel führt zu allen Anfragen",
     "Die Großprojekte-Kachel führt zu allen Anfragen, sie soll nur Großprojekte zeigen.", U,
     "Kachel öffnet die Kalkulationsliste mit Filter „nur Großprojekte“.", "Kachel anklicken → Filter Großprojekte gesetzt.", "DAS-1"),
    ("REV01-D03", "Dashboard", "wunsch", "mittel", 1, "Gewinnquote anklickbar – Übersicht gewonnen/verloren",
     "Gewinnquote nicht anklickbar, es fehlt eine Übersicht gewonnen/verloren.", U,
     "Gewinnquote führt zu Auswertungen; Kacheln Gewonnen/Verloren auf der Kalkulationsseite öffnen die gefilterte Liste.",
     "Gewinnquote anklicken → Auswertungen.", "DAS-1"),
    ("REV01-D04", "Dashboard", "wunsch", "niedrig", 1, "Trefferquote Kalkulation entfernen",
     "Trefferquote Kalkulation kann raus.", U, "Kachel entfernt (Dashboard und Kalkulationsseite).", "Dashboard ansehen.", "DAS-1"),
    ("REV01-D05", "Dashboard", "wunsch", "mittel", 3, "Vertriebsziel des Jahres mit Erreichung in % und Ampel",
     "Vertriebsziel des Jahres, erreichte % und Ampel anzeigen.", U,
     "Vertriebsziele (Neuumsatz, gesamt und je Vertriebler, optional Werkzeug/Einmal) im Monatsbericht pflegen; Startseite zeigt "
     "erreicht in % mit Ampel (Soll anteilig bis heute) und führt zum Monatsbericht.", "Ziel 2,5 Mio. € anlegen → Startseite Kachel „Vertriebsziel“.", "Kap. 15"),
    ("REV01-R01", "Berichte", "wunsch", "mittel", 3, "Vertriebsbericht für Zeitraum, Durchlaufzeit Anfrage → Angebot, Anzahl kalkulierter Artikel",
     "Schöner Vertriebsbericht für einen gewählten Zeitraum; Durchlaufzeit Anfrage → Angebot messen, Ziel in Parametern (10 Arbeitstage); "
     "Anzahl kalkulierter Artikel anzeigen.", U,
     "Als Monatsbericht umgesetzt (Kap. 15): Durchlaufzeit Anfrage → Angebot gegen Ziel 10 AT, kalkulierte Artikel, gewonnen/verloren, "
     "offene Pipeline, Handlungsbedarf, Auslastung; als PDF druckbar.", "Monatsbericht November öffnen → Kennzahlen prüfen.", "Kap. 15"),
    ("MB-01", "Berichte", "wunsch", "hoch", 3, "Monatsbericht Vertrieb für die Gesellschafter (PDF) mit Neuumsatz gegen Jahresziel",
     "Monatlicher Bericht statt Besprechung: wie lief der Monat, was ist offen, was fehlt, was wurde verloren, was seit Jahresbeginn "
     "gewonnen; Ziel = Neuumsatz (Umsatz des stärksten Lieferjahres) und wie viel davon erreicht ist; Auslastung im Folgejahr aus "
     "gewonnenen Projekten je Maschine. Kein Vorjahresvergleich. Versand macht die GF selbst.", U,
     "Menü Monatsbericht: Live-Stand oder gespeicherter Stand je Monat, Freigabe, Kommentar der GF, Drucken/PDF; Vertriebsziele je Jahr.",
     "November 2026 → Kommentar → Stand speichern → Freigeben → Drucken / PDF.", "Kap. 15"),
    ("MB-02", "Angebote", "wunsch", "hoch", 3, "Teilbeauftragung: von n angebotenen Artikeln/Varianten werden nur einige Auftrag",
     "Angebot mit 10 Artikeln oder Varianten, 2 werden Auftrag: diese auswählen, beim Rest „verloren“ wählen können. "
     "Nicht beauftragte Variante zählt nicht als Verlust.", U,
     "„Auftrag erhalten …“ am Angebot: beauftragte anhaken, Vorgabe für den Rest (verloren mit Grund / andere Variante / noch offen), "
     "Status „teilweise beauftragt“; nur beauftragte Artikel im Neuumsatz; Varianten nicht in Verlustquote.",
     "Angebot mit 5 Artikeln → 2 anhaken, 1 andere Variante, 1 verloren (Preis), 1 offen → Monatsbericht prüfen.", "Kap. 15.4"),

    # ---------------------------------------------------------------- Dokumentation
    ("REV01-X01", "Dokumentation", "doku", "hoch", 1, "Änderungsprotokoll zum Eintragen und Abarbeiten der Wünsche",
     "Ich kann das Protokoll nicht finden, wo ich diese gewünschten Änderungen eintragen könnte, damit ich diese sauber abarbeiten und prüfen kann.",
     U, "Neue Seite „Änderungen“ (Menü): alle REV01-Punkte mit Status, Umsetzung, Prüfanweisung und Prüfergebnis; neue Wünsche selbst "
     "eintragen; Export als CSV.", "Menü › Änderungen öffnen, Punkt anklicken, Prüfergebnis eintragen, Status „geprüft“ setzen.", "DOK-1"),
    ("REV01-X02", "Dokumentation", "doku", "hoch", 1, "Beschreibung und Lastenheft in Word und im Frontend",
     "Bitte für alles eine Beschreibung und ein Lastenheft erstellen, einmal in Word, aber auch auf dem Frontend zu finden.", U,
     "Seite „Dokumentation“ zeigt Lastenheft und Benutzerbeschreibung im Programm; Download als Word-Datei (.docx) direkt dort.",
     "Menü › Dokumentation → Lastenheft lesen, „Als Word herunterladen“.", "DOK-2"),
]


def seed_rev01(db) -> int:
    from .models import ChangeRequest  # noqa: PLC0415
    have = {c for (c,) in db.query(ChangeRequest.code).all()}
    n = 0
    # Neu umgesetzte Punkte nachziehen – nur wenn der Eintrag noch unbearbeitet „offen“ ist (Prüfstand bleibt unangetastet)
    for code, area, kind, prio, phase, title, desc, status, solution, test, req in ITEMS:
        if code in have and status == U:
            cr = db.query(ChangeRequest).filter(ChangeRequest.code == code).first()
            if cr and cr.status == "offen" and not (cr.test_result or "").strip():
                cr.status, cr.solution, cr.test_steps = U, solution, test
                cr.version = "1.24" if phase == 2 else "1.23"
    for code, area, kind, prio, phase, title, desc, status, solution, test, req in ITEMS:
        if code in have:
            continue
        db.add(ChangeRequest(code=code, revision="REV01" if code.startswith("REV01") else "Wunsch", area=area, kind=kind, priority=prio, phase=phase, title=title,
                             description=desc, status=status, solution=solution, test_steps=test,
                             req_ids=f"Lastenheft Kap. 13 · {code}",
                             version=("1.24" if phase == 2 else "1.23") if status == U else None,
                             requested_by="Sandro (REV01)"))
        n += 1
    db.commit()
    return n
