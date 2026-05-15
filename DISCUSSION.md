# DISCUSSION.md — Zürich Tram Flow

Analyse-Diskussion zu den Plots und Befunden der `03_analysis_*` Notebooks.

**Format jedes Eintrags:**
> **[Autor | Datum]** — Analyse-Text

Wenn der letzte Eintrag zu einem Thema nicht von Thomas ist: vorherige Einträge einbeziehen und
mit aktuellen Informationen Stellung beziehen.

---

## 03_analysis_target — Delay Target Analysis

### T1 — Delay Overview Per Year
*(Bar Chart: Ø Arrival Delay / Departure Delay / Delay Delta je Jahr)*

> **[Thomas | 2026-05-14]**
> Der Jahresvergleich zeigt einen klaren Aufwärtstrend in allen drei Delay-Größen —
> besonders auffällig ist `delay_delta`: von +4.4s (2023) auf +7.7s (2025), beinahe eine
> Verdopplung in drei Jahren.
>
> Mathematisch bedeutet das: Pro Halt verliert das System im Mittel jedes Jahr rund 1.5s mehr.
> Bei einer typischen Fahrt mit 15 Halten und 2–3 Fahrten pro Stunde summiert sich das
> auf ~3 Minuten Mehrbelastung pro Fahrt im Jahr 2025 gegenüber 2023. Das ist kein Rauschen —
> das ist ein strukturelles Signal.
>
> Mögliche Ursachen (zu vertiefen): (1) wachsendes Fahrgastaufkommen verlängert Haltezeiten,
> (2) Netzausbau 2023/24 erhöht Systemkomplexität, (3) zunehmende urbane Verkehrsdichte.
> Wichtig für die Modellierung: `year` sollte als Feature geprüft werden, da die Grundlinie
> sich von Jahr zu Jahr verschiebt. Auch die Wahl des Test-Jahres 2025 als "härterer" Test
> ist durch diesen Trend gut begründet.

> **[Michael | 2026-05-14]**
> Thomas' Trendinterpretation ist korrekt und gut begründet — ich ergänze aus technischer Sicht.
>
> Ein Detail das im Code auffällt: `lf_all` kombiniert Train (2023–2024) und Test (2025) via
> `pl.concat([pl.scan_parquet(TRAIN), pl.scan_parquet(TEST)])`. Das ist für diesen Jahresvergleich
> bewusst richtig — wir wollen alle drei Jahre sehen. Für alle anderen Analysen in diesem Notebook
> gilt aber: `lf` zeigt nur Train. Das muss beim Interpretieren der anderen Plots mitgedacht werden.
>
> Zur Feature-Empfehlung `year`: Ich würde `year` nicht direkt als Integer-Feature ins Modell
> nehmen — das würde dem Modell signalisieren "2025 > 2024 > 2023" als ordinale Skala, was
> inhaltlich stimmt, aber bei zukünftigen Jahreszahlen extrapoliert. Besser: `year` als
> kategoriales Feature (One-Hot) oder den Trend durch andere erklärende Features (Wetter, Events,
> Linienstruktur) indirekt abbilden. Wenn `year` nötig ist, dann als Indikator für Datendrift im
> Monitoring — nicht als Modell-Feature in Production.

---

### T2 — Delay Distribution
*(3 Histogramme: Arrival Delay · Departure Delay · Delay Delta — Sample 100k, geclippt ±300/600s)*

> **[Thomas | 2026-05-14]**
> Alle drei Verteilungen sind rechtsschief — das ist für Verspätungsdaten mathematisch
> erwartet: die Untergrenze ist durch das System bounded (Trams können nicht unbegrenzt
> früh ankommen), die Obergrenze ist konzeptuell offen.
>
> Das wichtigste Ergebnis ist die Diskrepanz bei `delay_delta`: der Notebook-Kommentar
> weist korrekt darauf hin, dass `median(A−B) ≠ median(A) − median(B)`. Das ist ein
> Jensen's-Inequality-Effekt bei asymmetrischen Verteilungen — kein Datenfehler.
>
> Die Frühankünfte bis −200s (trotz System-Tendenz zur Verspätung) deuten auf
> Terminus-Effekte hin: Trams warten am Wendepunkt, starten dann pünktlich oder früh,
> was die Ankunftszeit am ersten regulären Halt drückt. Das ist räumlich prüfbar
> (`03_analysis_spatial`).
>
> Für die Modellierung: Die Rechtsschiefe spricht dafür, den Target entweder zu
> log-transformieren (falls RMSE als Loss) oder einen quantilenbasierten Loss zu wählen,
> um die Dominanz der Extremausreißer zu dämpfen. XGBoost kann das, aber die
> Entscheidung sollte explizit getroffen werden.

> **[Michael | 2026-05-14]**
> Thomas' Empfehlungen zur Log-Transformation und quantilenbasiertem Loss sind der
> richtige Denkrahmen. Aus Implementierungssicht ein konkreter Hinweis: XGBoost's
> `objective='reg:tweedie'` ist für rechtschiefe, nicht-negative Targets (nach Shift um
> den Minimalwert) eine robustere Wahl als `reg:squarederror` und benötigt keine manuelle
> Log-Transformation des Targets — was den Pipeline-Code deutlich einfacher macht.
>
> Technisch wichtig zum Clip `(-300, 600)` im Plot: Das ist nur für die Visualisierung —
> die Aggregationen laufen auf `lf` (LazyFrame) ohne Clip. Das ist korrekt so und sollte
> als Konvention beibehalten werden. Wer den Plot-Code liest, sollte aber wissen dass
> der y-Achsen-Clip keine Aussage über die echten Extremwerte macht.
>
> Die Jensen's-Inequality-Notiz im Notebook-Kommentar ist ein guter Lernmoment. Für
> die spätere Modell-Evaluation relevant: Wenn wir RMSE auf dem gecollect'en Test-Set
> berechnen, dominieren die Extremausreißer die Metrik überproportional. Empfehle
> zusätzlich MAE und den Median Absolute Error auszuweisen — letzterer ist robust gegen
> Ausreißer und gibt ein ehrlicheres Bild der "normalen" Modellgüte.

---

### T3 — On-Time Performance (OTP)
*(Links: Arrival vs Departure — OTP/Late/Early. Rechts: Delay Delta — Recovering/Neutral/Growing)*

> **[Thomas | 2026-05-14]**
> 85–87% OTP ist für ein innerstädtisches Straßenbahnnetz im offenen Verkehr ein solider
> Wert — Zürich liegt hier im europäischen Spitzenfeld. Die fast symmetrische Parität
> zwischen Arrival- und Departure-OTP (~86% vs ~87%) zeigt, dass die Haltezeiten im
> Durchschnitt gut kontrolliert sind.
>
> Das kritische Signal steckt im rechten Chart: 70% der Halte bauen Verspätung auf,
> nur 27% recovern — ein Verhältnis von fast 3:1. Das ist ein starker Hinweis auf
> systematisch zu knapp kalkulierte Fahrplanpuffer. Für ein gut funktionierendes Netz
> würde man ein Verhältnis von ~50:50 erwarten.
>
> Besonders bemerkenswert: die 0.1% Frühankünfte über 120s. Das ist extrem gering und
> zeigt, dass Fahrer sehr diszipliniert darin sind, Fahrgäste nicht durch Frühausfahrten
> zu verpassen — eine operationelle Exzellenz die sich in den Daten widerspiegelt.
>
> Modellierer-Implikation: Der Zielwert `arrival_delay > 120s` als binäre
> Klassifikation (On-Time vs. Late) ist ein sauberes Label für ein späteres
> Klassifikationsmodell als Alternative zum Regressionsziel.

> **[Michael | 2026-05-14]**
> Thomas' Beobachtung zum 3:1-Verhältnis (Growing vs Recovering) ist das stärkste
> strukturelle Signal dieses Notebooks — ich stimme zu. Aus Datenperspektive möchte ich
> aber die Berechnungslogik im Code prüfen: `delta_neutral` wird mit `== 0` berechnet.
> Bei Float-Arithmetik ist exakt 0.0 selten — das wird in der Praxis nur Zeilen treffen
> wo Arrival und Departure identisch erfasst wurden (z.B. Terminus-Stops). Die echte
> "neutrale" Kategorie sollte eher `|delta| < 5s` sein. Das ändert die Aussage nicht
> grundlegend, macht die Kategorien aber robuster gegenüber Messrauschen.
>
> Zur Klassifikationsidee: `arrival_delay > 120s` als binäres Label ist operationell
> sauber — aber beim Klassenungleichgewicht aufpassen: ~13% positive Klasse (late).
> In sklearn's `XGBClassifier` dann `scale_pos_weight = 87/13 ≈ 6.7` setzen, sonst
> optimiert das Modell auf Accuracy und sagt fast immer "on-time". Das ist ein
> klassischer Implementierungsfehler der bei imbalancierten Labels auftritt.

---

### T4 — Arrival vs Departure Delay (Boxplot)
*(Boxplot aller 3 Delay-Spalten nebeneinander — Sample 100k, geclippt)*

> **[Thomas | 2026-05-14]**
> Die Boxplot-Struktur erzählt die Geschichte des Systems in drei Körpern:
> `departure_delay` liegt konsistent über `arrival_delay` (IQR und Median) — Halte
> kosten Zeit, netto. `delay_delta` zeigt eine erstaunlich symmetrische Box um 0,
> aber mit extrem langen Whiskern in beide Richtungen.
>
> Die mathematische Aussage der langen Whisker von `delay_delta`: Es gibt
> Haltepunkte, die regelmäßig große Zeitmengen absorbieren oder freisetzen — das sind
> nicht "normale" Halte. Wir sehen hier die Bimodalität des Netzbetriebs:
> einerseits Standardhalte (~0s Nettoverlust), andererseits kritische Knotenpunkte
> mit starker Konzentration von Verspätungsdynamik. Diese identifiziert der
> Spatial-Notebook (`03_analysis_spatial`, Plot S1/S2).
>
> Der Cascade-Mechanismus ist statistisch ablesar: Ein Tram das mit hohem
> `arrival_delay` ankommt, hat am Halt tendenziell mehr wartende Fahrgäste
> (Aufstauungseffekt), verlängert dadurch die Haltezeit und erzeugt positives
> `delay_delta`. Dieser Selbstverstärkungsmechanismus ist das Kernproblem der
> Timetable-Planung und sollte im Modell durch Lag-Features abgebildet werden.

> **[Michael | 2026-05-14]**
> Thomas beschreibt den Cascade-Mechanismus korrekt — aus Implementierungssicht ist
> das der schwierigste Teil der Feature Engineering Phase. `departure_delay` als Feature
> für `arrival_delay` wäre technisch trivial, aber es ist **Leakage**: Beim Zeitpunkt
> der Vorhersage (vor Ankunft) kennen wir `departure_delay` des aktuellen Stops noch nicht.
>
> Konkrete Lag-Feature Strategie die das verhindert: `arrival_delay` des *vorherigen*
> Stops als Feature — das ist zum Vorhersagezeitpunkt bekannt. In Polars:
> ```python
> lf.sort(["trip_id", "stop_sequence"])
>    .with_columns(pl.col("arrival_delay").shift(1).over("trip_id").alias("prev_stop_delay"))
> ```
> Das erfordert `trip_id` + `stop_sequence` — beides ist im GTFS-Join vorhanden.
> BACKLOG-Item #8 (Segment-Fahrzeit-Analyse) und der `trip_id`-Hinweis in T5 adressieren
> genau das. Dieser Lag-Feature wäre vermutlich das stärkste einzelne Feature im Modell.
>
> Zur Clip-Frage im Boxplot: Der Clip auf `(-300, 600)` ist für den Plot vertretbar,
> aber die Whisker werden durch den Clip beschnitten — wir sehen nicht die echten
> Q1.5×IQR-Whisker sondern gecappte Werte. Das sollte im Plot-Titel explizit stehen
> (was es tut: "clipped −300 to +600s"). Gut so.

---

### T5 — Cancellations (Gesamtquote)
*(Log-Output: canceled = False ~96.4%, True ~3.6%)*

> **[Thomas | 2026-05-14]**
> 3.6% = ~2.2 Mio. ausgefallene Halt-Ereignisse über 3 Jahre. Das klingt marginal,
> ist aber erheblich: Bei durchschnittlich ~5.000 Halt-Ereignissen pro Tag im VBZ
> Tramnetz entspricht das ~180 Ausfalls-Ereignissen täglich.
>
> Ohne `trip_id` bleibt offen: Sind das einzelne Skip-Stops (Tram hält nicht — im
> Schweizer Betrieb selten) oder vollständige Fahrtausfälle? Die Ausfallquote von
> ~3.6% ist für ein westeuropäisches Tramnetz eher hoch und lohnt sich zu hinterfragen.
>
> Vermutung: Ein Teil der `canceled = True` Einträge könnte aus der Datenerfassung
> stammen — Fahrten die in den IST-Daten erfasst wurden obwohl sie nicht stattfanden
> (Planungsartefakte). Die Verteilung nach Linie (T8) wird das klären.

> **[Michael | 2026-05-14]**
> Thomas' Vermutung zu Planungsartefakten ist plausibel. Eine einfache Prüfung die
> ich empfehle: Distribution von `canceled = True` nach Uhrzeit. Wenn Ausfälle
> überproportional in der ersten oder letzten Stunde des Betriebstages auftreten,
> deutet das auf Betriebsstart/-end-Artefakte hin. In Polars:
> ```python
> lf.filter(pl.col("canceled")).group_by("hour").agg(pl.len()).sort("hour")
> ```
>
> Zur CLAUDE.md-Entscheidung: "`canceled = True` Zeilen behalten — sind wichtige
> Extremfälle für das Modell" — das stimmt für die Analyse-Phase. Für das Prediction-
> Modell müssen wir aber klären: Wollen wir Cancellations vorhersagen (Klassifikation)
> oder den `arrival_delay` bei nicht-gecancelten Trips (Regression)? Falls letzteres,
> müssen `canceled = True` Zeilen *aus dem Regression-Target* herausgefiltert werden,
> dürfen aber als eigene Zielvariable im Klassifikationsmodell bleiben. Das ist eine
> Modellarchitektur-Entscheidung die jetzt dokumentiert werden sollte.

---

### T6 — Delay Delta Distribution Detail
*(Histogramm ±180s — feinauflösend)*

> **[Thomas | 2026-05-14]**
> Die Detailansicht von `delay_delta` im engen Bereich ±180s zeigt eine
> annähernd normalverteilte Grundform mit leichter Rechtsverschiebung. Der Modus
> liegt leicht positiv von 0 — nicht bei 0. Das ist präzise die Timetable-Spannung
> in einer einzigen Zahl.
>
> Mathematisch interpretiert: Der Halt-Prozess ist ein additiver Noise-Mechanismus
> mit positivem Bias. Die Bias-Komponente (geschätzt ~3–5s am Modus) ist der
> Anteil, den die Fahrplanrevision korrigieren müsste, indem Pufferzeiten
> standardmäßig leicht erhöht werden.
>
> Die fast gaußförmige Grundstruktur ist eine wertvolle Information für das Modell:
> Features die `delay_delta` bei normalem Betrieb vorhersagen, müssen vor allem
> die Mittelwert-Verschiebung erklären, nicht die Extremwerte. Die Extremwerte
> erklären sich durch externe Faktoren (Wetter, Events, räumliche Engpässe) —
> genau die Features der anderen Analysis-Notebooks.

> **[Michael | 2026-05-14]**
> Ich kann Thomas' Gauss-Beschreibung aus dem Code heraus bestätigen: Das Histogram
> verwendet 120 Bins auf ±180s, was 3s Binbreite ergibt — fein genug um den Modus
> präzise zu lokalisieren. Thomas schätzt ihn bei ~3–5s positiv von 0.
>
> Konkrete Messung wäre: `SAMPLE_SMALL["delay_delta"].mode()` oder die häufigste
> Bin-Mitte aus dem Histogramm. Das sollte in eine Beobachtungszelle, nicht nur als
> visuelle Schätzung bleiben.
>
> Thomas' Zweiteilung (normale Betriebsvarianz vs. externe Faktoren) ist konzeptuell
> richtig und hat direkte Implikationen für die Feature-Auswahl: Wenn die Basis-Varianz
> ~normalverteilt ist, sind die Residuen des Modells nach Abzug der erklärenden Features
> möglicherweise ebenfalls annähernd normal — das würde klassische lineare Regression
> als Baseline-Modell sinnvoll machen, bevor wir zu XGBoost wechseln. Eine OLS-Baseline
> auf den wichtigsten Features gibt uns einen kostenlosen Referenzpunkt.

---

### T7 — Extreme Values
*(Tabelle: Anteil Halte jenseits 120s / 300s / 600s / 1800s Schwellwert)*

> **[Thomas | 2026-05-14]**
> Die Schwellwert-Tabelle quantifiziert den Tail der Delay-Verteilung. Das Abfallen
> der Anteile über die Schwellwerte folgt erwartungsgemäß einem Power-Law-ähnlichen
> Muster — typisch für Wartezeitenverteilungen in realen Transportsystemen.
>
> Die ausgeprägte Asymmetrie zwischen "zu spät" und "zu früh" bei hohen Schwellwerten
> ist das entscheidende Signal: Bei 600s (10 min) gibt es praktisch keine Frühankünfte
> mehr, aber noch messbare Verspätungen. Das bestätigt die Richtungsasymmetrie des
> Systems: Das Netz hat operative Böden (Fahrer halten bewusst Mindestfahrzeiten ein),
> aber keine operativen Obergrenzen auf Verspätungen.
>
> Für das Modell: Der Schwellwert 120s (2 min) als OTP-Definition ist der
> Branchen-Standard — aber für Kettenverspätungs-Prognose könnte der Schwellwert
> 300s (5 min) als "kritisch" das relevantere Label sein. Zu diskutieren.

> **[Michael | 2026-05-14]**
> Ich stimme Thomas zu bei beiden Schwellwert-Optionen (120s und 300s). Für die
> Entscheidung empfehle ich einen pragmatischen Blick auf die Klassengrößen:
>
> Aus T4 wissen wir: ~13% der Halte haben `arrival_delay > 120s`. Wenn 300s die Grenze
> wäre, wären es deutlich weniger — vielleicht 3–5%. Das verschiebt das
> Klassenungleichgewicht von 1:6.7 auf circa 1:20, was die Modellierung schwieriger
> macht. Für ein erstes Modell ist 120s daher der robustere Einstieg.
>
> Zur Tabellen-Implementierung im Code: Der Loop über `thresholds` ist funktional
> korrekt, aber er triggert 4 separate Polars `collect()`-Aufrufe auf dem LazyFrame.
> Das kann in einem einzigen Pass berechnet werden:
> ```python
> lf.select([
>     (pl.col("arrival_delay") > t).sum().alias(f"late_{t}s") for t in thresholds
> ] + [(pl.col("arrival_delay") < -t).sum().alias(f"early_{t}s") for t in thresholds])
> .collect()
> ```
> Bei ~60M Zeilen macht das einen messbaren Unterschied in der Laufzeit.

---

### T8 — Cancellations by Line
*(Horizontales Bar-Chart: Ausfallquote Top-15 Linien)*

> **[Thomas | 2026-05-14]**
> Die linienspezifische Ausfallquote ist einer der inhaltlich reichsten Plots.
> Linien mit >1.5× Durchschnitt (im Code rot markiert) zeigen strukturelle
> Schwächen — entweder in der Infrastruktur, der Fahrzeugdisposition oder der
> Fahrzeitplanung.
>
> Erwartung: Die Sonder- und Nachtlinien (50/51/E, die in EDA bewusst behalten wurden)
> erscheinen vermutlich unter den Top-Ausreißern — nicht weil sie schlechter betrieben
> werden, sondern weil bei niedrigerer Taktfrequenz jeder Ausfall überproportional ins
> Gewicht fällt. Das macht `line_name` zu einem wichtigen Feature im Modell: es
> kodiert implizit Taktfrequenz, Streckenlänge und Fahrzeugtypzuverlässigkeit.
>
> Modellierer-Empfehlung: Target-Encoding für `line_name` könnte besser sein als
> One-Hot, da die Kardinalität moderat ist (~15–20 Linien) und der Zusammenhang
> mit Verspätung nicht monoton ist.

> **[Michael | 2026-05-14]**
> Thomas' Target-Encoding-Empfehlung ist korrekt — ich ergänze den Leakage-Schutz.
> Target-Encoding muss zwingend **nur auf den Trainingsdaten** berechnet und dann auf
> Test angewendet werden. In sklearn geht das mit `TargetEncoder` (ab 1.3) mit
> `cv=5` für Leave-One-Out-Approximation. In der Polars-Pipeline muss sichergestellt
> sein dass die Encoding-Map vor dem `collect()` des Test-Sets gespeichert wird.
>
> Zur Visualisierung: Das horizontale Barplot mit `invert_yaxis()` ist die richtige
> Wahl für lange Linienlabels. Der Schwellwert `avg_rate * 1.5` für die Rot-Markierung
> ist aber hartcodiert in einem List Comprehension — bei einem Report-Notebook sollte
> das als named constant leben: `CANCELLATION_THRESHOLD = 1.5`. Das macht die
> Schwellenwert-Wahl explizit und reviewbar.
>
> Inhaltlich: Ich würde neben der Ausfallrate auch `total` (Trips pro Linie) in der
> Visualisierung zeigen — eine Linie mit 20% Ausfallrate bei 1.000 Trips ist weniger
> kritisch als eine mit 5% bei 100.000 Trips. Ein zweiter Balken oder eine Bubble-Size
> würde das direkt kommunizieren.

---

### T9 — Delay Delta Monthly Trend
*(Linienchart: monatliches Ø delay_delta über 2023–2025)*

> **[Thomas | 2026-05-14]**
> Der monatliche Verlauf über 36 Monate ist das stärkste Kontext-Signal für die
> Modellierung. Drei Fragen die dieser Chart beantwortet:
>
> (1) **Saisonalität:** Wintermonate sollten höhere delta-Werte zeigen (Wettereffekte,
> Heizungsstart → langsamerer Passagierdurchsatz). Ein klares Saisonmuster würde
> `month` und `season` als starke Features validieren.
>
> (2) **Trend:** Wenn 2025 konsistent über 2023-Niveau liegt, bestätigt das den
> Jahres-Vergleich in T1 und zeigt: kein Mean-Reversion, sondern struktureller Drift.
>
> (3) **Anomalien:** Einzelne Monate deutlich über dem Trend (Events? Bauarbeiten?)
> sollten in `03_analysis_events` ihre Erklärung finden. Die Jahrestrennlinien
> (gestrichelte vertikale Linien bei 2024-01 und 2025-01) sind wichtig um
> den temporalen Split visuell zu überprüfen: 2025-Monate als Test-Set sollten
> sichtbar "anders" sein als 2023/24.
>
> Mathematische Note: Monatsmittelwerte mitteln über ~1.5–2 Mio. Einträge — die
> Konfidenzintervalle um diese Mittelwerte sind winzig. Selbst kleine visuell
> erkennbare Unterschiede sind statistisch hochsignifikant.

> **[Michael | 2026-05-14]**
> Thomas' drei Fragen sind gut strukturiert. Technisch zum Code: Die Aggregation
> läuft korrekt über `lf_all` (Train + Test) und konvertiert zu Pandas für die
> Zeitreihen-Plot-Logik. Der `pd.to_datetime(monthly[["year","month"]].assign(day=1))`
> Trick ist sauber und idiomatisch.
>
> Ein Verbesserungsvorschlag für die Visualisierung: Aktuell ist die Linie ohne
> Unsicherheitsband. Da Thomas korrekt anmerkt dass die CI winzig sind, könnte man
> stattdessen ein **7-Monats Rolling Average** als zweite Linie überlagern — das macht
> den langfristigen Trend sichtbar ohne Konfidenzintervalle zu benötigen. In Pandas:
> `monthly["delta_smooth"] = monthly["delta_mean"].rolling(7, center=True).mean()`
>
> Zur Anomalie-Erkennung: Eine einfache Z-Score-Markierung auf den Monatswerten
> würde Ausreißer-Monate automatisch flaggen, ohne auf das Events-Notebook warten
> zu müssen. Das wäre eine sinnvolle Ergänzung für diesen Plot als explorative
> Vorstufe: `|z| > 2` als Annotation direkt im Chart.

---

## 03_analysis_temporal — Temporal Analysis

> **Statushinweis [Thomas | 2026-05-14]:** Das Notebook ist in der Skeleton-Phase —
> die Aggregationscode-Zellen sind geschrieben, Visualisierungen und Observation-Zellen
> fehlen noch. Meine Einträge beschreiben erwartete Muster und analytische Hypothesen
> die nach Notebook-Ausführung validiert werden sollten.

> **[Michael | 2026-05-14]**
> Ich bestätige den Skeleton-Status aus dem Code. Die Aggregationen sind technisch
> korrekt: `group_by("hour").agg(mean)`, `group_by("weekday").agg(mean)` etc. sind
> saubere Polars-Abfragen die direkt ausführbar sind. Was fehlt sind Plots und
> Observation-Zellen — das ist der nächste Schritt.
>
> Implementierungshinweis für alle vier Temporal-Plots: Da alle vier eine ähnliche
> Struktur haben (Aggregat nach Zeit-Feature → Balken- oder Linienplot), lohnt es
> sich eine Hilfsfunktion zu schreiben statt den Plot-Code viermal zu kopieren:
> ```python
> def plot_delay_by_group(data, x_col, title, x_labels=None): ...
> ```
> Das hält den Notebook-Code DRY und macht künftige Anpassungen (z.B. Farbänderung)
> an einer Stelle pflegbar.

---

### TE1 — Hour of Day
*(Ø arrival_delay nach Stunde — aggregiert)*

> **[Thomas | 2026-05-14]**
> Der Stunden-Verlauf wird die bekannteste Kurve des gesamten Projekts sein:
> zwei Peaks (Morgen ~7–9 Uhr, Abend ~16–19 Uhr), ein Tagesminimum am Mittag,
> niedrige Nacht-Werte. Das ist die HVZ-Struktur (Hauptverkehrszeit) in Reinform.
>
> Mathematisch interessant: Nicht der absolute Mittelwert ist das Signal, sondern
> der Verlauf der Standardabweichung über den Tag. In den HVZ-Stunden steigt
> vermutlich nicht nur die mittlere Verspätung, sondern auch ihre Varianz —
> das Netz wird nicht nur später, sondern auch unvorhersehbarer. Ein Modell das
> die Varianz unterschätzt, gibt in den kritischsten Stunden die schlechtesten
> Prognosen.
>
> Feature-Empfehlung: Sowohl `hour` als stete Variable als auch `is_rush_hour`
> als binäres Flag (bereits im Feature-Set geplant). Die zyklische Natur der
> Stunden sollte per sin/cos-Encoding behandelt werden um Mitternachts-Sprünge
> zu vermeiden.

> **[Michael | 2026-05-14]**
> Die Varianz-Beobachtung von Thomas ist wichtig — ich ergänze die Aggregation um
> `std`: Die aktuelle Aggregation berechnet nur `mean`. Um Thomas' Hypothese zu
> validieren (höhere Varianz in HVZ), muss `pl.col("arrival_delay").std()` ergänzt
> werden. Das ist eine einzeilige Änderung und liefert direkt die Information.
>
> Zum sin/cos-Encoding: Vollständige Zustimmung. `hour_sin = sin(2π × hour / 24)`,
> `hour_cos = cos(2π × hour / 24)` — das sollte in `02_preparation.ipynb`'s
> Feature Engineering Phase rein, nicht erst im Modell-Notebook. Es ist bereits
> Teil des geplanten Feature-Sets laut PROCESS_LOG. Überprüfen ob das tatsächlich
> umgesetzt ist wenn Preparation läuft.

---

### TE2 — Day of Week
*(Ø arrival_delay nach Wochentag — aggregiert)*

> **[Thomas | 2026-05-14]**
> Die Wochentag-Struktur folgt dem Pendelverhalten: Montag als Wochenstarter
> (hohe Verspätung, schlechte "Warm-up-Phase" des Netzes nach Wochenende),
> Freitag ebenfalls hoch (frühere Freizeit-Abfahrten überlagern Berufsverkehr).
> Samstag ist ambivalent: weniger Pendler, aber mehr Freizeitreisende die
> langsamer ein-/aussteigen und die Haltezeiten verlängern.
>
> Die Null-Hypothese für Sonntag: niedrigste Verspätung. Alternative: Wenn Events
> (Sonntagsveranstaltungen in Zürich) dominant sind, kann Sonntag höher liegen
> als erwartet.
>
> Für das Modell liefert `weekday` (0–6) einen nichtlinearen, nicht-monotonen
> Zusammenhang — genau der Typ von Struktur wo XGBoost Baumtiefe ausschöpft.
> Alternativ: Wochentag kategorisch als One-Hot (7 Kategorien — überschaubar).

> **[Michael | 2026-05-14]**
> Thomas' Analyse zur Nicht-Monotonie ist korrekt — One-Hot ist hier besser als
> Ordinal-Encoding, weil "Freitag > Donnerstag" nicht gilt. Die Wahl zwischen
> One-Hot (7 Spalten) und direkt im XGBoost als kategorisches Feature (`enable_categorical=True`)
> ist Implementierungsdetail, aber XGBoost's native kategorische Unterstützung seit
> v1.6 ist in der Regel besser als manuelle One-Hot, da XGBoost dann optimale
> Splits direkt auf der Kategorie findet.
>
> Ein Zusatz-Feature das ich empfehle: `is_weekend` (0/1) als binäres Flag neben
> `weekday` — das kodiert den stärksten strukturellen Bruch (Werktag vs. Wochenende)
> explizit. XGBoost würde das zwar aus `weekday` lernen, aber ein explizites Feature
> macht das Modell interpretierbarer und beschleunigt das Training.

---

### TE3 — Month
*(Ø arrival_delay nach Monat — aggregiert)*

> **[Thomas | 2026-05-14]**
> Die Monats-Kurve wird Saisonalität und Event-Kalender überlagert zeigen.
> Erwartung: Dezember/Januar als Wintermonate ganz oben (Schnee, Eis, Dunkelheit
> verlängert Einstiegsvorgänge), August als Event-Spitze (Street Parade — größtes
> Open-Air Europas findet in Zürich statt, zieht das gesamte Tramnetz in Mitleidenschaft).
>
> Zürich-spezifisch zu erwarten: April-Spitze (Sechseläuten — Altstadtbereich
> komplett gesperrt), September (Knabenschiessen). Diese Zürich-spezifischen Peaks
> sind nur erkennbar wenn man den Zürich-Eventkalender kennt — sie sollten sich mit
> der Events-Analyse decken.
>
> `month` und `season` sind zwei unterschiedliche Abstractions-Ebenen. Beide ins
> Modell zu nehmen erzeugt Multikollinearität — besser: `month` allein, da es
> die feingranularere Information trägt.

> **[Michael | 2026-05-14]**
> Thomas' Multikollinearität-Argument gilt technisch für lineare Modelle streng —
> bei XGBoost ist Multikollinearität weniger kritisch, da Bäume die Information
> ohnehin aus demjenigen Feature ziehen das den besseren Split ergibt. Trotzdem:
> `month` zu nehmen ist die sauberere Entscheidung, weil `season` keine zusätzliche
> Information trägt die nicht in `month` steckt.
>
> Für die sin/cos-Encoding-Frage: Analog zu `hour` sollte auch `month` zyklisch
> encodiert werden — Dezember (12) und Januar (1) liegen im echten Kalender nebeneinander,
> aber als Integer weit auseinander. `month_sin = sin(2π × month / 12)` schließt
> diese Lücke. Das ist besonders wichtig wenn das Modell Wintermuster lernen soll.

---

### TE4 — Season
*(Ø arrival_delay nach Saison — aggregiert)*

> **[Thomas | 2026-05-14]**
> Die Jahreszeiten-Aggregation ist konzeptuell gröber als `month`, macht aber
> die Wetter-Komponente sauber sichtbar: Sommer (Saison 3) sollte am besten
> abschneiden (gutes Wetter, helle Abende, kein Schnee/Eis). Winter (Saison 1)
> am schlechtesten.
>
> Die mathematische Frage: Ist die Winter/Sommer-Differenz statistisch signifikant
> über 3 Jahreswerte hinweg? Bei ~15–20 Mio. Beobachtungen pro Saison: ja,
> selbst kleinste Effekte sind signifikant. Die relevante Frage ist daher nicht
> "Ist es signifikant?" sondern "Ist die Effektgröße praktisch relevant?" —
> also: Wie viele Sekunden Unterschied sind für den Betrieb/das Modell material?
>
> Herbst (Saison 4) ist interessant: Laubfall in Zürich (Oktober) kann Bremseffekte
> auf Tramschienen erzeugen — ein sehr lokaler Effekt der in den Daten sichtbar
> werden könnte.

> **[Michael | 2026-05-14]**
> Thomas' Effektgröße-Argument ist methodisch exakt richtig — mit ~60M Zeilen
> wird jeder Unterschied >0.1s statistisch signifikant. Die praxisrelevante Frage
> ist die Effektgröße in Sekunden.
>
> Wenn dieser Plot läuft, empfehle ich Cohen's d zwischen Winter und Sommer zu
> berechnen: `d = (mean_winter - mean_summer) / pooled_std`. Das gibt eine
> normierte, interpretierbare Effektgröße unabhängig von der Stichprobengröße.
> d < 0.2 = vernachlässigbar, d > 0.5 = moderat, d > 0.8 = stark.
>
> Der Laubfall-Effekt (Oktober) ist ein interessantes Domain-Detail — ich würde
> ein `has_leaf_fall` Flag vorschlagen (Oktober + Niederschlag) als exploratives
> Feature. Wenn es im Modell keinen Beitrag liefert, fliegt es raus. Datentechnisch
> wäre das eine einzeilige Polars-Expression:
> `pl.when((pl.col("month") == 10) & pl.col("has_rain")).then(True).otherwise(False)`

---

### TE5 — Full Year Trend
*(Tages-aggregierte Zeitreihe 2023–2025)*

> **[Thomas | 2026-05-14]**
> Der vollständige Jahresverlauf auf Tagesebene ist der Kontext für alle anderen
> temporalen Analysen. Was hier als Tagesvariation erscheint, ist in Wirklichkeit
> die Überlagerung von mindestens vier Signalschichten: Wochentag-Zyklus,
> Saison-Trend, Event-Spikes, und langfristiger Drift (T1/T9).
>
> Für die Visualisierung empfehle ich ein 7-Tage Rolling Average über den
> Tagesdurchschnitt — das dämpft den Wochentag-Zyklus und macht den Saison-Trend
> und Anomalien sichtbar. Außerdem: Farbcodierung der Jahre um die Entwicklung
> 2023→2024→2025 visuell sofort erkennbar zu machen.
>
> Statistisch: Eine einfache lineare Regression auf die Tagesmittelwerte würde
> den Trend quantifizieren (Sekunden/Tag). Wenn dieser Trend statistisch signifikant
> ist (bei ~1000 Datenpunkten sehr wahrscheinlich), hat man ein starkes Argument
> für die Hypothese des strukturellen Fahrplan-Defizits.

> **[Michael | 2026-05-14]**
> Thomas' Rolling-Average-Empfehlung ist gut. Ich ergänze den Implementierungsweg:
> Die aktuelle Aggregation in `03_analysis_temporal` sammelt Tagesdurchschnitte in
> `yearly` (Variablenname ist leicht irreführend für Tagesdaten — sollte `daily` heißen).
> Das Rolling Average dann:
> ```python
> daily["avg_delay_7d"] = daily["avg_delay"].rolling(7, center=True, min_periods=4).mean()
> ```
>
> Zur linearen Regression: `scipy.stats.linregress(daily.index, daily["avg_delay"])`
> liefert Slope (s/Tag), R², und p-value in einer Zeile. Das Ergebnis direkt in den
> Chart-Titel: "Trend: +X.Xs/Tag (p<0.001)" — das ist ein starkes Statement für
> das Portfolio.
>
> Vorsicht: Die Tagesmittelwerte haben stark unterschiedliche Stichprobengrößen
> (Wochentage vs. Wochenende haben unterschiedliche Fahrtenzahlen). Eine gewichtete
> Regression (`weights=daily["n_trips"]`) wäre methodisch korrekter als ungewichtet.

---

## 03_analysis_weather — Weather Impact Analysis

> **Statushinweis [Thomas | 2026-05-14]:** Notebook in Skeleton-Phase — Aggregationen
> vorbereitet, Visualisierungen fehlen. Meine Einträge sind analytische Hypothesen
> auf Basis der EDA-Befunde (max. lineare Korrelation r=0.03 bei Wetter→Delay).

> **[Michael | 2026-05-14]**
> Ich bestätige den Skeleton-Status. Die Aggregationen sind technisch korrekt und
> laufen auf `lf` (Training-Set via `setup_analysis`). Ein wichtiger Hinweis für
> alle fünf Wetter-Plots: Die `count`-Spalte ist kritisch für die Interpretation.
> Ohne Angabe der Stichprobengröße im Plot sind Mittelwertvergleiche irreführend —
> besonders bei `has_snow` (seltener Fall). Empfehle für alle Wetter-Barplots:
> n als Annotation auf den Balken oder als sekundäre y-Achse.
>
> Die r=0.03 Korrelation aus der EDA bedeutet: Der lineare Anteil ist minimal.
> Das schließt nichtlineare Effekte nicht aus — die Wetter-Flags (`has_rain`,
> `has_heavy_rain` etc.) sind genau dafür konzipiert, Schwellenwert-Effekte zu
> kodieren die lineare Korrelation nicht erfasst.

---

### W1 — Rain Impact
*(Ø arrival_delay: has_rain True vs False)*

> **[Thomas | 2026-05-14]**
> Der Regen-Effekt ist der Basis-Wettertest. Erwartung: leicht höhere mittlere
> Verspätung bei `has_rain = True`, aber der Effekt ist laut EDA schwach (r≤0.03).
>
> Mathematisch entscheidend: Ein kleiner Unterschied in den Mittelwerten (z.B.
> +5s) ist bei ~60 Mio. Beobachtungen statistisch hochsignifikant — aber praktisch
> kaum relevant. Die richtige Frage ist: Verändert Regen die Verteilung der
> extremen Verspätungen? (Erhöht er die 90. Perzentile?) Das wäre der
> operationell relevante Regen-Effekt.
>
> Die EDA-Korrelation von r=0.03 zeigt: kein linearer Zusammenhang. XGBoost wird
> aber nichtlineare Schwellenwerte finden — z.B. `precipitation > 3mm/h` als
> kritischer Schwellwert, unter dem kaum Effekt, darüber messbarer Anstieg.

> **[Michael | 2026-05-14]**
> Thomas fragt nach der 90. Perzentile — das ist genau der richtige Ansatz.
> Die aktuelle Aggregation berechnet nur `mean`. Ergänzung:
> ```python
> lf.group_by("has_rain").agg([
>     pl.col("arrival_delay").mean().alias("avg_delay"),
>     pl.col("arrival_delay").quantile(0.9).alias("p90_delay"),
>     pl.len().alias("count")
> ])
> ```
> Wenn die 90. Perzentile bei Regen deutlich stärker steigt als der Mittelwert,
> ist das ein Tail-Effekt — für das Modell bedeutet das: `has_rain` ist kein guter
> Prädiktor für den durchschnittlichen Delay, aber ein guter Prädiktor für
> extreme Delays. Das beeinflusst die Loss-Wahl (Quantile Loss statt MSE).

---

### W2 — Heavy Rain Impact
*(Ø arrival_delay: has_heavy_rain True vs False — precipitation > 5mm)*

> **[Thomas | 2026-05-14]**
> Der Vergleich Rain vs Heavy Rain ist methodisch wichtig: Er testet ob der
> Wettereffekt einen Schwellenwert hat. Hypothese: `has_rain` zeigt minimalen
> Effekt, `has_heavy_rain` zeigt deutlich stärkeren Effekt — weil intensive
> Niederschläge Sicht, Bremsverhalten und Fahrgastdurchsatz gleichzeitig
> beeinträchtigen.
>
> Wenn `has_heavy_rain` einen merklich größeren Effekt hat als `has_rain`,
> ist das ein starkes Argument für nichtlineare Wettermodellierung. Die binären
> Flags (`has_rain`, `has_heavy_rain`) im Feature-Set sind dann gut gewählt —
> sie kodieren genau diese Schwelleneffekte für XGBoost.

> **[Michael | 2026-05-14]**
> Technischer Hinweis: `has_heavy_rain` und `has_rain` sind nicht disjunkt —
> wenn `has_heavy_rain = True`, ist `has_rain = True` per Definition auch True
> (Starkregen ist eine Teilmenge von Regen). Das Modell sieht also Korrelation
> zwischen den beiden Features. Das ist kein Problem für XGBoost (Bäume sind
> robust gegen Feature-Korrelation), sollte aber in der Feature-Dokumentation
> stehen.
>
> Für diesen Plot konkret: Der Vergleich `has_rain = False` vs `has_rain = True`
> ist informativer wenn zusätzlich nach `has_heavy_rain` aufgeteilt wird —
> also drei Gruppen: kein Regen / leichter Regen / Starkregen. Das zeigt den
> Gradienten des Effekts in einem einzigen Barplot.

---

### W3 — Wind Impact
*(Ø arrival_delay: is_windy True vs False — wind_speed > 40 km/h)*

> **[Thomas | 2026-05-14]**
> Windeffekte auf Trams sind physikalisch direkt: Seitenwind erhöht den
> Fahrwiderstand, Wind-Extremwerte können zu Notbremsungen führen. Der Effekt
> sollte bei 40 km/h messbarer werden als bei moderatem Wind.
>
> In Zürich relevant: Die Tallage schützt weite Teile des Netzes vor starkem Wind,
> aber Strecken am Seeufer (Quailinien) und auf Anhöhen könnten signifikant
> wind-sensitiver sein. Das wäre im Spatial-Notebook prüfbar: Windy days ×
> stop_location → welche Streckenabschnitte reagieren stärker?

> **[Michael | 2026-05-14]**
> Thomas' Interaktionsidee (Wind × Stop-Location) ist analytisch wertvoll.
> In Polars wäre das ein `group_by(["is_windy", "stop_name"]).agg(mean)` mit
> anschließendem Pivot — technisch unkompliziert, aber der resultierende DataFrame
> wird breit. Für die Visualisierung dann die Top-N-Stops nach Delta
> (windy - non-windy) sortiert.
>
> Zur Schwellenwahl 40 km/h: Das ist der aktuelle hardcodierte Wert aus dem
> Feature Engineering. Für einen Robustheitscheck wäre es gut zu sehen ob der
> Effekt bei 30 km/h bereits einsetzt oder erst bei 50 km/h. Das würde die
> Schwellenwahl validieren oder zur Anpassung führen. Eine Bin-Analyse über
> `wind_speed` analog zu TE5-Temperatur wäre der richtige Test dafür.

---

### W4 — Snow Impact
*(Ø arrival_delay: has_snow True vs False — precipitation > 0 & temperature < 2°C)*

> **[Thomas | 2026-05-14]**
> Schnee ist erwartungsgemäß der stärkste Wettereffekt — und gleichzeitig der
> seltenste. In Zürich schneit es im Durchschnitt ~20–30 Tage pro Jahr, davon
> nur wenige mit signifikantem Schneefall auf Meereshöhe.
>
> Das statistische Problem: `has_snow = True` hat deutlich weniger Beobachtungen
> als alle anderen Wetter-Flags. Ein großer Mittelwert-Unterschied bei wenigen
> Datenpunkten ist weniger zuverlässig. Empfehlung: Konfidenzintervalle mit
> ausgeben (95%-CI der Mittelwertdifferenz).
>
> Für das Modell: `has_snow` als Feature könnte wichtig sein trotz geringer
> Häufigkeit, weil Schneebedingungen für das Modell die extremsten Verspätungen
> erklären. Im Training-Set (2023–2024) müssen ausreichend Schneetage sein damit
> das Modell die Wechselwirkung lernt.

> **[Michael | 2026-05-14]**
> Thomas empfiehlt 95%-CI für Schnee-Mittelwerte — konkrete Implementierung:
> `scipy.stats.sem(snow_delays) * 1.96` für das 95%-CI bei normaler Näherung.
> Bei wenigen Schneetagen könnte Bootstrap-CI robuster sein:
> `np.percentile([np.mean(rng.choice(snow_delays, len(snow_delays))) for _ in range(1000)], [2.5, 97.5])`
>
> Wichtiger Punkt zur Modellierbarkeit von `has_snow`: Wenn das Training-Set
> (2023–2024) wenige Schneetage enthält, lernt XGBoost den Schnee-Effekt
> schlecht. Das kann durch `sample_weight` adressiert werden — Schnee-Zeilen
> erhalten höheres Gewicht beim Training. Alternativ: separate Schnee-Bedingung
> als Override-Logik außerhalb des Hauptmodells (regelbasiert: "wenn Schnee,
> addiere X Sekunden auf Prediction"). Das ist ein valider Produktions-Pattern
> für seltene, hohe Effekte.

---

### W5 — Temperature Correlation
*(Ø arrival_delay nach Temperatur-Bins à 5°C)*

> **[Thomas | 2026-05-14]**
> Die Temperatur-Bin-Analyse ist eleganter als eine simple Korrelation: Sie macht
> nichtlineare Zusammenhänge sichtbar. Erwartete Kurvenform: U-Shape oder
> Monoton-fallend (höhere Temp → weniger Verspätung, wegen Schnee/Eis im Kältebett).
>
> Eine U-Shape (hohe Verspätung bei Kälte UND Hitze) würde bedeuten:
> Sommerhitze über ~30°C verlangsamt auch den Tramverkehr — plausibel durch
> erhöhtes Passagiervolumen an Badetagen, langsamere Fahrgastbewegungen,
> technische Hitzeeffekte auf Gleise/Fahrzeuge.
>
> Mathematische Note: Bei 5°C-Bins haben die Winterbins (<−5°C) sehr wenige
> Beobachtungen — die Mittelwerte dort sind weniger stabil. Ein Modell sollte
> `temperature` als kontinuierliches Feature verwenden (nicht gebinnt), damit
> XGBoost die Splits selbst optimieren kann.

> **[Michael | 2026-05-14]**
> Thomas' Empfehlung `temperature` als kontinuierliches Feature zu verwenden ist
> korrekt. Technischer Hinweis zum Code: `temp_bin_5c` wird per Integer-Division
> `(pl.col("temperature") / 5).floor().cast(pl.Int8)` berechnet — das ist korrekt
> und effizient. Die zurückübersetzten Bin-Labels (Bin × 5 = °C-Untergrenze) fehlen
> noch im Plot, sollten aber als x-Ticks angezeigt werden.
>
> Zur U-Shape-Hypothese: Das lässt sich mit XGBoost's Feature Importance oder einem
> Partial Dependence Plot (PDP) nach dem Training elegant visualisieren.
> `from sklearn.inspection import PartialDependenceDisplay` — das zeigt den marginal
> effect von `temperature` auf den Delay ohne Confounding durch andere Features.
> Das wäre ein starkes Insights-Visualisierung für `04_insights.ipynb`.

---

## 03_analysis_events — Event Impact Analysis

> **Statushinweis [Thomas | 2026-05-14]:** Notebook in Skeleton-Phase.

> **[Michael | 2026-05-14]**
> Bestätigt. Alle vier Aggregationen (holidays, event_days, event_size, event_type)
> sind technisch korrekt und laufen direkt auf `lf`. Die Aggregationen sind schnell
> da sie nur `mean` und `len` berechnen — kein größeres Performance-Thema.
> Hauptarbeit liegt in den Visualisierungen und Observation-Zellen die noch fehlen.

---

### E1 — Holiday Impact
*(Ø arrival_delay: is_holiday True vs False)*

> **[Thomas | 2026-05-14]**
> Feiertage in Zürich sind eine natürliche Kontrollgruppe: Reduzierter
> Berufsverkehr, verändertes Fahrgastprofil, oft geänderte Taktfrequenzen.
> Hypothese: Pünktlichkeit steigt an Feiertagen (weniger Druck auf das Netz).
>
> Aber Achtung: Manche Feiertage (Weihnachten, Silvester, 1. August) sind
> gleichzeitig Veranstaltungstage. `is_holiday AND has_event` ist die interessantere
> Interaktion. Wenn Feiertage mit Events verknüpft sind, können sie trotzdem hohe
> Verspätungen zeigen — der Effekt des geringeren Berufsverkehrs wird durch
> Event-Nachfrage überkompensiert.

> **[Michael | 2026-05-14]**
> Thomas' Interaktions-Idee (`is_holiday AND has_event`) ist datenanalytisch korrekt
> und einfach zu berechnen:
> ```python
> lf.group_by(["is_holiday", "has_event"])
>    .agg(pl.col("arrival_delay").mean(), pl.len())
> ```
> Das gibt vier Gruppen (normal / holiday-only / event-only / holiday+event) und
> zeigt direkt ob es einen Interaktionseffekt gibt. Für das Modell: Ein
> Interaction-Feature `is_holiday_event = is_holiday & has_event` könnte relevant
> sein, wenn die Kombination mehr als additiv ist.

---

### E2 — Event Days vs Normal Days
*(Ø arrival_delay: has_event True vs False)*

> **[Thomas | 2026-05-14]**
> Das ist die zentrale Hypothese des Event-Abschnitts. Mit >1.000 Besuchern als
> Einschlussgrenze für Events sind vor allem Großveranstaltungen erfasst — genau
> die mit messbarem Effekt auf das Tramnetz.
>
> Die statistisch interessante Frage: Liegt der Effekt in der Zeit VOR oder
> NACH dem Event? Anreise-Peak (1–2h vor Beginn) vs. Abreise-Peak (direkt nach
> Ende). Der Datensatz hat kein Eventstart-Feature — `has_event` ist ein Tages-Flag.
> Das ist eine Vergröberung die echte zeitliche Muster verdeckt. Für eine
> verbesserte Version: stundenaufgelöste Event-Flags wären deutlich aussagekräftiger.

> **[Michael | 2026-05-14]**
> Thomas' Punkt zu Vor/Nach-Event-Effekten ist wichtig und aus dem vorhandenen
> Datensatz teilweise erschließbar: Wenn wir auf Event-Tagen nur die Abend-Stunden
> (18–23 Uhr) filtern und mit Nicht-Event-Tagen gleicher Uhrzeit vergleichen,
> sehen wir den Abreise-Effekt:
> ```python
> lf.filter(pl.col("has_event") & pl.col("hour").is_between(18, 23))
>    .select(pl.col("arrival_delay").mean())
> ```
> Das ist kein perfekter Test, aber ein praktikabler Proxy mit vorhandenen Features.
> Der Tages-Flag-Limitation ist eine Data-Engineering-Entscheidung aus Phase 0 —
> für v2 könnte man Event-Startzeiten aus dem Datensatz extrahieren falls vorhanden.

---

### E3 — Event Size Impact
*(Ø arrival_delay nach event_weight 0/1/2/3)*

> **[Thomas | 2026-05-14]**
> `event_weight` (1–3) kodiert die Veranstaltungsgröße und ist ein ordinales Feature.
> Die erwartete Beziehung ist monoton steigend: größerer Event → mehr Verspätung.
> Wenn die Beziehung nicht monoton ist (z.B. weight=2 höher als weight=3), deutet
> das auf eine fehlerhafte Gewichtungsskala hin oder auf confounding (weight=3
> Events finden primär in gut erreichbaren Lagen statt mit redundantem Tramnetz).
>
> Mathematisch ist `event_weight` als geordnete Kategorie zu behandeln, nicht
> als kontinuierliche Variable. Im Modell: entweder ordinales Encoding (0,1,2,3)
> wenn Monotonie bestätigt, oder One-Hot wenn nicht.

> **[Michael | 2026-05-14]**
> Einfacher Test für Monotonie nach Notebook-Ausführung: Wenn die vier Mittelwerte
> (weight 0–3) monoton steigen, ist Ordinal-Encoding korrekt. Wenn nicht, sollte
> man zusätzlich die Standardabweichungen betrachten — nicht-Monotonie kann durch
> hohe Varianz bei kleinen Gruppen entstehen statt durch echte Nicht-Monotonie.
>
> Technischer Hinweis: `event_weight = 0` (kein Event) und `weight = 1,2,3`
> (Events unterschiedlicher Größe) sind verschiedene Konzepte. Im Modell kann
> `event_weight` direkt als Integer-Feature verwendet werden (0–3) — XGBoost
> behandelt es effektiv als ordinales Feature und findet optimale Splits selbst.
> Das ist die empfohlene Strategie wenn die Monotonie-Annahme unklar ist.

---

### E4 — Event Type Breakdown
*(Ø arrival_delay nach Kategorie: Feiertag, Stadtfest, Konzert, Messe, Fussball)*

> **[Thomas | 2026-05-14]**
> Der Typ-Breakdown ist die inhaltlich reichste Event-Analyse. Hypothese für die
> Reihenfolge (von höchster zu niedrigster Verspätung): Fussball > Stadtfest >
> Konzert > Messe > Feiertag.
>
> Begründung: Fussball (Letzigrund) generiert extrem konzentrierte Verkehrsströme
> auf wenigen Linien im Westen der Stadt nach einem harten Schluss-Pfiff. Stadtfeste
> (Züri Fäscht) betreffen das gesamte Netz über mehrere Tage. Konzerte sind
> punktuell (Hallenstadion, Letzigrund). Messen (Zürich Messe) erzeugen Dauerbelastung
> über Tage. Feiertage dagegen reduzieren Berufsverkehr.
>
> Wenn diese Reihenfolge in den Daten nicht stimmt, lohnt es sich die
> Event-Kategorisierung zu überdenken — möglicherweise sind manche Kategorien
> mit zu wenigen Beobachtungen belegt um stabile Mittelwerte zu liefern.

> **[Michael | 2026-05-14]**
> Thomas' erwartete Reihenfolge ist plausibel. Technische Anmerkung: Die Aggregation
> `lf.filter(pl.col("has_event")).group_by("event_type")` filtert zuerst auf
> Event-Tage — das ist korrekt um `event_type = null` (kein Event) auszuschließen.
>
> Zur Stabilität der Mittelwerte: `count` ist in der Aggregation enthalten —
> das sollte direkt im Plot als Beschriftung sichtbar sein. Ein horizontales
> Barplot mit Balken sortiert nach `avg_delay` und `n=X` als Annotation auf jedem
> Balken macht die Vertrauenswürdigkeit sofort sichtbar. Kategorien mit n < 50
> Tagen sollte man vorsichtig interpretieren.
>
> Das Fussball-Hypothese lässt sich elegant prüfen: Fussballspiele Letzigrund +
> Linie 2/3/4 (Richtung Letzigrund) in der Stunde nach dem Schlusspfiff.
> Diese Detail-Analyse würde die Business-Story des Projekts stark machen.

---

## 03_analysis_spatial — Spatial Analysis

> **Statushinweis [Thomas | 2026-05-14]:** Notebook in Skeleton-Phase.

> **[Michael | 2026-05-14]**
> Bestätigt. Drei saubere Aggregationen (top_stops, districts, lines) auf `lf`.
> Die Spatial-Plots werden vermutlich die visuell eindrucksvollsten des Projekts —
> besonders S2 als Choropleth-Karte. Hauptaufwand liegt in der Folium-Integration
> und der GTFS-Geometrie für die Kreise.

---

### S1 — Top Delay Stops
*(Top-20 Haltestellen nach Ø arrival_delay)*

> **[Thomas | 2026-05-14]**
> Die Top-Delay-Haltestellen sind die operationellen "Hotspots" des Projekts —
> Orte wo sich Fahrplanabweichungen konzentrieren. Sie sind der konkreteste
> Deliverable für die Betreiberperspektive (VBZ).
>
> Erwartung: Haltestellen an topografischen Engpässen (Steigungen, enge Kurven),
> an verkehrsreichen Kreuzungen (Stauffacher, Bürkliplatz, Bellevue) oder an
> Endpunkten wo mehrere Linien zusammentreffen. Bellevue und Bürkliplatz sind
> klassische Zürich-Engstellen.
>
> Methodische Note: `avg_delay` allein ist kein gutes Bottleneck-Maß. Eine
> Haltestelle mit hoher mittlerer Verspätung aber wenigen Fahrten unterscheidet
> sich fundamental von einer Haltestelle mit mäßiger mittlerer Verspätung aber
> sehr hohem Fahrgastaufkommen. Ein "Delay Impact Score" = `avg_delay × trip_count`
> wäre aussagekräftiger für die Business-Perspektive.

> **[Michael | 2026-05-14]**
> Thomas' Delay Impact Score Idee ist analytisch stark — und in Polars trivial:
> ```python
> top_stops.with_columns(
>     (pl.col("avg_delay") * pl.col("trip_count")).alias("impact_score")
> ).sort("impact_score", descending=True)
> ```
> Das gibt eine andere Rangliste als reines `avg_delay` — eine Haltestelle mit
> moderater Verspätung aber 200.000 Trips/Jahr hat mehr Gesamtauswirkung als
> eine mit hoher Verspätung aber 1.000 Trips/Jahr.
>
> Für die Folium-Karte: Die GTFS-Stops-Tabelle enthält `stop_lat` / `stop_lon`
> direkt — kein zusätzlicher Geocoding-Schritt nötig. Merge auf `bpuic`:
> `top_stops.join(stops_gtfs, on="bpuic")`. Dann Folium CircleMarkers mit Radius
> proportional zum `impact_score`. Das ist der visuell stärkste Deliverable dieses
> Notebooks und direkt umsetzbar.

---

### S2 — District Analysis
*(Ø arrival_delay nach Stadtkreis 1–12 + außerhalb)*

> **[Thomas | 2026-05-14]**
> Die Stadtkreis-Analyse ist die politisch relevanteste Dimension: Jeder Kreis
> hat eine eigene Interessenvertretung und Bevölkerungscharakteristik.
>
> Erwartete Muster: Kreis 1 (Altstadt/Innenstadt) mit hoher Verspätung durch
> Fussgängerzonen und Tourismus. Kreis 3/4 (Wiedikon/Aussersihl) mit
> Arbeiterbevölkerung und starkem Pendelverkehr. Die äußeren Kreise (7–12)
> eher pünktlicher da weniger Stadtverkehr-Interferenz.
>
> Die Kategorie "außerhalb" (kein Stadtkreis 1–12) ist methodisch zu klären:
> Sind das Haltestellen in den Agglomerationsgemeinden? Wenn ja, könnte das
> Verhalten dort anders sein (weniger Stop-and-Go, mehr Streckenfahrt).
>
> Diese Daten eignen sich direkt für eine Folium-Choropleth-Karte der Stadtkreise —
> der stärkste visuelle Deliverable des gesamten Projekts.

> **[Michael | 2026-05-14]**
> Für die Choropleth-Karte brauchen wir GeoJSON der Zürcher Stadtkreise. Diese
> sind öffentlich verfügbar über die Stadt Zürich Open Data Plattform
> (data.stadt-zuerich.ch) als Shapefile oder GeoJSON. Mit GeoPandas:
> ```python
> import geopandas as gpd
> kreise = gpd.read_file("stadtkreise.geojson")
> kreise_delay = kreise.merge(districts.to_pandas(), left_on="KNr", right_on="district_nr")
> ```
> Dann `folium.Choropleth()` mit `data=kreise_delay` und `columns=["KNr","avg_delay"]`.
>
> Zur "außerhalb"-Kategorie: In der Master-Daten-Dokumentation sollte stehen wie
> `district_nr = 0` oder `null` belegt wurde. Falls das Agglomeration-Stops sind,
> ist ein separates Highlighting sinnvoll — sie haben möglicherweise eine
> andere Delay-Charakteristik (Endstationen, weniger Kreuzungsverkehr). Das ist
> eine schnelle Plausibilitätsprüfung: `lf.filter(pl.col("district_nr").is_null()).select("stop_name").unique()` zeigt welche Haltestellen betroffen sind.

---

### S3 — Line Analysis
*(Ø arrival_delay und Median nach Linie)*

> **[Thomas | 2026-05-14]**
> Die Linien-Analyse schließt den Kreis zur Ausfallquote aus T8. Linien mit
> hoher Ausfallquote sollten auch höhere mittlere Verspätung zeigen — wenn nicht,
> deutet das auf unterschiedliche Störungsmuster hin (eine Linie wird häufig
> ganz abgesagt statt verspätet, eine andere fährt immer aber mit Verspätung).
>
> Mathematisch wertvoll: Das gleichzeitige Zeigen von Mittelwert AND Median je
> Linie quantifiziert die Ausreißer-Sensitivität. Eine Linie mit
> Median ≈ 30s aber Mittelwert ≈ 80s hat eine starke Rechts-Tail-Struktur —
> wenige sehr große Ereignisse dominieren die Statistik. Eine Linie mit
> Median ≈ 50s und Mittelwert ≈ 60s ist gleichmäßig zuverlässig langsam.
>
> Für das Modell ist `line_name` ein strukturelles Feature: Es kodiert implizit
> Trassierung, Fahrzeugtyp, Netzposition und Taktfrequenz. Empfehle
> Target-Encoding mit leave-one-out Strategie um Leakage zu vermeiden.

> **[Michael | 2026-05-14]**
> Thomas' Mittelwert vs. Median Vergleich je Linie ist eine elegante Visualisierung.
> Konkrete Implementierung: Grouped Barplot mit zwei Balken pro Linie (Mean + Median)
> oder ein Scatter-Plot Mean vs. Median mit Liniennamen als Labels — letzteres macht
> die Ausreißer-Sensitivität direkt sichtbar: Linien nah an der Diagonale haben
> symmetische Verteilungen, Linien weit oberhalb der Diagonale haben heavy tails.
>
> Zur Target-Encoding-Leakage-Frage: Thomas hat recht. Die sklearn `TargetEncoder`
> Klasse (v1.3+) implementiert cv-basiertes Encoding das Leakage verhindert.
> Alternativ: In Polars die Encoding-Map manuell aus Train berechnen und auf Test
> applizieren:
> ```python
> encoding_map = df_train.group_by("line_name").agg(pl.col("arrival_delay").mean().alias("line_target_enc"))
> df_test = df_test.join(encoding_map, on="line_name", how="left")
> ```
> Das ist transparenter als eine Blackbox-Klasse und zeigt klar was encodiert wird.

---

## Offene Querschnittsfragen

> **[Thomas | 2026-05-14]**
> Über alle Analysis-Notebooks hinweg ergeben sich folgende Fragen die aktuell
> nicht durch einen einzelnen Plot beantwortet werden:
>
> 1. **Wechselwirkungen:** Wie interagieren Wetter + Zeit + Events? Ist ein
>    verregneter Freitagabend mit Fussballspiel mehr als die Summe der Einzeleffekte?
>    Dafür bräuchte es Interaktionsfeatures im Modell oder einen separaten
>    Interaktions-Plot.
>
> 2. **Cascade-Effekte:** Ohne `trip_id` ist unklar ob eine verspätete Tram die
>    nächste Fahrt ebenfalls verspätet. Lag-Features (`delay_previous_stop`) wären
>    das stärkste Feature im Modell — aber sie erfordern Trip-Level-Gruppierung.
>    Das BACKLOG-Item #8 (Segment-Fahrzeit-Analyse) adressiert genau das.
>
> 3. **Stationarität:** Sind die Muster über 3 Jahre stabil? Oder hat sich das
>    Netz strukturell verändert (Linienänderungen, neue Haltestellen)? Die GTFS
>    Referenz-Jahres-Entscheidung (2024) als Basis für alle drei Jahre sollte
>    explizit im Modell-Dokumentation stehen.
>
> 4. **Modell-Fairness:** Sagt das Modell für alle Linien/Stadtkreise gleich gut
>    vorher? Oder wird es für Randgebiete (weniger Trainingsdaten) deutlich
>    schlechter? Das ist ein Fairness-/Equity-Aspekt der für die Business-Cases
>    relevant ist.

> **[Michael | 2026-05-14]**
> Thomas' vier Querschnittsfragen sind gut identifiziert. Ich ergänze technische
> Lösungsansätze:
>
> **Zu 1 — Wechselwirkungen:** Interaktionsfeatures in Polars:
> `pl.when(pl.col("has_rain") & pl.col("is_rush_hour")).then(1).otherwise(0).alias("rain_rush")`
> Alternativ: XGBoost's SHAP Interaction Values nach dem Training — das zeigt
> automatisch welche Feature-Paare sich gegenseitig verstärken.
>
> **Zu 2 — Cascade-Effekte:** `trip_id` + `stop_sequence` sind im GTFS vorhanden.
> Die Lag-Feature-Implementierung (siehe T4-Kommentar) ist der konkrete nächste
> Schritt für BACKLOG-Item #8. Priority: H, weil es das stärkste einzelne Feature
> im Modell werden wird.
>
> **Zu 3 — Stationarität:** Ein einfacher Test: Für jedes Jahr separat die Top-5
> Delay-Stationen berechnen. Wenn die Liste stabil ist, sind die Muster stationär.
> Wenn nicht, hat sich das Netz strukturell verändert. Eine Zeile Polars pro Jahr.
>
> **Zu 4 — Modell-Fairness:** Nach dem Modell-Training: RMSE je Linie und je
> Stadtkreis aufschlüsseln. Wenn Kreis 11/12 (wenig Daten) deutlich schlechtere
> Metriken hat als Kreis 1/2, ist das ein Fairness-Problem. Das gehört in
> `04_insights.ipynb` als eigener Abschnitt.
