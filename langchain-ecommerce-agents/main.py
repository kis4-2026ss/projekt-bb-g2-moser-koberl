import os
import json
import re
from pathlib import Path
from typing import TypedDict, List, Dict, Any

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END


load_dotenv()


# ------------------------------------------------------------
# Konfiguration
# ------------------------------------------------------------

OUTPUT_DIR = Path(
    r"C:\Users\sebas\Nextcloud\PC\Studium\KIS4\Projekt\Project-Output"
)

MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


# ------------------------------------------------------------
# State Definition
# ------------------------------------------------------------

class WebsiteState(TypedDict):
    user_request: str
    product_owner_output: str
    architect_output: str
    developer_output: str
    tester_output: str
    reviewer_output: str
    final_output: str


model = ChatOpenAI(
    model=MODEL_NAME,
    temperature=0.2,
)


# ------------------------------------------------------------
# Hilfsfunktionen
# ------------------------------------------------------------

def extract_json(text: str) -> Dict[str, Any]:
    """
    Extrahiert JSON aus einer Modellantwort.
    Funktioniert auch, wenn das Modell ```json ... ``` verwendet.
    """
    text = text.strip()

    # Markdown-Codeblock entfernen
    code_block_match = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if code_block_match:
        text = code_block_match.group(1).strip()

    return json.loads(text)


def save_files_from_json(files_json_text: str, base_dir: Path) -> List[Path]:
    """
    Erwartet JSON im Format:
    {
      "files": [
        {
          "path": "package.json",
          "content": "..."
        }
      ]
    }
    """
    data = extract_json(files_json_text)

    saved_files = []

    for file in data.get("files", []):
        relative_path = file["path"]
        content = file["content"]

        target_path = base_dir / relative_path
        target_path.parent.mkdir(parents=True, exist_ok=True)

        with open(target_path, "w", encoding="utf-8") as f:
            f.write(content)

        saved_files.append(target_path)

    return saved_files


def save_markdown(filename: str, content: str, base_dir: Path) -> Path:
    target_path = base_dir / filename
    target_path.parent.mkdir(parents=True, exist_ok=True)

    with open(target_path, "w", encoding="utf-8") as f:
        f.write(content)

    return target_path


# ------------------------------------------------------------
# Agenten
# ------------------------------------------------------------

def product_owner_agent(state: WebsiteState) -> WebsiteState:
    prompt = f"""
Du bist Product Owner.

Ziel:
Erstelle klare Anforderungen für eine einfache E-Commerce-Plattform.

User Request:
{state["user_request"]}

Technologie:
Angular

Liefere:
1. Projektziel
2. Zielgruppe
3. Seitenstruktur
4. Kernfunktionen
5. User Stories
6. Akzeptanzkriterien
7. Minimale Produktdaten
8. Nicht-Ziele / Out of Scope
9. Priorisierte MVP-Anforderungen

Halte alles realistisch, simpel und für ein kleines Angular-Projekt umsetzbar.
"""

    response = model.invoke([
        ("system", "Du bist ein erfahrener Product Owner für Web- und E-Commerce-Projekte."),
        ("human", prompt),
    ])

    state["product_owner_output"] = response.content
    return state


def architect_agent(state: WebsiteState) -> WebsiteState:
    prompt = f"""
Du bist Software Architect.

Basierend auf diesen Anforderungen:

{state["product_owner_output"]}

Entwirf eine einfache Angular-Systemarchitektur.

Liefere:
1. Architekturübersicht
2. Angular-Komponentenstruktur
3. Services
4. Datenmodell
5. State-Management-Ansatz
6. Routing-Konzept
7. Teststrategie
8. Dateistruktur
9. Technische Annahmen

Wichtig:
- Kein Backend
- Kein echtes Payment
- Daten dürfen lokal im Frontend simuliert werden
- Die Architektur soll für ein Anfänger-/Studienprojekt verständlich sein
"""

    response = model.invoke([
        ("system", "Du bist ein Software Architect mit Fokus auf Angular-Anwendungen."),
        ("human", prompt),
    ])

    state["architect_output"] = response.content
    return state


def developer_agent(state: WebsiteState) -> WebsiteState:
    prompt = f"""
Du bist Angular Developer.

Erstelle basierend auf Product-Owner-Anforderungen und Architektur ein simples Angular-Projekt.

Product Owner Anforderungen:
{state["product_owner_output"]}

Architektur:
{state["architect_output"]}

Aufgabe:
Implementiere eine einfache Angular E-Commerce-App.

Anforderungen:
- Angular App
- Simple Produktliste
- Warenkorb
- Produkt zum Warenkorb hinzufügen
- Produkt aus Warenkorb entfernen
- Gesamtsumme anzeigen
- Kein Backend
- Keine echte Zahlung
- Lokale Mock-Daten
- Saubere einfache Struktur
- Modernes CSS
- Standalone Components bevorzugt
- Der Code soll als Projektdateien gespeichert werden können

Gib ausschließlich valides JSON zurück.

Format:
{{
  "files": [
    {{
      "path": "package.json",
      "content": "..."
    }},
    {{
      "path": "src/main.ts",
      "content": "..."
    }}
  ]
}}

Wichtig:
- Keine Markdown-Codeblöcke
- Keine Erklärung außerhalb des JSON
- Alle notwendigen Dateien für ein minimales Angular-Projekt angeben
- Verwende einfache, robuste Implementierung
"""

    response = model.invoke([
        ("system", "Du bist ein Angular Frontend Developer. Du gibst ausschließlich valides JSON mit Projektdateien zurück."),
        ("human", prompt),
    ])

    state["developer_output"] = response.content
    return state


def tester_agent(state: WebsiteState) -> WebsiteState:
    prompt = f"""
Du bist Tester / QA Engineer.

Erstelle Tests für diese Angular-App.

Product Owner Anforderungen:
{state["product_owner_output"]}

Architektur:
{state["architect_output"]}

Implementierter Code als JSON:
{state["developer_output"]}

Aufgabe:
Erstelle passende Testdateien für Angular.

Tests sollen prüfen:
1. App wird erstellt
2. Produkte werden angezeigt
3. Produkte können dem Warenkorb hinzugefügt werden
4. Produkte können entfernt werden
5. Gesamtsumme wird korrekt berechnet

Gib ausschließlich valides JSON zurück.

Format:
{{
  "files": [
    {{
      "path": "src/app/app.spec.ts",
      "content": "..."
    }}
  ]
}}

Wichtig:
- Keine Markdown-Codeblöcke
- Keine Erklärung außerhalb des JSON
- Tests sollen zum generierten Code passen
"""

    response = model.invoke([
        ("system", "Du bist ein Angular QA Engineer. Du erstellst ausschließlich valide JSON-Dateien mit Tests."),
        ("human", prompt),
    ])

    state["tester_output"] = response.content
    return state


def reviewer_agent(state: WebsiteState) -> WebsiteState:
    prompt = f"""
Du bist Code Reviewer.

Prüfe die Angular-Implementierung und die Tests.

Product Owner Anforderungen:
{state["product_owner_output"]}

Architektur:
{state["architect_output"]}

Developer Output:
{state["developer_output"]}

Tester Output:
{state["tester_output"]}

Liefere:
1. Kurzfazit
2. Erfüllung der Anforderungen
3. Architektur-Review
4. Codequalität
5. Testabdeckung
6. Risiken
7. Verbesserungsvorschläge
8. Go/No-Go Entscheidung

Sei kritisch, aber konstruktiv.
"""

    response = model.invoke([
        ("system", "Du bist ein erfahrener Senior Code Reviewer für Angular-Projekte."),
        ("human", prompt),
    ])

    state["reviewer_output"] = response.content
    return state


def final_agent(state: WebsiteState) -> WebsiteState:
    state["final_output"] = f"""
# Agenten-Ergebnis

## 1. Product Owner Agent

{state["product_owner_output"]}

---

## 2. Architect Agent

{state["architect_output"]}

---

## 3. Developer Agent

Der Developer Agent hat Angular-Projektdateien als JSON erzeugt.

---

## 4. Tester Agent

Der Tester Agent hat Angular-Testdateien als JSON erzeugt.

---

## 5. Reviewer Agent

{state["reviewer_output"]}
"""
    return state


# ------------------------------------------------------------
# Graph bauen
# ------------------------------------------------------------

graph_builder = StateGraph(WebsiteState)

graph_builder.add_node("product_owner", product_owner_agent)
graph_builder.add_node("architect", architect_agent)
graph_builder.add_node("developer", developer_agent)
graph_builder.add_node("tester", tester_agent)
graph_builder.add_node("reviewer", reviewer_agent)
graph_builder.add_node("final", final_agent)

graph_builder.add_edge(START, "product_owner")
graph_builder.add_edge("product_owner", "architect")
graph_builder.add_edge("architect", "developer")
graph_builder.add_edge("developer", "tester")
graph_builder.add_edge("tester", "reviewer")
graph_builder.add_edge("reviewer", "final")
graph_builder.add_edge("final", END)

agent_team = graph_builder.compile()


# ------------------------------------------------------------
# Ausführung
# ------------------------------------------------------------

if __name__ == "__main__":
    request = """
Erstelle eine simple E-Commerce-Plattform als Angular-Webseite.

Thema:
Sneaker-Shop

Die Webseite soll:
- Produkte anzeigen
- Produktname, Preis und Beschreibung zeigen
- Produkte in einen Warenkorb legen können
- Produkte aus dem Warenkorb entfernen können
- die Gesamtsumme anzeigen
- modern, übersichtlich und simpel aussehen
"""

    initial_state: WebsiteState = {
        "user_request": request,
        "product_owner_output": "",
        "architect_output": "",
        "developer_output": "",
        "tester_output": "",
        "reviewer_output": "",
        "final_output": "",
    }

    print("Starte Agenten-Team...")
    print("Product Owner → Architect → Developer → Tester → Reviewer")

    result = agent_team.invoke(initial_state)

    print("Erstelle Output-Ordner...")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Speicherort: {OUTPUT_DIR}")

    # Dokumentation speichern
    save_markdown("01_product_owner_requirements.md", result["product_owner_output"], OUTPUT_DIR)
    save_markdown("02_architecture.md", result["architect_output"], OUTPUT_DIR)
    save_markdown("03_developer_raw_output.json", result["developer_output"], OUTPUT_DIR)
    save_markdown("04_tester_raw_output.json", result["tester_output"], OUTPUT_DIR)
    save_markdown("05_code_review.md", result["reviewer_output"], OUTPUT_DIR)
    save_markdown("summary.md", result["final_output"], OUTPUT_DIR)

    # Angular-Projektdateien speichern
    print("Speichere Angular-Projektdateien...")
    try:
        saved_dev_files = save_files_from_json(result["developer_output"], OUTPUT_DIR)
    except Exception as e:
        print("Fehler beim Speichern der Developer-Dateien.")
        print("Prüfe 03_developer_raw_output.json")
        raise e

    print("Speichere Testdateien...")
    try:
        saved_test_files = save_files_from_json(result["tester_output"], OUTPUT_DIR)
    except Exception as e:
        print("Fehler beim Speichern der Tester-Dateien.")
        print("Prüfe 04_tester_raw_output.json")
        raise e

    print("")
    print("Fertig!")
    print(f"Projekt wurde gespeichert unter:")
    print(OUTPUT_DIR)
    print("")
    print("Gespeicherte Developer-Dateien:")
    for file in saved_dev_files:
        print(f"- {file}")

    print("")
    print("Gespeicherte Test-Dateien:")
    for file in saved_test_files:
        print(f"- {file}")

    print("")
    print("Nächste Schritte:")
    print(f"cd \"{OUTPUT_DIR}\"")
    print("npm install")
    print("npm start")