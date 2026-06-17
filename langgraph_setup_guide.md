# Setup-Anleitung: LangGraph Multi-Agent Orchestrator (Codex CLI)

## 1. Ziel des Setups

Diese Anleitung beschreibt, wie der **`codex_orchestrator_multi_agent.py`** eingerichtet und ausgeführt wird. Der Orchestrator koordiniert über einen LangGraph-Graphen fünf spezialisierte Rollen:

- **Product Owner Agent** (LLM) – erstellt strukturierte Anforderungen aus dem User-Request
- **Architect Agent** (LLM) – entwirft Architektur und zerlegt die Implementierung in Work Items
- **Developer Agent** (Codex CLI) – implementiert den Code je Work Item
- **Tester Agent** (Codex CLI) – schreibt Tests im selben Arbeitsverzeichnis
- **Reviewer Agent** (LLM) – bewertet das Ergebnis (Pass/Fail); bei Fail wird ein Korrekturlauf ausgelöst (max. 1 Iteration)

---

## 2. Voraussetzungen

### Python

Empfohlen: Python 3.11 oder neuer.

```powershell
py --version
```

### Node.js & npm

Wird ausschließlich für die Codex CLI benötigt.

```powershell
node -v
npm -v
```

### Codex CLI

```powershell
npm install -g @openai/codex
codex --version
```

Auf Windows kann es vorkommen, dass `codex` nicht direkt auf `PATH` liegt. In diesem Fall findet der Orchestrator die ausführbare Datei automatisch unter bekannten Installationsorten (z.B. `%LOCALAPPDATA%\Programs\OpenAI\Codex\bin\codex.exe`).

### OpenAI API Key

Der Key muss in der Umgebung verfügbar sein – entweder über eine `.env`-Datei im Orchestrator-Verzeichnis oder als Systemvariable:

```env
OPENAI_API_KEY=dein_openai_api_key_hier
```

---

## 3. Python-Umgebung einrichten

Im Orchestrator-Verzeichnis eine virtuelle Python-Umgebung erstellen:

```powershell
cd <Pfad-zum-Orchestrators-Ordner>
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Falls PowerShell die Ausführung blockiert:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\.venv\Scripts\Activate.ps1
```

---

## 4. Python-Abhängigkeiten installieren

```powershell
py -m pip install --upgrade pip
pip install langgraph langchain-openai python-dotenv
```

Die benötigten Pakete:

| Paket | Zweck |
|---|---|
| `langgraph` | Graph-basierte Agenten-Orchestrierung |
| `langchain-openai` | OpenAI-Anbindung für PO, Architect und Reviewer |
| `python-dotenv` | Laden von `OPENAI_API_KEY` aus `.env` |

---

## 5. OpenAI API Key konfigurieren

Im Orchestrator-Verzeichnis eine `.env`-Datei anlegen:

```powershell
New-Item .env
```

Inhalt:

```env
OPENAI_API_KEY=dein_openai_api_key_hier
OPENAI_MODEL=gpt-4o-mini
```

- `OPENAI_API_KEY` wird vom Orchestrator für LLM-Aufrufe (PO, Architect, Reviewer) **und** von der Codex CLI verwendet.
- `OPENAI_MODEL` gilt für die LLM-Agenten. Das Modell für Codex CLI wird separat per `--codex-model` übergeben.

Wichtig: Die `.env`-Datei nicht in Git einchecken.

---

## 6. Rollen-Prompts prüfen

Der Orchestrator liest fünf Prompt-Dateien aus `prompts/multi_agent/`. Alle müssen vorhanden sein:

```text
prompts/multi_agent/product_owner.md
prompts/multi_agent/architect.md
prompts/multi_agent/developer.md
prompts/multi_agent/tester.md
prompts/multi_agent/reviewer.md
```

Der Pfad wird automatisch relativ zur Orchestrator-Datei aufgelöst. Er kann per `--prompts-dir` überschrieben werden.

---

## 7. LangGraph-Workflow: Ablauf

```text
START
  ↓
Product Owner Agent (LLM)   → requirements.md
  ↓
Architect Agent (LLM)       → architecture.md + Work Items
  ↓
Developer Agent (Codex CLI) → code/ (parallelisierbar je Work Item)
  ↓
Tester Agent (Codex CLI)    → code/tests/
  ↓
Reviewer Agent (LLM)        → review.md  (verdict: Pass | Fail)
  ↓
Fail + Iteration < 1?
  ├── Ja  → Developer → Tester → Reviewer  (Korrekturlauf, max. 1×)
  └── Nein → Final Report → summary.md
  ↓
END
```

---

## 8. Orchestrator ausführen

```powershell
cd <Pfad-zum-Orchestrators-Ordner>
.\.venv\Scripts\Activate.ps1
py codex_orchestrator_multi_agent.py --codex-model gpt-5.5
```

Wichtige Parameter:

| Parameter | Standard | Beschreibung |
|---|---|---|
| `--codex-model` | `gpt-5.5` | Modell für Codex CLI (Developer & Tester) |
| `--openai-model` | `gpt-4o-mini` | Modell für LLM-Agenten (PO, Architect, Reviewer) |
| `--prompts-dir` | `../prompts/multi_agent` | Verzeichnis mit den Rollen-Prompts |
| `--max-parallel-jobs` | `1` | Anzahl paralleler Codex-Jobs (Developer & Tester) |
| `--timeout` | `600` | Sekunden je Codex-Aufruf |
| `--stream-mode` | `events+raw` | Ausgabe: `events`, `raw` oder `events+raw` |
| `--dry-run` | – | Nur Preflight-Prüfung, kein tatsächlicher Lauf |

Preflight-Check (prüft PATH, API Key und Prompts ohne Ausführung):

```powershell
py codex_orchestrator_multi_agent.py --dry-run
```

---

## 9. Häufige Probleme

### `codex` nicht auf PATH gefunden

Der Orchestrator sucht automatisch auch unter `%LOCALAPPDATA%\Programs\OpenAI\Codex\bin\codex.exe`. Falls das nicht hilft:

```powershell
# Alternativer Aufruf über npx
py codex_orchestrator_multi_agent.py --codex-cmd "npx --yes @openai/codex exec"
```

### `OPENAI_API_KEY` nicht gesetzt

Prüfen:

```powershell
$env:OPENAI_API_KEY
```

Setzen für die aktuelle Session:

```powershell
$env:OPENAI_API_KEY = "sk-..."
```

### Rollen-Prompt fehlt

Fehlermeldung beim `--dry-run`:

```text
Rollen-Prompt fehlt: ..\prompts\multi_agent\reviewer.md
```

Alle fünf `.md`-Dateien im Prompts-Verzeichnis müssen vorhanden sein (siehe Abschnitt 7).

---

## 10. Kurzablauf

```powershell
# Einmalig: Abhängigkeiten installieren
cd <Pfad-zum-Orchestrators-Ordner>
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install langgraph langchain-openai python-dotenv
npm install -g @openai/codex

# Preflight prüfen
py codex_orchestrator_multi_agent.py --dry-run

# Orchestrator starten
py codex_orchestrator_multi_agent.py --codex-model gpt-5.5
```


