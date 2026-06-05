# Einführung in die Orchestrierung von KI-Modellen

Eine Einführung in die Konzepte und Werkzeuge für Erstellung von Multi-Agenten-Systemen im Software Engineering verwendet werden.

## 1. Was ist Orchestrierung von KI-Modellen?

Orchestrierung bezeichnet die Koordination und Steuerung mehrerer KI-Modelle oder spezialisierter Agenten, damit diese gemeinsam ein komplexes Ziel erreichen. 

Man kann es sich wie ein Orchester vorstellen: Das LLM ist ein talentierter Musiker, aber ohne einen **Dirigenten (die Orchestrierung)** spielen alle Musiker unabhängig voneinander. Die Orchestrierung sorgt dafür, dass:
1.  Die richtige Aufgabe zur richtigen Zeit an den richtigen Agenten geht.
2.  Informationen korrekt zwischen den Agenten fließen.
3.  Fehler erkannt und Korrekturschleifen eingeleitet werden.

## 2. Warum ist Orchestrierung sinnvoll? (Vorteile)

Der Übergang von einem Single-Agent zu einem orchestrierten Multi-Agenten-System bietet mehrere Vorteile:

*   **Spezialisierung (Modularität):** Anstatt einem LLM zu sagen "Schreibe die ganze App", bekommt ein Agent eine sehr spezifische Rolle (z. B. "Du bist ein Security Experte"). Das reduziert Halluzinationen und erhöht die Qualität.
*   **Fehlerkorrektur:** Ein dedizierter Review-Agent kann Fehler finden, die der ursprüngliche Developer-Agent übersehen hat. In einem Multi-Agenten-System ist Selbstreflexion systemisch eingebaut.
*   **Skalierbarkeit:** Komplexe Aufgaben können in kleinere, handhabbare Teilaufgaben zerlegt werden.
*   **Transparenz:** Man kann genau nachvollziehen, welcher Agent welche Entscheidung getroffen hat, was das Debugging von KI-Workflows erleichtert.

## 3. Was ist LangChain?

**LangChain** ist ein Open-Source-Framework, das entwickelt wurde, um die Erstellung von Anwendungen zu erleichtern, die auf Large Language Models (LLMs) basieren. Da LLMs alleine oft "gedächtnislos" sind und keinen direkten Zugriff auf externe Datenquellen oder Werkzeuge haben, schließt LangChain diese Lücke.

**Kernkomponenten von LangChain:**
*   **Chains:** Ermöglichen das "Verketten" mehrerer Schritte. Das Ergebnis eines LLM-Aufrufs kann als Input für den nächsten dienen.
*   **Prompt Templates:** Standardisierte Vorlagen für Prompts, um konsistente Ergebnisse zu erzielen.
*   **Retrieval-Augmented-Generation (RAG):** Anbindung an Datenbanken oder Dokumente, um dem Modell spezifisches Wissen zur Verfügung zu stellen.
*   **Agents:** Ein Agent entscheidet mithilfe eines LLMs, welche Aktionen (z. B. Websuche, Datenbankabfrage) in welcher Reihenfolge ausgeführt werden sollen.

## 4. Was ist LangGraph?

**LangGraph** ist eine Erweiterung von LangChain, die speziell für die Erstellung von zustandsbehafteten (stateful) und zyklischen Multi-Agenten-Systemen entwickelt wurde.

Während klassische LangChain-"Chains" oft linear (wie eine Kette) verlaufen, erlaubt LangGraph die Definition von Graphen:
*   **Nodes (Knoten):** Repräsentieren Funktionen oder Agenten (z. B. der "Developer Agent").
*   **Edges (Kanten):** Definieren den Fluss zwischen den Knoten.
*   **State:** Ein zentrales Objekt, das den aktuellen Zustand des Projekts speichert und zwischen den Agenten weitergereicht wird.

LangGraph ist ideal für komplexe Workflows, bei denen Agenten miteinander interagieren, Feedback geben und Schritte wiederholen müssen (z. B. wenn der Reviewer den Code zur Korrektur an den Developer zurückschickt).
