# Blueprints from Tomorrow – Konzept & Skill-Entwurf

Arbeitstitel: Blueprints from Tomorrow. Non-Profit-Projekt. Ein Zeitreise-Rollenspiel, das als Skill (Markdown-Dateien) in beliebige Chatbots und Voice-Agenten geladen wird.

## Idee
Der Spieler reist als er selbst in die Vergangenheit, meist in den eigenen Kulturkreis. Er muss sich zu wichtigen Personen (Gelehrte, Anführer, Könige) durcharbeiten und sein Wissen über Naturwissenschaft, Technologie, Hygiene, Institutionen und Rechtsstaat anwenden. Ziel: herausfinden, wie viel man von der heutigen Zivilisation wirklich versteht – etwa ob man einer Epoche eine Dampfmaschine erklären und bauen lassen kann. Gesprächspartner sind Ingenieure, Handwerker, Chemiker und Alchemisten der Zeit.

## Verbreitung
- Keine eigene App: weniger Reibung, gleiche Möglichkeiten.
- Skill-Dateien auf GitHub, eigene Domain zeigt darauf. Start per „Lade Blueprints from Tomorrow“.
- Teilen von Kampagnen zuerst als Text (Kampagnen-File) und Bild (Visualisierung). Supabase-Backend erst später, falls nötig.
- Jeder kann eigene Versionen und Editionen herausbringen; alle werden auf der Webseite gesammelt.

## Kampagnenstart und Standards
Grundsatz: gut gewählte Standards statt vieler Menüs. Zusatzmodule nur bei Bedarf nachladen.
- Abgefragt werden nur: Ort/Epoche (oder vordefinierte Kampagne) und Schwierigkeit.
- Standard-Spielfigur: man selbst, unvorbereitet, mit dem, was man gerade bei sich trägt (Handy, Schlüssel, Geldbörse …). Bezeichnung dafür noch offen, etwa „Rucksack“.
- Aufenthaltsdauer: ein Tag, ein Monat, ein Jahr oder bis zum Lebensende. Standard: ein Jahr. Der Spieler weiß, wie lange er hat.
- Optional: soziale RPG-Ebene (Gunst des Herrschers, Intrigen, Quests). Wer nur Technikverständnis testen will, schaltet sie ab.

## Schwierigkeitsachsen
- Hinweise: leicht (direkte Hinweise), mittel (beiläufige Details, die man selbst verknüpft), schwer (keine Hinweise). Hinweise dürfen nicht zu offensichtlich sein.
- Widerstand der Gelehrten/Ingenieure: einstellbar. Ob Vorführungen oder Experimente nötig sind, entscheidet die KI situativ – je nach Technologie und Schwierigkeit.
- Sprache: eigene Achse, steht im Skill, wird beim Start aber nicht extra erwähnt. Bei „schwer“ automatisch aktiv, sonst nur auf Wunsch. Stufen: keine Barriere, keine Fachbegriffe, verwandte Sprache (Bruchstücke, Missverständnisse), Dolmetscher in-universe, gar kein Verständnis.

## Aufhänger
- Standard: Unfall mit Nachricht, dass man nach Ablauf der Frist zurückkehrt.
- Manche vordefinierte Kampagnen: Auftrag aus der Zukunft. Verworfen: Forschungsexperiment als Aufhänger.

## Spielmechanik
- Die Welt reagiert von sich aus: Ereignisse wie Seuchen, Intrigen, Inquisition, Ressourcen- und Zeitdruck.
- Falsches Wissen hat Folgen: Die Leute bauen es so, wie man es erklärt hat. Aufgelöst wird erst in der Auswertung.
- Mitgebrachte Gegenstände sind echte Ressourcen (z. B. Handyakku leert sich).
- Abschluss: „Was hast du bewirkt?“ – kurze Erzählung, wie sich die Geschichte verändert hat.
- Auswertung: was richtig erklärt wurde, wo man danebenlag, was man nachlesen kann.
- Vordefinierte Kampagnen, z. B. Florenz 1490 (Pest, Medici), Wien 1683 (Belagerung). Weitere folgen.

## Technologiebaum
- Ausführliche Hauptdatei (z. B. YAML) mit allen Technologien, Abhängigkeiten, Jahreszahlen, Personen, Regionen und Quellen. Daraus wird automatisch eine kompakte Markdown-Fassung für das Modell erzeugt.
- Gemeinsames Grundgerüst für alle Regionen, dazu pro Epoche und Region eine Datei mit dem Stand.
- Pro Technologie mehrere Dimensionen: Wissen, Nutzung (richtig, falsch, gar nicht – existiert etwas, wird aber nicht richtig verwendet?), Herstellbarkeit, Akzeptanz.
- Wissensstufen, z. B.: unbekannt, Idee/Gerücht, theoretisch beschrieben, handwerklich im Einsatz, breit verbreitet.
- Hinweis, wo es eine Technologie anderswo schon gibt (z. B. Papier in China) – Stoff für Quests.
- Verschiedene Kulturkreise berücksichtigen (Europa, China, Amerika …).
- Kontextbudget: 5.000–10.000 Tokens sind in Ordnung.

## Kampagnen-File und Tracking
- Die KI schreibt den Kampagnenstand laufend mit: Ort, Zeit, Personen, Einstellungen, Fortschritt im Technologiebaum.
- Ein mitgeliefertes Skript visualisiert daraus den Technologiebaum. Landkarte als optionales Modul.

## Versionierung
- Versionierung über Git.
- Jedes Kampagnen-File speichert die Skill-Version, mit der es gestartet wurde.
- Migrationsguide für brechende Änderungen, immer schrittweise von einer Version zur nächsten.

## Name und Domain
- Verworfen: Anachronist (vergeben), Hindsight Engine (Nähe zum Spiel „Hindsight“), PastForward (klingt wie „fast forward“, schlecht für Spracherkennung).
- Kriterien: international, aus gängigen Wörtern, gut für Speech-to-Text.
- Favorit: Blueprints from Tomorrow – kein Spiel und keine Marke mit diesem Namen gefunden.
- Domain: blueprintsfromtomorrow.com vermutlich frei, bei Cloudflare prüfen. .game kostet laut TLD-List ca. 265–749 $, zu teuer; .games ab ca. 8 $.

## Erkenntnisse aus dem Testlauf
Erster Testlauf: Florenz 1490, Gespräch mit Marsilio Ficino, Thema Pest, Hinweise auf „mittel“.
- Figuren dürfen Fragen nicht wiederholen. Lösung über besseren Prompt und laufend mitgeschriebenen Stand.
- Die KI aktualisiert das Kampagnen-File nach jeder wichtigen Szene.
- Die KI löst Ereignisse von sich aus aus, statt nur zu reagieren.
- Hinweise waren zu offensichtlich (tote Ratten) – daraus entstand die Hinweis-Achse.
- Im Voice-Modus beim Autofahren: Pausen des Spielers nicht sofort füllen, kurze Antworten. Plattform-Grenzen werden akzeptiert.
- Gut funktioniert hat: mitgebrachte Gegenstände als Beweis (Handy, Autoschlüssel), Anknüpfen an Wissen der Zeit (Varro, Aqua vitae, Seife aus Venedig).

## Verwandte Projekte
- TimeFall (Bot auf Poe): Zeitreise-Textspiel, Figur mit Beruf, Fokus auf Überleben, Vertrauen und Empathie, 15 historische Szenarien plus offene Welt, kostet Poe-Punkte. Unterschied: kein Fokus auf Anwenden und Prüfen des eigenen Wissens, plattformgebunden.
- The Anachronist: ein Hackathon-Projekt (3D) und ein Interactive-Fiction-Spiel mit fremder Spielfigur.
- Anachrony (Brettspiel) und Hindsight (Erzählspiel von Annapurna): nur der Name ist nah, das Konzept nicht.
- Fazit: Der Kern – man selbst, eigenes Wissen, Technologiebaum, Auswertung – ist bisher nicht besetzt.

## Weitere Namenskandidaten
- Seeds from Tomorrow: frei, aber Verwechslung mit „Seeds for Tomorrow“ (Marke von Galena Genetics) und vielen Saatgutprojekten.
- From Tomorrow: kein Spiel gefunden, aber „Tomorrow“ ist stark belegt.
- Lessons from Tomorrow, Ideas from Tomorrow: gut verständlich, aber eventuell zu allgemein.
- Weitere: Recipes, Tinkerers, Envoy, Alchemy, Inventions, Secrets, Visitor from Tomorrow.
- Kriterium dazu: Name soll mit dem Zusatz „Spiel“ bzw. „game“ gut auffindbar sein.

## Weitere Ideen
- Lizenz festlegen, passend zum Non-Profit- und Open-Source-Gedanken (z. B. CC BY-SA für Inhalte, MIT für Skripte).
- Beiträge der Community über Pull Requests: neue Epochen, Regionen, Kampagnen, Korrekturen am Technologiebaum.
- Quellenangaben im Technologiebaum, damit die Auswertung auf echte Literatur verweisen kann.
- Skill mehrsprachig anlegen: Regeln auf Englisch, Spielsprache frei wählbar.
- Leitlinie für den Umgang mit Gewalt, Krankheit und Vorurteilen vergangener Epochen.
- Kurze Zusammenfassung beim Fortsetzen einer Kampagne („Was bisher geschah“).
- Test mit mehreren Modellen und Plattformen, um zu prüfen, wie gut der Skill überall läuft.

## Offene Punkte
- Domain prüfen und registrieren.
- Bezeichnung für mitgebrachte Gegenstände. (Im Skill vorerst: „Pockets“.)
- Weitere vordefinierte Kampagnen.
- ~~Repo anlegen, Skill-Datei ausformulieren, Technologiebaum für erste Epoche anlegen, Visualisierungsskript.~~ Erledigt in v0.1.0.
