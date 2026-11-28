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

    # ---------------------------------------------------------------- REV02: Testrunde Phase 2 (23.11.2026)
    ("REV02-01", "Freigabe", "wunsch", "hoch", 2, "Freigabe nur noch ab Umsatz 500 T€ oder Invest 350 T€ – sonst rote Markierung",
     "Freigabe so streng macht Unmut und Mehrarbeit: nur noch bei Teileumsatz > 500.000 € und Invest > 350.000 €; was fehlt, nur rot "
     "markieren (Test REV01-P03, P06 und P08 waren wegen der Freigabe nicht prüfbar).", U,
     "Freigabegründe nur noch Jahresumsatz ≥ 500 T€ und Invest ≥ 350 T€ (Parameter, bestehende Einstellung 250 T€ wird einmalig "
     "umgestellt). Unvollständige Artikelanalyse, fehlende Entscheidung und Marge unter Grenze sperren nicht mehr, sondern stehen rot "
     "unter „Noch offen“ in Kalkulation und Anfrage.", "Kalkulation unter 500 T€ mit offener Artikelanalyse → rote Markierung, keine "
     "Freigabeleiste; Angebot der Anfrage erstellen geht. Danach REV01-P06 und P08 prüfen.", "Kap. 13.4"),
    ("REV02-02", "Freigabe", "wunsch", "hoch", 2, "Freigabe-Workflow sichtbar: an wen geht die Freigabe",
     "Wohin geht der Workflow, zu wem? Das ist aktuell nicht erkennbar.", U,
     "Beim Anfordern wählt man, an wen (Administratoren und Benutzer mit Freigaberecht, nicht man selbst; oder alle). Die Person "
     "bekommt eine Benachrichtigung (E-Mail, falls eingerichtet), die Aufgabe „Freigabe prüfen“ und auf der Startseite den Block "
     "„Freigaben für mich“. Die Freigabeleiste zeigt „liegt bei … seit …“, die Anfrage ebenso.",
     "Freigabe an Tim Kraus anfordern → als Tim anmelden → Startseite „Freigaben für mich“ und Aufgabe → freigeben → Aufgabe erledigt.", "Kap. 13.4"),
    ("REV02-03", "Anfrage", "wunsch", "hoch", 2, "Entscheidung je Artikel weniger starr, Pflichtfelder klar",
     "Entscheidung ist zu starr; es ist nicht angegeben, was Pflichtfelder sind (Test REV01-P02).", U,
     "Die Entscheidung sperrt das Speichern der Kalkulation nicht mehr (rote Markierung „Entscheidung fehlt“). Gebraucht wird sie erst "
     "beim Erstellen des Angebots („Alle offenen anbieten“ in der Anfrage). Im Entscheidungsfeld stehen die Pflichtangaben: Entscheidung, "
     "Begründung bei „nicht anbieten“ und „Sonstiges“, Standort bei „anderer Standort“.",
     "Neuen Artikel ohne Entscheidung kalkulieren und speichern → geht, rote Markierung. Angebot erstellen → Hinweis auf offene Entscheidung.", "Kap. 13.4"),
    ("REV02-04", "Artikelanalyse", "wunsch", "mittel", 2, "Artikelanalyse: Fläche berechnen, Werkstoffwerte ausblenden, Vollständigkeit erklären",
     "Projizierte Fläche selbst ausrechnen und Formel anzeigen; Werkstoffwerte können raus; wann ist eine Artikelanalyse vollständig?", U,
     "Ohne CAD-Wert wird die projizierte Fläche aus Länge × Breite ÷ 100 geschätzt (umschließendes Rechteck, eher zu hoch → Schließkraft "
     "auf der sicheren Seite), Formel wird angezeigt, ebenso die Schließkraftformel. Werkstoffkennwerte eingeklappt (Richtwerte aus der "
     "Werkstoffgruppe). Vollständig = alle Prüfpunkte bewertet (ok/kritisch/n. a.) + Machbarkeit gewählt + gespeichert – als Liste mit ✓/✗.",
     "Artikelanalyse: Länge 600, Breite 130, Fläche leer → 780 cm² geschätzt mit Formel. Werkstoffkennwerte zugeklappt. Liste „Vollständig, wenn“.", "Kap. 13.4"),
    ("REV02-05", "Pipeline / Anfragen", "wunsch", "hoch", 2, "Wahrscheinlichkeit von Hand je Anfrage, ohne Gewichtung, filterbar",
     "Wahrscheinlichkeit je Angebot angeben (z. B. 25/50/75 %) und filtern; Volumen bleibt voll (1,2 Mio. € bleibt 1,2 Mio. €). Woher kommt "
     "die angezeigte Prozentzahl? (Test REV01-P09)", U,
     "Die Prozentzahl wurde bisher automatisch aus der Phase gesetzt – entfällt. Wahrscheinlichkeit wird nur von Hand eingeschätzt (Anfrage-Kopf "
     "oder Bearbeiten), sonst „–“ (nicht eingeschätzt); automatisch nur beim Abschluss 100 % / 0 %. Anfragenliste: Filter und Summen je "
     "Klasse (≥ 75 %, 50–74 %, < 50 %, nicht eingeschätzt) mit vollem Volumen, keine Gewichtung. Bisherige Automatikwerte wurden zurückgesetzt.",
     "Anfrage öffnen → Wahrscheinlichkeit 75 % wählen → Liste: Summe „≥ 75 %“ enthält das volle Volumen; Filter wählen.", "Kap. 13.4"),
    ("REV02-06", "Stammdaten Maschinen", "fehler", "mittel", 2, "Schichtmodell setzt verfügbare Stunden sofort",
     "Schichtmodell kann man auswählen, verfügbare Stunden ändern sich aber nicht (Test REV01-K01).", U,
     "Die Stunden wurden erst beim Speichern berechnet. Jetzt springt das Feld „Verfügbare Stunden / Jahr“ bei der Auswahl sofort um "
     "(1.920 / 3.840 / 5.760 h).", "Maschine bearbeiten → 2 Schichten → Feld zeigt sofort 3.840.", "Kap. 13.4"),
    ("REV02-07", "Protokoll", "wunsch", "hoch", 2, "Protokoll per Passwort gesperrt, nur für den SuperUser",
     "Das Protokoll soll per Passwort gesperrt und nur für mich als SuperUser zu öffnen sein; vorerst soll es niemand sehen.", U,
     "Menü „Protokoll“ und Reiter „Protokoll“ der Kalkulation nur für den SuperUser, Öffnen nach erneuter Passworteingabe (30 Minuten). "
     "SuperUser beim Update: SUPERUSER_EMAIL, sonst ADMIN_EMAIL. Recht und Konto ändert nur der SuperUser selbst. Aufzeichnung läuft weiter.",
     "Als Vertrieb/anderer Admin: kein Menüpunkt Protokoll. Als SuperUser: Protokoll → Passwort → Einträge sichtbar.", "Kap. 13.4"),
    ("REV02-10", "Protokoll", "wunsch", "hoch", 2, "Protokoll für dieses Update ausblenden",
     "Das Protokoll soll in diesem Update für niemanden sichtbar sein.", U,
     "Menü „Protokoll“ und Reiter „Protokoll“ der Kalkulation ausgeblendet, Schnittstelle gesperrt – für alle Benutzer. "
     "Aufzeichnung läuft weiter. Einschalten nur über eine Code-Änderung, nicht über die .env.",
     "Als Administrator anmelden → kein Menüpunkt Protokoll, kein Reiter in der Kalkulation; /protokoll zeigt „ausgeblendet“.", "Kap. 13.4"),
    ("REV02-08", "Allgemein", "fehler", "mittel", 2, "Uhrzeit nicht auf Winterzeit",
     "Die Uhrzeit des Systems scheint nicht auf Winterzeit zu sein.", U,
     "Zeitfelder (z. B. Fälligkeit von Aktivitäten) wurden ohne Zeitzone gesendet und als UTC gespeichert → eine Stunde verschoben. "
     "Jetzt mit Zeitzone; Server und Datenbank auf Europe/Berlin.", "Aktivität mit Fälligkeit 10:00 anlegen → Liste zeigt 10:00.", "Kap. 13.4"),
    ("REV02-09", "Allgemein", "wunsch", "mittel", 2, "Anzeige verbreitern; Beschaffung: Bezeichnung zeigt fremde Vorschläge",
     "Kalkulationsliste breiter anzeigen. In der Beschaffung erscheint unter Bezeichnung z. B. „Pipeline mit allen Anfragen …“.", U,
     "Listen nutzen die volle Breite. Der Vorschlag kam vom Browser (frühere Eingaben) – Browser-Vorschläge in Formularen abgeschaltet. "
     "Beschaffung: Kalkulation per Auswahl statt interner ID.", "Kalkulationsliste bei 1440 px ohne Querscrollen; Beschaffung anlegen → keine Vorschläge.", "Kap. 13.4"),
    # ---------------------------------------------------------------- REV03: Testrunde 3 (25.11.2026)
    ("REV03-01", "Pipeline / Anfragen", "fehler", "hoch", 2, "Pipeline und Anfragen: Fehler 500 nach Update auf v1.30",
     "Die Pipeline ist leer, Fehler 500 (Test REV01-P01, P05).", U,
     "Neue Ja/Nein-Spalte blieb in Altdaten leer → Listen brachen ab. Beim Start werden leere Ja/Nein-Werte gefüllt (Hotfix v1.30.1).",
     "Pipeline und Anfragen öffnen → Karten/Zeilen sichtbar, kein Fehler.", "Kap. 13.5"),
    ("REV03-02", "Angebot", "fehler", "hoch", 2, "Angebot lässt sich nicht erstellen",
     "Man kann keine Angebote erstellen (Test REV01-P04, P07, P08, MB-02).", U,
     "Ursache war die fehlende Entscheidung je Artikel. „Angebot der Anfrage erstellen“ setzt offene Artikel jetzt automatisch auf „anbieten“.",
     "Anfrage mit nicht entschiedenem Artikel → „Angebot erstellen“ → Angebot entsteht, Artikel „angeboten (automatisch)“. Danach P04, P06, P08, MB-02 prüfen.", "Kap. 13.5"),
    ("REV03-03", "Freigabe", "wunsch", "hoch", 2, "Freigabe-Workflow vorerst abschalten",
     "Freigabe zunächst rausnehmen, bis alles funktioniert (WUN-0004, Test REV01-F01, REV02-02).", U,
     "Parameter „Freigabe-Workflow aktiv“ (Stammdaten › Parameter), Standard 0 = aus: keine Freigabegründe, keine Sperre. Großprojekt-Markierung bleibt.",
     "Großprojekt-Kalkulation öffnen → keine Freigabeleiste; Angebot erstellen geht.", "Kap. 13.5"),
    ("REV03-04", "Artikelanalyse", "fehler", "hoch", 2, "Artikelanalyse lässt sich nicht speichern",
     "Man kann in der Artikelanalyse nichts speichern (Test REV01-P03).", U,
     "Der Knopf stand ganz unten rechts unter der Maschinenliste. Jetzt Speicherleiste oben, gelb bei ungespeicherten Änderungen.",
     "Artikelanalyse öffnen → Länge ändern → Leiste gelb → „Analyse speichern“ → „✓ gespeichert“.", "Kap. 13.5"),
    ("REV03-05", "Monatsbericht", "fehler", "mittel", 2, "Vertriebsziel eingegeben, aber nicht sichtbar",
     "Vertriebsziel kann eingegeben werden, ist aber nicht sichtbar – auch in der Tabelle (Test REV01-D05).", U,
     "Ziele je Vertriebler ohne Gesamtziel wurden nicht berücksichtigt. Jetzt gilt deren Summe als Jahresziel (Bericht und Startseite); alle Vertriebler mit Ziel stehen in der Tabelle.",
     "Nur Ziele je Vertriebler anlegen → Monatsbericht und Startseite zeigen Ziel = Summe.", "Kap. 13.5"),
    ("REV03-06", "Allgemein", "fehler", "mittel", 2, "Auswahl springt zurück; Branchen nicht zu sehen",
     "Nach i. O. springt die Auswahl zurück; Branchen werden nicht angezeigt (Test REV01-S01).", U,
     "Änderungswünsche: Filter bleiben nach i. O./n. i. O. stehen. Branche (und andere Felder mit eigener Eingabe): Auswahlliste mit „Eigene Eingabe …“.",
     "Änderungswünsche filtern → i. O. klicken → Filter bleibt. Firma bearbeiten → Branche als Liste.", "Kap. 13.5"),
    ("REV03-07", "Protokoll", "wunsch", "mittel", 2, "SuperUser fürs Protokoll zurücknehmen",
     "REV02-07 soll vorerst nicht umgesetzt werden – bitte zurücknehmen.", U,
     "SuperUser-Regeln und das Feld in der Benutzerverwaltung entfernt; Protokoll bleibt ausgeblendet (REV02-10).",
     "Benutzer bearbeiten → kein SuperUser-Feld.", "Kap. 13.5"),
    ("REV03-08", "Artikelanalyse", "wunsch", "hoch", 2, "Schließkraft nach F&R-Faustformel 0,55 t/cm²",
     "Formeln prüfen: ich rechne cm Länge × cm Breite × 0,55 (Test REV02-04).", U,
     "Schließkraft = Fläche × Fachzahl × 0,55 t/cm² (Parameter); Literatur bestätigt 3–5,5 kN/cm² → 0,55 ist das sichere Ende. Werkstoffbezogen nur noch als Option.",
     "Länge 600, Breite 130, Fachzahl 1 → 780 cm² × 0,55 = 429 t.", "Kap. 13.5"),
    ("REV03-09", "Angebot", "wunsch", "hoch", 2, "Wahrscheinlichkeit als eigene Einschätzung am Angebot",
     "Es soll nur anzeigen, wie wahrscheinlich ich es sehe, dass ein Angebot an uns vergeben wird (Test REV02-05).", U,
     "Feld im Angebot (10–90 % oder nicht eingeschätzt), Spalte und Filter in der Angebotsliste; keine Summen, keine Gewichtung.",
     "Angebot öffnen → 75 % wählen → Angebotsliste zeigt 75 %, Filter 75 % findet es.", "Kap. 13.5"),
    ("REV04-01", "Allgemein", "wunsch", "mittel", 3, "Softwarestand anzeigen: Version und wann eingespielt",
     "Auf die Seite muss, wann zuletzt aktualisiert wurde (Softwarestand).", U,
     "Unten in der Seitenleiste (über © SB/Thinkworks), auf der Anmeldeseite und unter Dokumentation steht „KlarCRM v1.32 · "
     "eingespielt am TT.MM.JJJJ, hh:mm“. Das Datum merkt sich das CRM beim ersten Start einer neuen Version; ein Neustart ändert es nicht. "
     "Klick auf den Softwarestand zeigt alle Auslieferungen.",
     "Seitenleiste unten ansehen, dann darauf klicken; abmelden und die Anmeldeseite ansehen.", "Kap. 13.6"),
    ("REV04-02", "Änderungswünsche", "wunsch", "hoch", 3, "Prüfseite je Update: nur aktuelle Punkte, Reihenfolge, Hinspringen, abhaken",
     "Abhaken ist verwirrend: alte und neue Punkte durcheinander, Nachbessern gemischt; eins nach dem anderen prüfen können.", U,
     "Neue Seite „Prüfen“ (Menü Verwaltung): nur die Punkte des aktuellen Updates in Prüfreihenfolge, Zähler „x von y geprüft“, "
     "je Punkt „Was tun“ und „Was herauskommen muss“, Knopf „Hinspringen“ öffnet die Stelle im CRM, große Knöpfe „✓ passt“ / "
     "„✗ passt nicht“ (dann Text Pflicht). Sind alle Punkte geprüft, erklärt der Administrator „v1.xx abgenommen“. "
     "Ersetzte Altpunkte stehen jetzt auf „überholt“ mit Verweis auf den neuen Punkt.",
     "Menü „Prüfen“ öffnen und diese Liste von oben nach unten abarbeiten; unter Änderungswünsche Filter Status „überholt“.", "Kap. 13.6"),
    ("REV04-03", "Pipeline", "fehler", "hoch", 2, "Pipeline: Spalte „Verloren“ fehlt",
     "Die Pipeline hat den Reiter „Verloren“ nicht mehr (Test REV01-P05).", U,
     "Ursache: Board fest auf 6 Spalten, seit Phase 2 (v1.24) gibt es 7 Phasen → „Verloren“ rutschte in eine zweite Reihe unter „Lead“. "
     "Jetzt alle Phasen in einer Reihe (bei schmalem Bildschirm seitlich scrollbar).",
     "Pipeline öffnen → rechts außen Spalte „Verloren“.", "Kap. 13.6"),
    ("REV04-04", "Startseite", "wunsch", "hoch", 3, "Vertriebsziel groß auf der Startseite mit Erfüllungsgrad",
     "Nachbesserung REV03-05: Vertriebsziel ist da, aber auf der Startseite zu klein – Erfüllungsgrad muss auf einen Blick sichtbar sein.", U,
     "Oben auf der Startseite ein breiter Block „Vertriebsziel 2026“: gewonnen seit 1.1. gegen Jahresziel, Erfüllungsgrad in %, Ampel, "
     "Balken mit Soll-Marke (wo wir heute stehen müssten), Rest bis zum Ziel und eine Zeile je Vertriebler (mit eigenem Ziel, falls vorhanden). "
     "Klick öffnet den Monatsbericht. Ohne Ziel: Hinweis, wo es eingetragen wird.",
     "Startseite öffnen; danach im Monatsbericht ein Ziel ändern und die Startseite neu laden.", "Kap. 13.6"),
    ("REV04-05", "Stammdaten", "wunsch", "niedrig", 3, "Freigabe-Schalter als Häkchen statt 0/1",
     "Parameter „Freigabe-Workflow“ wird als Zahl 0/1 eingegeben – unverständlich.", U,
     "Stammdaten → Parameter → „Großprojekte und Freigabe“: Häkchen „Freigabe-Workflow eingeschaltet“. Wirkung unverändert (aus = keine Freigabe nötig).",
     "Häkchen ansehen (nicht gesetzt), nicht verändern.", "Kap. 13.6"),
    ("REV04-06", "Anfrage", "fehler", "mittel", 3, "Schrittleiste: „Kalkulation“ erst nach zweiter Version erledigt",
     "In der Anfrage wurde „Kalkulation“ erst grün, wenn eine zweite Kalkulationsversion existierte.", U,
     "„Kalkulation“ gilt als erledigt, sobald jeder angebotene Artikel eine berechnete Kalkulation hat (oder „nicht anbieten“ ist).",
     "Anfrage mit kalkulierten Artikeln öffnen → Schritt „Kalkulation“ ist erledigt.", "Kap. 13.6"),
    ("REV05-01", "Pipeline", "wunsch", "mittel", 2, "Verlust: Hauptgrund plus weitere Gründe",
     "Aus Prüfung REV01-P05 (v1.32, 28.11.2026): Man sollte mehr als einen Grund angeben können, warum etwas verloren ging.", "freigegeben",
     "Vorgemerkt für Block 3 Pipeline/Berichte: ein Hauptgrund bleibt Pflicht und zählt allein in der Auswertung der Absagegründe "
     "(sonst mehr Gründe als Verluste); zusätzlich optional „weitere Gründe“ zum Ankreuzen, sichtbar in Anfrage/Angebot und als eigene Spalte im Bericht.",
     "", "Kap. 13.7"),
    ("WUN-0004", "Freigabe", "wunsch", "hoch", 2, "Freigabeprozess",
     "Freigabe zunächst einmal wieder rausnehmen, bis alles funktioniert – Sperrung durch fehlende Freigabe raus.", U,
     "Umgesetzt mit REV03-03: Freigabe-Workflow per Parameter abgeschaltet.", "siehe REV03-03", "Kap. 13.5"),
    ("WUN-0001", "Änderungswünsche", "wunsch", "niedrig", 2, "In Änderungswünschen",
     "In den Änderungswünschen sollte man per Klick angeben können, ob eine Änderung erfolgreich war, wenn nicht muss man dieses beschreiben. "
     "Auch von wem Änderungswünsche gemeldet werden, sollte automatisch gefüllt sein. Änderungswünsche können nur durch einen Admin freigegeben werden.", U,
     "Knöpfe „✓ i. O.“ und „✗ n. i. O.“ in der Liste (bei n. i. O. Beschreibung Pflicht) – Prüfer und Datum werden automatisch gesetzt. "
     "„Gemeldet von“ wird beim Anlegen mit dem angemeldeten Benutzer gefüllt. Neue Wünsche sind „eingereicht“ und werden nur von einem "
     "Administrator freigegeben (oder abgelehnt); vom Administrator angelegte Wünsche sind gleich freigegeben.",
     "Als Vertrieb neuen Wunsch anlegen → Status eingereicht, Melder gesetzt → als Admin „Freigeben“. Bei einem umgesetzten Punkt „✗ n. i. O.“ → Text Pflicht.", "Kap. 13.4"),
]


def _ver(code: str, phase) -> str:
    if code in V134:
        return "1.34"
    if code.startswith("REV05") or code in V133:
        return "1.33"
    if code.startswith("REV04"):
        return "1.32"
    if code.startswith("REV03") or code == "WUN-0004":
        return "1.31"
    if code.startswith("REV02") or code == "WUN-0001":
        return "1.28"
    if code.startswith("MB-"):
        return "1.27" if code == "MB-02" else "1.26"
    return "1.24" if phase == 2 else "1.23"


def seed_rev01(db) -> int:
    from .models import ChangeRequest  # noqa: PLC0415
    have = {c for (c,) in db.query(ChangeRequest.code).all()}
    n = 0
    # Neu umgesetzte Punkte nachziehen – nur wenn der Eintrag noch unbearbeitet „offen“ ist (Prüfstand bleibt unangetastet)
    for code, area, kind, prio, phase, title, desc, status, solution, test, req in ITEMS:
        if code in have and status == U:
            cr = db.query(ChangeRequest).filter(ChangeRequest.code == code).first()
            if cr and cr.status in ("offen", "eingereicht", "freigegeben", "in_arbeit") and not (cr.test_result or "").strip():
                cr.status, cr.solution, cr.test_steps = U, solution, test
                cr.version = _ver(code, phase)
    for code, area, kind, prio, phase, title, desc, status, solution, test, req in ITEMS:
        if code in have:
            continue
        rev = code.split("-")[0] if code.startswith("REV") else "Wunsch"
        db.add(ChangeRequest(code=code, revision=rev, area=area, kind=kind, priority=prio, phase=phase, title=title,
                             description=desc, status=status, solution=solution, test_steps=test,
                             req_ids=f"Lastenheft Kap. 13 · {code}",
                             version=_ver(code, phase) if status == U else None,
                             requested_by=f"Sandro ({rev})" if rev != "Wunsch" else "Sandro"))
        n += 1
    db.commit()
    seed_checks(db)
    return n


# ------------------------------------------------------------------ REV04-02 Prüfseite: Prüfpunkte je Update
# code: (Update, Reihenfolge, Hinspringen, Was tun, Was herauskommen muss)
CHECKS = {
    "REV04-01": ("1.32", 1, "/", "Unten links in der Seitenleiste über „© SB/Thinkworks“ nachsehen, dann darauf klicken. "
                 "Zum Schluss abmelden und die Anmeldeseite ansehen.",
                 "Dort steht „KlarCRM v1.32 · eingespielt am …“ mit dem Datum und der Uhrzeit, an dem die IT das Update eingespielt hat. "
                 "Der Klick zeigt die Liste der Auslieferungen. Auf der Anmeldeseite steht ebenfalls v1.32."),
    "REV04-04": ("1.32", 2, "/", "Startseite ansehen.",
                 "Ganz oben ein breiter Block „Vertriebsziel 2026“: gewonnen seit 1.1. gegen das Jahresziel, Erfüllungsgrad in %, Ampel, "
                 "Balken mit Soll-Marke und darunter je Vertriebler eine Zeile. Klick auf den Block öffnet den Monatsbericht."),
    "REV04-03": ("1.32", 3, "/pipeline", "Pipeline öffnen und nach rechts schauen (bei schmalem Bildschirm seitlich scrollen).",
                 "Alle 7 Spalten stehen nebeneinander in einer Reihe, rechts außen „Verloren“."),
    "REV01-P05": ("1.32", 4, "/pipeline", "Nachprüfung aus v1.31: eine Karte auf „Verloren“ ziehen. Grund zuerst leer lassen und speichern, dann „Sonstiges“ ohne Text.",
                  "Ohne Grund lässt sich nicht speichern; bei „Sonstiges“ ist der Freitext Pflicht. Danach Dialog abbrechen "
                  "(oder eine Test-Anfrage verwenden), damit keine echte Anfrage verloren gesetzt wird."),
    "REV04-06": ("1.32", 5, "/anfragen", "Eine Anfrage öffnen, deren Artikel schon kalkuliert sind (Teilgewicht eingetragen), aber nur eine Version haben.",
                 "In der Schrittleiste oben ist „Kalkulation“ erledigt (grün). Bei einer Anfrage mit noch leeren Artikeln ist er offen."),
    "REV04-05": ("1.32", 6, "/stammdaten?tab=params", "Stammdaten → Parameter → Karte „Großprojekte und Freigabe“ ansehen. Nichts ändern.",
                 "Statt der Zahl 0/1 steht ein Häkchen „Freigabe-Workflow eingeschaltet“ – es ist nicht gesetzt (Freigabe bleibt aus)."),
    "REV04-02": ("1.32", 7, "/aenderungen?status=ueberholt", "Diese Seite selbst: Punkte der Reihe nach mit „✓ passt“ / „✗ passt nicht“ prüfen. "
                 "Dann unter Änderungswünsche den Status „überholt“ ansehen (Hinspringen).",
                 "Der Zähler oben zählt mit; „✗ passt nicht“ verlangt einen Text. Unter „überholt“ stehen die ersetzten Altpunkte "
                 "(z. B. REV03-05 → REV04-04), sie tauchen nicht mehr bei „Nachbessern“ auf."),
}

# Altpunkt → ersetzt durch (REV04-02): erhält den Status „überholt“ mit Verweis
SUPERSEDED = {
    "REV01-P01": "REV03-01", "REV01-F01": "REV03-03", "REV02-02": "REV03-03", "REV01-P03": "REV03-04",
    "REV02-04": "REV03-08", "REV01-D05": "REV03-05", "REV01-P09": "REV03-09", "REV02-05": "REV03-09",
    "REV01-S01": "REV03-06", "REV02-07": "REV03-07", "REV03-05": "REV04-04",
}


def seed_checks(db) -> None:
    from .models import CalcSettings, ChangeRequest  # noqa: PLC0415
    for code, (ver, order, link, todo, expected) in CHECKS.items():
        cr = db.query(ChangeRequest).filter(ChangeRequest.code == code).first()
        if not cr or cr.check_version:
            continue          # schon eingeplant – Prüfstand aus der Oberfläche bleibt
        cr.check_version, cr.check_order, cr.check_link, cr.test_steps, cr.expected = ver, order, link, todo, expected
        if cr.status not in ("geprueft", "abgelehnt", "ueberholt"):
            cr.status = U
            cr.version = ver
    # WUN-0003 „direkt zur geänderten Stelle springen“ (aus der Oberfläche) ist mit „Hinspringen“ erledigt
    w = db.query(ChangeRequest).filter(ChangeRequest.code == "WUN-0003").first()
    if w and not w.check_version and "spring" in f"{w.title} {w.description}".lower():
        w.status, w.version, w.check_version, w.check_order, w.check_link = U, "1.32", "1.32", 8, "/pruefen"
        w.solution = "Umgesetzt mit REV04-02: Knopf „Hinspringen“ auf der Prüfseite öffnet die geänderte Stelle im CRM."
        w.test_steps = "Auf dieser Seite bei einem Punkt „Hinspringen“ klicken."
        w.expected = "Die passende Seite im CRM öffnet sich; mit „Zurück“ im Browser geht es wieder auf die Prüfseite."
    cs = db.get(CalcSettings, 1)
    if cs is not None and not (cs.data or {}).get("_rev04_ueberholt"):
        for old, new in SUPERSEDED.items():
            cr = db.query(ChangeRequest).filter(ChangeRequest.code == old).first()
            if cr and cr.status not in ("geprueft", "abgelehnt"):
                cr.status, cr.superseded_by = "ueberholt", new
                cr.test_result = ((cr.test_result or "").strip() + f"\n→ überholt durch {new}").strip()
        cs.data = {**(cs.data or {}), "_rev04_ueberholt": True}
    db.commit()


# ------------------------------------------------------------------ v1.33 Block 1 „Kalkulation rechnen“ (28.11.2026)
V133 = {
    "REV01-C02": ("Kalkulation → Mengen: Tabelle „Mengen je Lieferjahr“ mit Menge und Losgröße je Jahr (leer = Jahresmenge/Losgröße oben). "
                  "Je Jahr: Lose, Maschinenstunden, Material kg, Zukaufteile Stk, Preis, Umsatz, Marge (mit Menge und Losgröße des Jahres "
                  "nachgerechnet) und Projektsumme. Werkzeugamortisation über die Summe der Jahresmengen. Neuumsatz = stärkstes Jahr.",
                  "Kalkulation öffnen → Mengen: Jahr 1 = 20.000, Jahr 2–5 = 60.000 eintragen."),
    "REV01-C05": ("Lieferjahre standardmäßig 5 (Projektlaufzeit), „+ Jahr“ / „− Jahr“ bis 15. Preis je Jahr inkl. Abschläge wie bisher; "
                  "Häkchen „Preise und Mengen je Lieferjahr im Angebot zeigen“ (ohne Häkchen Angebot wie bisher).",
                  "In der Tabelle „+ Jahr“ klicken; Häkchen setzen, speichern, Angebot der Anfrage aktualisieren."),
    "REV01-C04": ("Losgröße: Vorschlag Jahresmenge ÷ 12 mit „übernehmen“; in der Jahrestabelle Jahr 1 (Anlauf) von Hand, ab Jahr 2 Vorschlag "
                  "Menge ÷ 12 (Knopf „Losgröße ab Jahr 2 = Menge ÷ 12“). „Verpackungsimport?“ entfällt (unklar, GF 28.11.2026).",
                  "Bei Jahr 2 = 60.000 steht als Vorschlag 5.000."),
    "REV01-C01": ("Zukaufteile: Name frei eingebbar (neu → beim Speichern in Stammdaten › Zukaufteile, Vermerk „aus Kalkulation“), "
                  "Lieferant, bis zu 5 Staffelpreise; Jahresbedarf = Stück je Bauteil × Jahresmenge, es gilt die passende Staffel. "
                  "Hinweis, wenn eine größere Einkaufsmenge günstiger ist.",
                  "Zukaufteil „Buchse M5“ frei anlegen, 4 Stk je Bauteil, Staffeln ab 10.000 → 0,12 € und ab 50.000 → 0,09 €, Jahresmenge 15.000, speichern."),
    "REV01-C03": ("Material: „Neues Material (Freitext)“ (beim Speichern → Stammdaten › Material), Lieferant, Angebotsnummer, bis zu 5 "
                  "Staffelpreise je kg nach Jahresbedarf (inkl. Anguss und Ausschuss), Vorschlag Einkaufsmenge pro Jahr mit Hinweis, "
                  "wenn die nächste Staffel günstiger ist. Masterbatch mit Bezeichnung und Lieferant, Anteil als Dosierung in %.",
                  "Neues Material „PP schwarz Test“ mit Staffeln, Masterbatch 3 % eintragen, speichern, Stammdaten › Material ansehen."),
    "REV01-C07": ("Knopf „⎘ Variante anlegen“: Kopie mit neuer Fachzahl in derselben Anfrage, verknüpft („Variante von“). Artikelanalyse "
                  "(Schließkraft) rechnet mit der neuen Fachzahl; Werkzeugkosten/Zyklus passt der Kalkulator an. Karte „Varianten im "
                  "Vergleich“. In der Pipeline zählt je Artikel nur die größte Variante.",
                  "In einer 2-fach-Kalkulation „Variante anlegen“ mit Fachzahl 4."),
}
_new = [
    ("REV05-02", "Startseite", "wunsch", "mittel", 3, "Vertriebsziel-Block etwa doppelt so groß",
     "Aus Prüfung REV04-04 (v1.32): Block ist da, kann aber doppelt so groß sein – Zahlen gewonnen, Jahresziel usw.", U,
     "Prozentwert, Zahlen (Gewonnen, Jahresziel, Soll heute, Noch bis zum Ziel), Ampel und Balken etwa doppelt so groß.",
     "Startseite ansehen.", "Kap. 13.8"),
    ("REV05-03", "Änderungswünsche", "wunsch", "mittel", 3, "Prüfbericht je Update als PDF und CSV",
     "Aus Prüfung v1.32: Von der Prüfseite lässt sich nichts exportieren – Abnahmenachweis muss ablegbar sein.", U,
     "Prüfseite: „🖨 Prüfbericht drucken / PDF“ (Druckansicht mit allen Punkten, Ergebnis, Prüfer, Datum, Abnahme – im Druckdialog "
     "„Als PDF speichern“) und „⬇ Prüfbericht CSV“ (Excel).",
     "Prüfseite → beide Knöpfe; Update-Auswahl v1.32 → Bericht mit Abnahme.", "Kap. 13.8"),
]
ITEMS = [(t[0], t[1], t[2], t[3], t[4], t[5], t[6], U, V133[t[0]][0], V133[t[0]][1], "Kap. 13.8") if t[0] in V133 else t
         for t in ITEMS] + _new

CHECKS.update({
    "REV01-C02": ("1.33", 1, "/kalkulationen", "Eine Kalkulation öffnen (Reiter Kalkulation) → Abschnitt Mengen → Tabelle „Mengen je Lieferjahr“: "
                  "Jahr 1 = 20.000, Jahr 2 bis 5 = 60.000 eintragen (noch nicht speichern).",
                  "Je Jahr ändern sich Lose, Maschinenstunden, Material kg und Umsatz passend zur Menge; die Zeile „Projekt“ zeigt die Summe. "
                  "Jahr 1 hat wegen der kleinen Menge eine schlechtere Marge."),
    "REV01-C04": ("1.33", 2, "/kalkulationen", "In derselben Tabelle auf „Losgröße ab Jahr 2 = Menge ÷ 12“ klicken; oben beim Feld Losgröße den Vorschlag ansehen.",
                  "Jahr 2–5 bekommen Losgröße 5.000 (60.000 ÷ 12), Jahr 1 bleibt von Hand. Beim Feld Losgröße steht „Vorschlag … (Jahresmenge ÷ 12) · übernehmen“."),
    "REV01-C05": ("1.33", 3, "/kalkulationen", "„+ Jahr“ klicken. Dann Häkchen „Preise und Mengen je Lieferjahr im Angebot zeigen“ setzen und speichern.",
                  "Es gibt ein Jahr 6 mit Preis, Umsatz und Marge. Nach „→ Angebot … aktualisieren“ stehen im Angebot Menge × Preis je Jahr."),
    "REV01-C01": ("1.33", 4, "/kalkulationen", "Abschnitt Material → „+ Zukaufteil“, Auswahl „– frei –“, Name „Buchse M5 Test“, 4 Stück je Artikel, "
                  "Lieferant eintragen, Staffeln ab 10.000 → 0,12 und ab 50.000 → 0,09. Jahresmenge 15.000. Speichern.",
                  "Jahresbedarf 60.000 Stk, das CRM nimmt 0,09 €. Danach steht „Buchse M5 Test“ unter Stammdaten › Zukaufteile (mit Staffel)."),
    "REV01-C03": ("1.33", 5, "/kalkulationen", "Material → „Neues Material (Freitext)“: „PP schwarz Test“, Lieferant, Angebotsnummer, Staffeln ab 1.000 kg → 2,00 und "
                  "ab 5.000 kg → 1,80. Masterbatch 3 % mit Bezeichnung. Speichern.",
                  "Unter den Feldern stehen Jahresbedarf kg, die gültige Staffel und die Einkaufsmenge; Masterbatch-kg = 3 % der Materialmenge. "
                  "„PP schwarz Test“ und der Masterbatch stehen danach in Stammdaten › Material."),
    "REV01-C07": ("1.33", 6, "/kalkulationen", "In einer Kalkulation oben „⎘ Variante anlegen“, Fachzahl z. B. doppelt so hoch.",
                  "Eine neue Kalkulation „… – Variante 4-fach“ öffnet sich, rechts die Karte „Varianten im Vergleich“ (Fachzahl, Schließkraft, Preis). "
                  "In der Anfrage steht sie als „↳ Variante von …“; der Anfragewert zählt nur die größere Variante."),
    "REV05-02": ("1.33", 7, "/", "Startseite ansehen.", "Der Vertriebsziel-Block ist deutlich größer: Prozent, Zahlen, Ampel und Balken etwa doppelt so groß."),
    "REV05-03": ("1.33", 8, "/pruefen", "Auf dieser Seite „🖨 Prüfbericht drucken / PDF“ und „⬇ Prüfbericht CSV“ klicken; oben Update v1.32 wählen und wiederholen.",
                 "Die Druckansicht zeigt alle Punkte mit Ergebnis, Prüfer, Datum und die Abnahme (bei v1.32 mit Namen und Datum). Die CSV öffnet sich in Excel."),
})


# ------------------------------------------------------------------ v1.34 Block 1 Teil 2 „Zusatzblätter“ (28.11.2026)
V134 = {
    "REV01-C06": ("Reiter „3 · Werkzeug“ (Werkzeugblatt je Artikel): Konstruktion/CNC, Abmustern/Prüfbericht, Fühler, Heißkanal (mit Düsen), "
                  "Werkzeugkosten extern, Angebotspreis und Marge; Termine FOT, Baumuster/EMPB, PPAP in Wochen, SOP; Standzeit gegen Schüsse "
                  "über die Laufzeit; Vergleich Werkzeugangebote WZB 1–4 (gewähltes ersetzt „extern“). „→ in die Kalkulation übernehmen“ "
                  "schreibt Kosten/Preis als Einmalkosten „Werkzeug“ (neue Version). Termine, Heißkanal und Standzeit stehen im Angebot.",
                  "Werkzeugblatt ausfüllen, speichern, übernehmen, Angebot aktualisieren."),
    "REV01-C08": ("Reiter „4 · Risiko“: 13 Fragen ja/nein mit Bemerkung; Einstufung nach Anteil „ja“ hoch > 60 % / mittel 35–60 % / niedrig "
                  "< 35 %, getrennt für Fertigungsprozess und Lieferkette; Invest > 10.000 € aus der Kalkulation vorbelegt; Maßnahmen. "
                  "Einstufung im Kopf der Kalkulation, in der Anfrage und im Kickoff.",
                  "Risikoanalyse ausfüllen und speichern."),
    "REV01-C09": ("Reiter „Neue Anlagen“: je Anlage Invest F&R/extern, Nutzungsdauer, Zins, Fläche, Leistung, Betriebskosten, Instandhaltung, "
                  "Overhead, verfügbare Stunden, Verfügbarkeit, Zeit je Stück → Stundensatz (Herleitung wie Maschinen, Kap. 6.1), Kosten je "
                  "Stück, Auslastung; Kostenbasis „nur dieser Artikel“ (Standard) oder „auch andere Aufträge“; Kapazitätsprüfung Liquidität, "
                  "Fläche, Personal. „→ als Arbeitsgang in die Kalkulation“ (neue Version).",
                  "Neue Anlage anlegen, speichern, als Arbeitsgang übernehmen."),
    "REV01-C10": ("Beim Auftrag (Auftrag erhalten, Status „gewonnen“ oder Anfrage gewonnen) entsteht automatisch der Kickoff: Schnappschuss "
                  "aller Daten (Kunde, Preis/Mengen je Jahr, Fertigung, Material/Zukaufteile, Werkzeug, neue Anlagen, Risiko, Machbarkeit) "
                  "mit offenen Punkten, Reiter „Kickoff“ zum Drucken, Aufgabe „Kickoff durchführen“ für den Verantwortlichen (5 Arbeitstage).",
                  "Test-Artikel auf „gewonnen“ setzen, Reiter Kickoff und Aufgaben ansehen."),
}
ITEMS = [(t[0], t[1], t[2], t[3], t[4], t[5], t[6], U, V134[t[0]][0], V134[t[0]][1], "Kap. 13.9") if t[0] in V134 else t for t in ITEMS]
CHECKS.update({
    "REV01-C06": ("1.34", 1, "/kalkulationen", "Eine Kalkulation öffnen → Reiter „3 · Werkzeug“: Kosten eintragen, Heißkanal anhaken, zwei Werkzeugangebote "
                  "erfassen und eines wählen, Angebotspreis, Wochen für FOT / Baumuster / PPAP und Standzeit eintragen. Speichern, dann "
                  "„→ in die Kalkulation übernehmen“.",
                  "Summe, Marge und Standzeit-Prüfung stimmen; das gewählte Angebot ersetzt „extern“. Im Reiter Kalkulation steht eine neue Version "
                  "mit Einmalkosten „Werkzeug (lt. Werkzeugblatt)“. Nach „Angebot aktualisieren“ stehen Termine (FOT, PPAP, SOP) unter dem Artikel."),
    "REV01-C08": ("1.34", 2, "/kalkulationen", "Reiter „4 · Risiko“: alle 13 Fragen beantworten, Maßnahme eintragen, speichern.",
                  "Oben Gesamt-% mit Einstufung (hoch > 60 %, mittel 35–60 %, niedrig < 35 %) und je Fertigungsprozess / Lieferkette. Die Einstufung "
                  "steht danach im Kopf der Kalkulation und in der Anfrage beim Artikel."),
    "REV01-C09": ("1.34", 3, "/kalkulationen", "Reiter „Neue Anlagen“ → „+ Neue Anlage“ (z. B. Schweißanlage 120.000 €, 12 s je Stück), speichern; "
                  "dann „→ als Arbeitsgang in die Kalkulation“.",
                  "Stundensatz mit Herleitung, Kosten je Stück und Auslastung erscheinen; Kostenbasis umschaltbar. In der Kalkulation steht ein "
                  "Arbeitsgang „Neue Anlage: …“ (neue Version)."),
    "REV01-C10": ("1.34", 4, "/kalkulationen", "Einen Test-Artikel beauftragen (Angebot → Auftrag erhalten, oder Status „gewonnen“). Dann Reiter „Kickoff“ "
                  "öffnen und „Kickoff drucken / PDF“.",
                  "Der Kickoff ist da – mit Daten aus Kalkulation, Werkzeug, Risiko, neuen Anlagen und den offenen Punkten. Unter Aufgaben steht "
                  "„Kickoff durchführen: …“ für den Verantwortlichen."),
})
