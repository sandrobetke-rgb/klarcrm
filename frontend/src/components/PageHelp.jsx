import { useState } from 'react'
import { useLocation } from 'react-router-dom'

/** Kurze Anleitung oben auf jeder Seite: wozu die Seite da ist und wie man vorgeht. Auf-/Zuklappen wird je Seite gemerkt. */
const HELP = [
  ['/kalkulationen/', 'Kalkulation bearbeiten', 'Eine Anfrage durchrechnen, Versionen festhalten und in ein Angebot überführen.', [
    'Kopfdaten prüfen: Kunde, Ansprechpartner, Artikel, Status, Machbarkeit, Serienstart.',
    'Im Reiter „Kalkulation“ von oben nach unten arbeiten: Mengen → Material/Zukaufteile → Maschine & Personal (in %) → Rüsten → Montage & Arbeitsgänge → Verpackung & Transport → Zuschläge.',
    'Werte sind aus Stammdaten vorbelegt; Abweichungen werden gelb markiert und lassen sich mit „↺“ zurücksetzen.',
    'Teure Zukaufteile bei Bedarf per Haken in die Nebenkalkulation nehmen; Jahresabschläge und Vorserienpreis unten eintragen.',
    'Rechts stehen Preis, Kalkulationsschema und CO₂ – live. Mit „Version speichern“ (mit Änderungsnotiz) wird der Stand festgeschrieben.',
    'Großprojekte brauchen vor dem Angebot eine Freigabe (Vier-Augen-Prinzip). Danach „Angebot erstellen“.',
    'Weitere Reiter: Artikelanalyse, Lebensweg, Dokumente, Anrufe, Versionen (Vergleich), Nachkalkulation, Protokoll.',
  ]],
  ['/kalkulationen', 'Kalkulationen / Anfragen', 'Übersicht aller Anfragen mit Status, Preis, Umsatz und letztem Anruf.', [
    '„Neue Kalkulation“ legt eine Anfrage an (optional aus Vorlage). Filter oben: Status, Verlust-/Absagegrund, Machbarkeit, Großprojekte, Freigabe.',
    'Zeile anklicken öffnet die Kalkulation. Fett = lange nicht angerufen.',
    'Mehrere Artikel desselben Kunden anhaken → „Sammelangebot“ erstellt ein Angebot mit allen Positionen.',
  ]],
  ['/auswertungen', 'Auswertungen', 'Berichte über alle Anfragen: wo kommen Anfragen her, wo sagen wir ab, wo gewinnen oder verlieren wir.', [
    'Zeitraum (nach Anfragedatum), Vertrieb oder Kunde oben wählen – alle Berichte rechnen sofort neu.',
    'Bericht über die Reiter wählen; je Bericht zwischen Anzahl, Umsatz und Absagen + Verluste umschalten.',
    '„CSV“ exportiert die Tabelle für Excel, „Drucken / PDF“ druckt die Seite (z. B. „Alle Berichte“ für die Gesellschafterrunde).',
  ]],
  ['/auslastung', 'Auslastung kommende Jahre', 'Maschinen- und Anlagenstunden aus Bestand und Kalkulationen im Verhältnis zur Kapazität.', [
    'Ansicht wählen: Fest (Bestand + gewonnen), Erwartet (+ offene gewichtet mit Wahrscheinlichkeit), Maximal (+ alle offenen).',
    'Zeile anklicken zeigt, welche Kalkulationen bzw. Arbeitsgänge die Stunden verursachen.',
    'Kapazität, Grundauslastung und Auslauf je Maschine pflegen Sie in den Stammdaten.',
  ]],
  ['/stammdaten', 'Stammdaten', 'Vorgabewerte für alle neuen Kalkulationen.', [
    'Maschinen & Anlagen (inkl. Montagelinien, Prüfstände), Stundensätze, Materialien, Zukaufteile, Preisgleitung, Vorlagen und Parameter (Zuschläge, Lohnsätze).',
    'Änderungen wirken auf neue Kalkulationen; gespeicherte Versionen bleiben unverändert (Nachvollziehbarkeit).',
    'Nur Administratoren ändern Parameter; Materialpreisänderungen werden automatisch protokolliert.',
  ]],
  ['/angebote/', 'Angebot', 'Angebot bearbeiten, drucken und versenden.', [
    'Positionen, Texte und Konditionen prüfen; Sprache Deutsch/Englisch wählen.',
    '„Drucken / PDF“ erzeugt das Angebot im Firmenlayout; „E-Mail“ öffnet einen Entwurf an den Ansprechpartner.',
    'Status pflegen (versendet, angenommen, abgelehnt) – das wirkt auf Pipeline und Auswertungen.',
  ]],
  ['/angebote', 'Angebote', 'Alle Angebote mit Status und Summe.', ['Angebote entstehen meist aus einer Kalkulation („Angebot erstellen“) oder als Sammelangebot.']],
  ['/firmen/', 'Firma', 'Alles zu einem Kunden auf einen Blick.', ['Kontakte, Verkaufschancen, Aktivitäten, Kalkulationen, Angebote und Dokumente des Kunden.']],
  ['/firmen', 'Firmen', 'Kunden, Interessenten und Lieferanten.', ['Firma anlegen, über die Suche finden, Zeile öffnen für die Kundenakte.']],
  ['/kontakte', 'Kontakte', 'Ansprechpartner bei den Firmen.', ['E-Mail-Adresse pflegen – sie wird für Angebots-E-Mails verwendet.']],
  ['/aktivitaeten', 'Aktivitäten', 'Aufgaben, Anrufe, Termine und Wiedervorlagen.', ['Filter „Überfällig“ und „Heute“ nutzen; Termine lassen sich als .ics in Outlook übernehmen.']],
  ['/pipeline', 'Pipeline', 'Verkaufschancen nach Phase.', ['Karten zeigen Volumen und Wahrscheinlichkeit; Chancen aus Kalkulationen werden automatisch aktualisiert.']],
  ['/beschaffung/', 'Beschaffungsvorgang', 'Lieferanten anfragen, Angebote vergleichen, vergeben und in die Kalkulation übernehmen.', [
    'Eckdaten prüfen („Bearbeiten“): bei Werkzeugen Fachzahl, Heißkanal, Stahl, Standzeit … – vorbelegt aus der Kalkulation.',
    'Lieferanten hinzufügen (Firmen mit Typ „Lieferant“) oder „+ anderer Lieferant“. Je Lieferant „Anfrage“ druckt die Werkzeuganfrage im Firmenlayout (als PDF speichern), „E-Mail“ öffnet einen Entwurf – Zeichnung/3D-Daten anhängen.',
    'Eingehende Angebote mit „Erfassen“ eintragen (Preis, Lieferzeit, Stahl, Standzeit, Bewertung) und das PDF unten ablegen.',
    'Im Vergleich „Wählen“ und die Vergabe begründen. „In Kalkulation übernehmen“ setzt den Preis als Einmalkosten in einer neuen Kalkulationsversion.',
  ]],
  ['/beschaffung', 'Beschaffung', 'Alle Anfragen für Werkzeuge, Montagelinien, Vorrichtungen und Prüfmittel.', [
    'Neuer Vorgang über „+ Beschaffung anlegen“ oder direkt in der Kalkulation im Reiter „Beschaffung“ (dann mit Eckdaten aus der Kalkulation).',
    'Liste zeigt je Vorgang Anzahl Angebote, günstigstes Angebot und die Vergabeentscheidung.',
  ]],
  ['/protokoll', 'Änderungsprotokoll', 'Wer hat wann was geändert (IATF/ISO-Nachweis).', ['Nach Objekt, Benutzer oder Zeitraum filtern. Einträge sind nicht änderbar.']],
  ['/benutzer', 'Benutzer', 'Zugänge und Rollen verwalten.', ['Rollen: Administrator, Vertrieb, Gesellschafter (nur lesen). „Freigabeberechtigt“ für das Vier-Augen-Prinzip.']],
  ['/einstellungen', 'Firma & Layout', 'Briefkopf für alle Dokumente (Angebote, Werkzeug- und Anlagenanfragen).', [
    'Firmendaten, Standorte, Registerangaben, Steuernummer, Bankverbindungen und Zertifizierungen eintragen – leere Felder erscheinen nicht.',
    'Logo hochladen (PNG, JPG oder SVG, am besten mit transparentem Hintergrund), Größe und Akzentfarbe wählen.',
    'Die Vorschau zeigt Kopf und Fußzeile; mit „Speichern“ gilt alles sofort für neue Ausdrucke.',
    'Standardtexte für Angebote getrennt für Deutsch und Englisch pflegen.',
  ]],
  ['/profil', 'Profil', 'Eigenes Konto.', ['Passwort ändern und Outlook-Kalender abonnieren.']],
  ['/', 'Dashboard', 'Tagesüberblick für Vertrieb und Geschäftsführung.', [
    'Kennzahlen anklicken führt zur passenden Liste. Fällige Aufgaben und Hinweise (Glocke) zuerst abarbeiten.',
    'Für Berichte nach Kunde, Maschinengröße oder Absagegründen: Menü „Auswertungen“.',
  ]],
]

export default function PageHelp() {
  const { pathname } = useLocation()
  const entry = HELP.find(([p]) => (p === '/' ? pathname === '/' : p.endsWith('/') ? pathname.startsWith(p) : pathname === p))
  const key = entry ? `help:${entry[0]}` : null
  const [, force] = useState(0)
  if (!entry) return null
  let open = true
  try { open = localStorage.getItem(key) !== 'zu' } catch { /* ohne Speicher immer offen */ }
  const [, title, purpose, steps] = entry
  return (
    <div className="page-help-wrap"><details key={key} className="page-help" open={open} onToggle={(e) => {
      try { localStorage.setItem(key, e.currentTarget.open ? 'auf' : 'zu') } catch { /* egal */ }
      force((x) => x + 1)
    }}>
      <summary>So arbeiten Sie hier: {title}</summary>
      <p>{purpose}</p>
      <ol>{steps.map((s) => <li key={s}>{s}</li>)}</ol>
    </details></div>
  )
}
