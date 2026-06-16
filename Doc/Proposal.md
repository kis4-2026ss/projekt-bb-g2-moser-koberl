# Evaluation von Multi-Agent AI-Systemen im Software Engineering mit rollenspezifischer Aufgabenverteilung

## Übergeordnetes Ziel
Ziel dieses Projekts ist es, zu untersuchen, wie man ein Multi-Agenten-KI-System aufsetzt und ob ein Multi-Agenten-KI-System mit rollenspezifischer Aufgabenverteilung bessere Ergebnisse im Software Engineering liefert als ein einzelner KI-Agent.

Dabei wird AI-unterstütztes Software Engineering genutzt, indem ein klassischer Entwicklungsprozess durch mehrere spezialisierte KI-Agenten simuliert wird, die typische Rollen eines Software-Teams übernehmen.

---

## Validierung / Evaluation
Der Vergleich erfolgt zwischen zwei Ansätzen:

### 1. Single-Agent-System
Ein einzelnes LLM übernimmt den gesamten Entwicklungsprozess:
* Anforderungen verstehen
* Architektur entwerfen
* Code generieren
* Tests erstellen
* Selbstreview durchführen

### 2. Multi-Agenten-System
Mehrere spezialisierte KI-Agenten arbeiten in einer Pipeline zusammen:
* **Product Owner Agent** → erstellt Anforderungen
* **Architect Agent** → entwirft Systemarchitektur
* **Developer Agent** → implementiert Code
* **Tester Agent** → erstellt Tests
* **Reviewer Agent** → führt Code-Review durch und gibt Feedback

---

## Bewertungskriterien
Die Ergebnisse beider Systeme werden anhand folgender Metriken verglichen:
* Codequalität
* Produktqualität
* Funktionale Korrektheit (bestehende Unit Tests)
* Testabdeckung
* Lesbarkeit und Wartbarkeit
* Effizienz (Anzahl Iterationen bis zur Lösung)
* Kosten

---

## Beitrag von KI im Projekt
KI wird als zentrale Komponente eingesetzt:
* Nutzung von Large Language Models (z. B. GPT)
* Rollenbasierte Prompt-Engineering-Strategien
* Simulation eines Software-Entwicklungsteams durch AI-Agenten
* Automatisierte Code-, Test- und Review-Generierung
* Orchestrierung verschiedener KI-Agenten mittels LangChain

---

## Zu entwickelndes System
Es wird eine einfache E-Commerce Applikation entwickelt, welche vollumfänglich von LLMs erstellt wird. Die Applikation soll einen simplen Webshop darstellen, welcher folgende Funktionen umfassen soll:
* Produktübersicht
* Warenkorb
* Produktdetails

--

## Development/Architecture Diagramm
![Development and Architecture Diagram](KIS-Projekt.drawio.png)


---

## Project Plan
* **Phase 1:** Vorbereitung & Start-Test (Single-Agent)
* **Phase 2:** Das KI-Team aufbauen (Multi-Agent)
* **Phase 3:** Projektumsetzung durch Single-Agent und Multi-Agent
* **Phase 4:** Vergleich durchführen & Abschlussbericht erstellen