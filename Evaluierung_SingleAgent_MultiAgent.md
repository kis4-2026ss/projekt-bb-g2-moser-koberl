# Einführung in die Orchestrierung von KI-Modellen

Dieses Dokument dient als Einführung in die Konzepte und Werkzeuge, die für die Evaluierung von Single-Agent- vs. Multi-Agenten-Systemen im Software Engineering verwendet werden.

---

## I. Konzeptuelle Einführung

### 1.1 Was ist Orchestrierung von KI-Modellen?
Orchestrierung bezeichnet die Koordination und Steuerung mehrerer KI-Modelle oder spezialisierter Agenten, damit diese gemeinsam ein komplexes Ziel erreichen. 

Man kann es sich wie ein Orchester vorstellen: Das LLM ist ein talentierter Musiker, aber ohne einen **Dirigenten (die Orchestrierung)** spielen alle Musiker unabhängig voneinander. Die Orchestrierung sorgt dafür, dass:
1.  Die richtige Aufgabe zur richtigen Zeit an den richtigen Agenten geht.
2.  Informationen korrekt zwischen den Agenten fließen.
3.  Fehler erkannt und Korrekturschleifen eingeleitet werden.

### 1.2 Warum ist Orchestrierung sinnvoll? (Vorteile)
Der Übergang von einem Single-Agent zu einem orchestrierten Multi-Agenten-System bietet mehrere Vorteile:
*   **Spezialisierung (Modularität):** Anstatt einem LLM zu sagen "Schreibe die ganze App", bekommt ein Agent eine sehr spezifische Rolle (z. B. "Du bist ein Security Experte"). Das reduziert Halluzinationen und erhöht die Qualität.
*   **Fehlerkorrektur:** Ein dedizierter Review-Agent kann Fehler finden, die der ursprüngliche Developer-Agent übersehen hat. In einem Multi-Agenten-System ist Selbstreflexion systemisch eingebaut.
*   **Skalierbarkeit:** Komplexe Aufgaben können in kleinere, handhabbare Teilaufgaben zerlegt werden.
*   **Transparenz:** Man kann genau nachvollziehen, welcher Agent welche Entscheidung getroffen hat, was das Debugging von KI-Workflows erleichtert.

---

## II. Technologische Basis (Werkzeuge)

### 2.1 Was ist LangChain?
**LangChain** ist ein Open-Source-Framework, das entwickelt wurde, um die Erstellung von Anwendungen zu erleichtern, die auf Large Language Models (LLMs) basieren. Da LLMs alleine oft "gedächtnislos" sind und keinen direkten Zugriff auf externe Datenquellen oder Werkzeuge haben, schließt LangChain diese Lücke.

**Kernkomponenten von LangChain:**
*   **Chains:** Ermöglichen das "Verketten" mehrerer Schritte. Das Ergebnis eines LLM-Aufrufs kann als Input für den nächsten dienen.
*   **Prompt Templates:** Standardisierte Vorlagen für Prompts, um konsistente Ergebnisse zu erzielen.
*   **Retrieval-Augmented-Generation (RAG):** Anbindung an Datenbanken oder Dokumente, um dem Modell spezifisches Wissen zur Verfügung zu stellen.
*   **Agents:** Ein Agent entscheidet mithilfe eines LLMs, welche Aktionen (z. B. Websuche, Datenbankabfrage) in welcher Reihenfolge ausgeführt werden sollen.

### 2.2 Was ist LangGraph?
**LangGraph** ist eine Erweiterung von LangChain, die speziell für die Erstellung von zustandsbehafteten (stateful) und zyklischen Multi-Agenten-Systemen entwickelt wurde.

Während klassische LangChain-"Chains" oft linear (wie eine Kette) verlaufen, erlaubt LangGraph die Definition von Graphen:
*   **Nodes (Knoten):** Repräsentieren Funktionen oder Agenten (z. B. der "Developer Agent").
*   **Edges (Kanten):** Definieren den Fluss zwischen den Knoten.
*   **State:** Ein zentrales Objekt, das den aktuellen Zustand des Projekts speichert und zwischen den Agenten weitergereicht wird.

LangGraph ist ideal für komplexe Workflows, bei denen Agenten miteinander interagieren, Feedback geben und Schritte wiederholen müssen.

---

## III. Agentisches Design & Methodik

### 3.1 Agentic Design Patterns (Agentische Entwurfsmuster)
Für die effiziente Zusammenarbeit von Agenten haben sich spezifische Entwurfsmuster etabliert:
*   **Reflection:** Ein Agent überprüft seine eigene Arbeit oder erhält Feedback von einem anderen Agenten, um Ergebnisse iterativ zu verbessern.
*   **Tool Use:** Die Fähigkeit eines LLMs zu bestimmen, wann und wie externe Werkzeuge (z. B. Compiler, Suchmaschinen, Datenbanken) eingesetzt werden müssen.
*   **Planning:** Der Prozess, bei dem ein Agent ein komplexes Ziel in eine logische Abfolge von Teilschritten zerlegt, bevor er mit der Ausführung beginnt.
*   **Multi-Agent Collaboration:** Die Aufteilung einer Aufgabe auf verschiedene spezialisierte Agenten, die unterschiedliche Rollen einnehmen und Informationen austauschen.

### 3.2 Prompt Engineering Strategien
Da die Qualität der KI-Ergebnisse stark von der Eingabe abhängt, kommen folgende Strategien zum Einsatz:
*   **Persona-based Prompting:** Zuweisung einer spezifischen Expertenrolle (z. B. "Du bist ein Senior Software Architekt"), um den Fokus und den Stil des Modells zu steuern.
*   **Chain-of-Thought (CoT):** Die Anweisung an das Modell, seine Gedankengänge explizit darzulegen, was besonders bei komplexer Programmierlogik die Fehlerquote senkt.
*   **Few-Shot Prompting:** Bereitstellung von Beispielen im Prompt, damit das Modell das gewünschte Ausgabeformat oder den Lösungsweg besser versteht.

---

## IV. Systemdesign & Evaluierung

### 4.1 State Management (Zustandsverwaltung)
In einem Multi-Agenten-System ist es entscheidend, wie Informationen über die Zeit gespeichert werden:
*   **Zentraler State:** In LangGraph wird ein gemeinsames Objekt (State) genutzt, das alle relevanten Projektdaten (Anforderungen, Code, Testergebnisse) enthält.
*   **Context Window Management:** Da LLMs ein begrenztes "Gedächtnis" (Token-Limit) haben, muss die Orchestrierung entscheiden, welche Informationen für den aktuellen Schritt am wichtigsten sind.

### 4.2 Evaluierungsmethodik
Um den Vergleich zwischen Single-Agent und Multi-Agent objektiv zu gestalten, werden folgende Ansätze genutzt:
*   **Deterministische Tests:** Klassische Unit-Tests prüfen die funktionale Korrektheit des generierten Codes.
*   **LLM-as-a-Judge:** Ein leistungsfähiges Modell (z. B. GPT-4o) bewertet die Codequalität, Lesbarkeit und Architektur nach vordefinierten Kriterien.
*   **Effizienz-Metriken:** Messung der Anzahl der benötigten Iterationen und Token-Kosten bis zur erfolgreichen Lösung.

---

## V. Projektspezifische Umsetzung

### 5.1 Gewählter Technologie-Stack
Für die zu entwickelnde E-Commerce Applikation wurde ein moderner und modularer Stack gewählt, der die Fähigkeiten der KI-Agenten optimal herausfordert und vergleichbar macht:

*   **Backend: Python mit FastAPI**
    *   *Begründung:* FastAPI bietet eine hohe Performance und nutzt Python-Typhinweise, was die KI dazu zwingt, sauberen und validierbaren Code zu schreiben. Zudem werden API-Dokumentationen (Swagger) automatisch generiert, was die Überprüfung der Endpunkte durch Reviewer-Agenten erleichtert.
*   **Datenbank: SQLite mit SQLAlchemy**
    *   *Begründung:* SQLite benötigt keine externe Server-Infrastruktur, was die Portabilität des Projekts erhöht. SQLAlchemy als ORM (Object-Relational Mapper) testet die Fähigkeit der KI, komplexe Datenstrukturen und Datenbankbeziehungen korrekt abzubilden.
*   **Frontend: Web Components (Vanilla JS) mit Tailwind CSS**
    *   *Begründung:* Web Components erlauben eine modulare Frontend-Entwicklung ohne die Abhängigkeit von schweren Frameworks wie React oder Vue. Dies ist ideal, um zu evaluieren, ob ein Agent in der Lage ist, Code in wiederverwendbare Komponenten zu kapseln. Tailwind CSS ermöglicht ein modernes Design durch Utility-Classes direkt im HTML/JS-Code.

### 5.2 Aufbau der Applikation
Um den gesamten Entwicklungsprozess abzubilden, umfasst die Applikation drei Kernbereiche:
1.  **Produktübersicht:** Anzeige aller verfügbaren Produkte (Testfall für Datenabfrage und Listen-Rendering).
2.  **Produktdetailseite:** Detaillierte Ansicht eines einzelnen Produkts (Testfall für dynamisches Routing und Parameter-Handling).
3.  **Warenkorb:** Verwaltung der ausgewählten Produkte (Testfall für State Management und komplexere Logik zwischen Frontend und Backend).

---
