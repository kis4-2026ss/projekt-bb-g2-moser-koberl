"""
LangGraph Multi-Agent Orchestrator (Rollen-spezifisch, verkaufsfertig)

Pipeline (gemaess Proposal.md, prompts/multi_agent/*.md):

    1. Product Owner Agent (LLM)        -> requirements.md
    2. Architect Agent     (LLM)        -> architecture.md + work_items
    3. Developer Agent     (Codex CLI)  -> implementiert Code je Work-Item (parallelisierbar)
    4. Tester Agent        (Codex CLI)  -> erstellt Tests im selben Workdir
    5. Reviewer Agent      (LLM)        -> Pass/Fail-Review mit Korrektur-Anweisungen
       -> bei "Fail" und review_iteration < 1: zurueck zu Developer (max. 1 Korrektur-Lauf),
          danach erneut Tester + Reviewer.
    6. Final Report                     -> summary.md

Unterschiede zur Roles-Variante:
- System-Prompts kommen aus prompts/multi_agent/{product_owner,architect,developer,tester,reviewer}.md
- Reviewer liefert strukturiertes JSON (verdict + developer_corrections), wodurch ein
  Pass/Fail-Loop mit max. 1 Iteration moeglich wird.
- Default-Request beschreibt einen verkaufsfertigen Sneaker-Webshop (Hero, Markenfilter,
  Suche, Reviews, Checkout, Footer; kein oeffentliches /docs; kein FastAPI-Branding).

Aufruf:
    python codex_orchestrator_multi_agent.py --request "..." --output-dir "..." \
        --max-parallel-jobs 2 --stream-mode events+raw --timeout 600

Setup-Vorbedingungen:
- Codex CLI auf PATH (https://github.com/openai/codex)
    Install (z.B.): npm install -g @openai/codex
    Aufruf-Schema:   codex exec "<prompt>"
- OPENAI_API_KEY in der Umgebung (sowohl fuer Codex CLI als auch PO/Architect/Reviewer)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TypedDict

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END


load_dotenv()


# ============================================================
# Farben / ANSI
# ============================================================

# Windows: ANSI Escape aktivieren
if os.name == "nt":
    os.system("")


class C:
    RESET = "\033[0m"
    DIM = "\033[2m"
    BOLD = "\033[1m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    GRAY = "\033[90m"


EVENT_COLORS = {
    "run_start": C.BOLD + C.CYAN,
    "run_end": C.BOLD + C.CYAN,
    "node_start": C.BOLD + C.BLUE,
    "node_end": C.BLUE,
    "agent_thought": C.MAGENTA,
    "tool_start": C.BOLD + C.GREEN,
    "tool_end": C.GREEN,
    "raw_stdout": C.GRAY,
    "raw_stderr": C.YELLOW,
    "warning": C.YELLOW,
    "error": C.BOLD + C.RED,
    "info": C.CYAN,
}


# ============================================================
# Events
# ============================================================

@dataclass
class Event:
    ts: str
    run_id: str
    node: str
    event_type: str
    message: str
    job_id: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)


class EventBus:
    """
    Sehr einfacher synchroner Event-Bus mit Subscribern.
    Thread-sicher per Lock.
    """

    def __init__(self) -> None:
        self._subscribers: List[Callable[[Event], None]] = []
        self._lock = threading.Lock()

    def subscribe(self, fn: Callable[[Event], None]) -> None:
        self._subscribers.append(fn)

    def emit(
        self,
        event_type: str,
        node: str,
        message: str,
        run_id: str,
        job_id: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        ev = Event(
            ts=datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            run_id=run_id,
            node=node,
            event_type=event_type,
            message=message,
            job_id=job_id,
            payload=payload or {},
        )
        with self._lock:
            for sub in self._subscribers:
                try:
                    sub(ev)
                except Exception as exc:  # noqa: BLE001
                    sys.stderr.write(f"[event-bus] subscriber error: {exc}\n")


def make_console_subscriber(stream_mode: str) -> Callable[[Event], None]:
    """
    stream_mode:
      - "events"      -> nur strukturierte Events
      - "raw"         -> nur Rohstream
      - "events+raw"  -> beides
    """
    show_events = stream_mode in ("events", "events+raw")
    show_raw = stream_mode in ("raw", "events+raw")

    def _print(ev: Event) -> None:
        is_raw = ev.event_type in ("raw_stdout", "raw_stderr")
        if is_raw and not show_raw:
            return
        if not is_raw and not show_events:
            return

        color = EVENT_COLORS.get(ev.event_type, C.RESET)
        tag_job = f" job={ev.job_id}" if ev.job_id else ""
        short_ts = ev.ts.split("T", 1)[1][:12] if "T" in ev.ts else ev.ts
        prefix = (
            f"{C.DIM}{short_ts}{C.RESET} {color}[{ev.event_type:<11}]{C.RESET} "
            f"{C.BOLD}{ev.node}{C.RESET}{tag_job}"
        )
        if is_raw:
            print(f"{prefix} {C.DIM}|{C.RESET} {ev.message}")
        else:
            print(f"{prefix} {C.DIM}->{C.RESET} {ev.message}")

    return _print


def make_jsonl_subscriber(path: Path) -> Callable[[Event], None]:
    path.parent.mkdir(parents=True, exist_ok=True)
    fh = open(path, "a", encoding="utf-8")
    lock = threading.Lock()

    def _write(ev: Event) -> None:
        with lock:
            fh.write(json.dumps(asdict(ev), ensure_ascii=False) + "\n")
            fh.flush()

    return _write


# ============================================================
# Codex CLI Runner
# ============================================================

@dataclass
class CliResult:
    job_id: str
    exit_code: int
    stdout: str
    stderr: str
    duration_s: float
    timed_out: bool = False


# Default: nicht-interaktiver Codex-Aufruf.
# Schema:  codex exec "<prompt>"
# Alternativen: ["npx", "--yes", "@openai/codex", "exec"]
DEFAULT_CODEX_CMD: List[str] = ["codex", "exec"]

# Bekannte Installationsorte fuer codex.exe (Windows), die zusaetzlich zu PATH durchsucht werden.
KNOWN_CODEX_PATHS: List[Path] = [
    Path(os.path.expandvars(r"%LOCALAPPDATA%\Programs\OpenAI\Codex\bin\codex.exe")),
    Path(os.path.expandvars(r"%LOCALAPPDATA%\Programs\OpenAI\Codex\codex.exe")),
]


def resolve_cmd(base_cmd: List[str]) -> Optional[List[str]]:
    """
    Stellt sicher, dass das erste Element ein auffindbares Executable ist.
    Auf Windows liefert shutil.which fuer 'codex' z.B. 'codex.cmd'.
    Faellt fuer 'codex' auf bekannte Installationsorte zurueck.
    """
    if not base_cmd:
        return None
    launcher = base_cmd[0]
    resolved = shutil.which(launcher)
    if resolved is None and launcher.lower() in ("codex", "codex.exe"):
        for candidate in KNOWN_CODEX_PATHS:
            if candidate.is_file():
                resolved = str(candidate)
                break
    if resolved is None:
        return None
    return [resolved, *base_cmd[1:]]


class CodexRunner:
    """
    Kapselt subprocess-Aufrufe an Codex CLI (per Default 'codex exec').
    Streamt stdout/stderr live.
    """

    def __init__(
        self,
        bus: EventBus,
        run_id: str,
        raw_dir: Path,
        timeout: int,
        base_cmd: Optional[List[str]] = None,
        work_dir: Optional[Path] = None,
        node_label: str = "codex_cli",
        model: Optional[str] = None,
    ) -> None:
        self.bus = bus
        self.run_id = run_id
        self.raw_dir = raw_dir
        self.timeout = timeout
        self.base_cmd: List[str] = list(base_cmd) if base_cmd else list(DEFAULT_CODEX_CMD)
        self.work_dir: Optional[Path] = work_dir
        self.node_label = node_label
        self.model: Optional[str] = model

    def _emit(
        self,
        ev_type: str,
        msg: str,
        job_id: Optional[str] = None,
        payload: Optional[dict] = None,
    ) -> None:
        self.bus.emit(
            ev_type,
            node=self.node_label,
            message=msg,
            run_id=self.run_id,
            job_id=job_id,
            payload=payload,
        )

    def run(self, prompt: str, job_id: str) -> CliResult:
        resolved = resolve_cmd(self.base_cmd)
        if resolved is None:
            self._emit(
                "error",
                f"Kommando '{self.base_cmd[0]}' nicht auf PATH gefunden "
                f"(Aufruf: {' '.join(self.base_cmd)})",
                job_id=job_id,
            )
            return CliResult(
                job_id=job_id,
                exit_code=127,
                stdout="",
                stderr=f"{self.base_cmd[0]} not found",
                duration_s=0.0,
            )

        self.raw_dir.mkdir(parents=True, exist_ok=True)
        raw_path = self.raw_dir / f"{job_id}.log"

        cwd: Optional[str] = None
        if self.work_dir is not None:
            self.work_dir.mkdir(parents=True, exist_ok=True)
            cwd = str(self.work_dir)

        # Codex bricht in fremden, nicht-git Ordnern ohne --skip-git-repo-check ab.
        # workspace-write explizit setzen, damit Codex Dateien anlegen darf.
        extra_flags: List[str] = ["--skip-git-repo-check", "--sandbox", "workspace-write"]
        if self.model:
            # Codex CLI akzeptiert das Modell via -m/--model.
            extra_flags.extend(["-m", self.model])
        cmd = [*resolved, *extra_flags, prompt]
        self._emit(
            "tool_start",
            f"starte codex via '{' '.join(self.base_cmd)}' "
            f"(prompt={len(prompt)} chars, cwd={cwd or '.'})",
            job_id=job_id,
            payload={"raw_log": str(raw_path), "cmd": self.base_cmd, "cwd": cwd},
        )

        start = time.time()
        timed_out = False

        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,
                text=True,
                bufsize=1,
                encoding="utf-8",
                errors="replace",
                cwd=cwd,
            )
        except FileNotFoundError as exc:
            self._emit("error", f"Konnte codex nicht starten: {exc}", job_id=job_id)
            return CliResult(
                job_id=job_id,
                exit_code=127,
                stdout="",
                stderr=str(exc),
                duration_s=0.0,
            )

        stdout_chunks: List[str] = []
        stderr_chunks: List[str] = []
        raw_fh = open(raw_path, "w", encoding="utf-8")
        raw_lock = threading.Lock()

        def pump(stream, sink: List[str], ev_type: str) -> None:
            try:
                for line in iter(stream.readline, ""):
                    if not line:
                        break
                    line_stripped = line.rstrip("\n")
                    sink.append(line)
                    with raw_lock:
                        raw_fh.write(f"[{ev_type}] {line_stripped}\n")
                        raw_fh.flush()
                    self._emit(ev_type, line_stripped, job_id=job_id)
            except Exception as exc:  # noqa: BLE001
                self._emit("error", f"stream-error ({ev_type}): {exc}", job_id=job_id)
            finally:
                try:
                    stream.close()
                except Exception:
                    pass

        t_out = threading.Thread(
            target=pump, args=(proc.stdout, stdout_chunks, "raw_stdout"), daemon=True
        )
        t_err = threading.Thread(
            target=pump, args=(proc.stderr, stderr_chunks, "raw_stderr"), daemon=True
        )
        t_out.start()
        t_err.start()

        try:
            exit_code = proc.wait(timeout=self.timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            self._emit("warning", f"timeout nach {self.timeout}s, kille Prozess", job_id=job_id)
            proc.kill()
            try:
                exit_code = proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                exit_code = -9

        t_out.join(timeout=2)
        t_err.join(timeout=2)
        raw_fh.close()

        duration = time.time() - start
        self._emit(
            "tool_end",
            f"fertig exit={exit_code} duration={duration:.1f}s timed_out={timed_out}",
            job_id=job_id,
            payload={
                "exit_code": exit_code,
                "duration_s": round(duration, 2),
                "timed_out": timed_out,
            },
        )

        return CliResult(
            job_id=job_id,
            exit_code=exit_code,
            stdout="".join(stdout_chunks),
            stderr="".join(stderr_chunks),
            duration_s=duration,
            timed_out=timed_out,
        )

    def run_with_retry(self, prompt: str, job_id: str) -> CliResult:
        res = self.run(prompt, job_id)
        if res.exit_code == 0 and not res.timed_out:
            return res
        if "auth" in (res.stderr or "").lower() or "permission" in (res.stderr or "").lower():
            self._emit("error", "Auth-Problem, kein Retry", job_id=job_id)
            return res
        self._emit("warning", "retry 1/1", job_id=job_id)
        return self.run(prompt, job_id + "_retry")


# ============================================================
# Hilfsfunktionen
# ============================================================

def extract_json_block(text: str) -> Any:
    """
    Versucht robust ein JSON-Objekt aus dem LLM-Output zu ziehen.
    Reihenfolge der Versuche:
      1. Direktes json.loads(text)
      2. ```json ... ``` oder ``` ... ```-Codeblock
      3. Erstes balanciertes {...} im Text (Brace-Matching, beruecksichtigt Strings).
    """
    text = text.strip()
    if not text:
        raise ValueError("leerer LLM-Output")

    # 1) direkter Parse
    try:
        return json.loads(text)
    except Exception:
        pass

    # 2) Codeblock
    m = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if m:
        candidate = m.group(1).strip()
        try:
            return json.loads(candidate)
        except Exception:
            pass

    # 3) Erstes balanciertes {...} (mit String-/Escape-Beruecksichtigung)
    start = text.find("{")
    while start != -1:
        depth = 0
        in_str = False
        escape = False
        for i in range(start, len(text)):
            ch = text[i]
            if in_str:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    in_str = False
            else:
                if ch == '"':
                    in_str = True
                elif ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        candidate = text[start : i + 1]
                        try:
                            return json.loads(candidate)
                        except Exception:
                            break
        # naechste Klammer probieren
        start = text.find("{", start + 1)

    raise ValueError("kein gueltiger JSON-Block im LLM-Output gefunden")


def llm_invoke_json(
    llm: ChatOpenAI,
    system_prompt: str,
    human_prompt: str,
    bus: EventBus,
    run_id: str,
    node: str,
) -> Any:
    """
    Ruft das LLM auf und erzwingt JSON-Output.
    Bei Parse-Fehler wird genau ein Repair-Retry geschickt, der das LLM
    auffordert, dieselbe Antwort als reines JSON zu wiederholen.
    """
    resp = llm.invoke([("system", system_prompt), ("human", human_prompt)])
    raw = resp.content
    try:
        return extract_json_block(raw)
    except Exception as exc:
        bus.emit(
            "warning",
            node=node,
            message=f"JSON-Parse-Fehler ({exc}); starte Repair-Retry",
            run_id=run_id,
        )

    repair_system = (
        "Du bist ein JSON-Reformatierer. Du bekommst eine Antwort eines anderen Agenten "
        "und musst sie in das geforderte JSON-Schema bringen. Antworte AUSSCHLIESSLICH "
        "mit gueltigem JSON, ohne Markdown-Codeblock, ohne Erklaerungen davor oder danach."
    )
    repair_human = (
        "Original-Anforderung an den Agenten:\n---\n"
        f"{system_prompt}\n\n{human_prompt}\n---\n\n"
        "Antwort des Agenten (potentiell mit Markdown / Erklaertext drumherum):\n---\n"
        f"{raw}\n---\n\n"
        "Extrahiere die enthaltene Information und gib sie als reines JSON-Objekt zurueck, "
        "das exakt dem im Original geforderten Schema entspricht. Wenn die Antwort kein JSON "
        "enthaelt, baue selbst aus dem Inhalt ein passendes JSON. Antworte NUR mit JSON."
    )
    resp2 = llm.invoke([("system", repair_system), ("human", repair_human)])
    return extract_json_block(resp2.content)


def short_id() -> str:
    return uuid.uuid4().hex[:8]


def safe_name(text: str, length: int = 40) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]+", "_", text)[:length]


# ============================================================
# Rollen-Prompts laden
# ============================================================

ROLE_FILES: Dict[str, str] = {
    "product_owner": "product_owner.md",
    "architect": "architect.md",
    "developer": "developer.md",
    "tester": "tester.md",
    "reviewer": "reviewer.md",
}


def load_role_prompts(prompts_dir: Path) -> Dict[str, str]:
    """
    Liest die fuenf Rollen-System-Prompts aus prompts_dir.
    Wirft FileNotFoundError, wenn eine Rolle fehlt.
    """
    prompts: Dict[str, str] = {}
    for role, filename in ROLE_FILES.items():
        path = prompts_dir / filename
        if not path.is_file():
            raise FileNotFoundError(f"Rollen-Prompt fehlt: {path}")
        prompts[role] = path.read_text(encoding="utf-8").strip()
    return prompts


# ============================================================
# State
# ============================================================

class WorkItem(TypedDict):
    id: str
    title: str
    prompt: str


class Artifact(TypedDict):
    work_item_id: str
    title: str
    content: str
    exit_code: int
    timed_out: bool
    role: str  # 'developer' oder 'tester'
    iteration: int


class OrchestratorState(TypedDict, total=False):
    run_id: str
    user_request: str
    output_dir: str
    max_parallel_jobs: int
    # Phase 1: Product Owner
    requirements: str
    # Phase 2: Architect
    architecture: str
    work_items: List[WorkItem]
    # Phase 3 + 4: Developer + Tester (beide Codex)
    dev_artifacts: List[Artifact]
    test_artifacts: List[Artifact]
    # Phase 5: Reviewer (Pass/Fail)
    review_report: str
    review_status: str        # 'pass' | 'fail' | 'unknown'
    review_iteration: int     # 0 = erster Lauf, 1 = nach Korrektur
    review_feedback: str      # Korrektur-Anweisungen vom Reviewer fuer den Developer
    # Phase 6: Final
    final_report: str
    errors: List[Dict[str, Any]]


# ============================================================
# Globale Laufzeitobjekte (per Run gesetzt)
# ============================================================

@dataclass
class Runtime:
    bus: EventBus
    dev_runner: CodexRunner
    test_runner: CodexRunner
    llm: ChatOpenAI
    output_dir: Path
    role_prompts: Dict[str, str]


RUNTIME: Optional[Runtime] = None


def rt() -> Runtime:
    assert RUNTIME is not None, "Runtime nicht initialisiert"
    return RUNTIME


# ============================================================
# Agenten / Nodes
# ============================================================

def product_owner_node(state: OrchestratorState) -> OrchestratorState:
    """
    Product Owner Agent (LLM):
    Macht aus dem User-Request strukturierte Anforderungen / User Stories.
    System-Prompt: prompts/multi_agent/product_owner.md.
    """
    run_id = state["run_id"]
    rt().bus.emit(
        "node_start",
        node="product_owner",
        message="erstelle Anforderungen / User Stories",
        run_id=run_id,
    )

    sys_prompt = rt().role_prompts["product_owner"]
    human_prompt = f"""
Projekt-Request:
---
{state["user_request"]}
---

Liefere ein Markdown-Dokument mit folgenden Abschnitten:
1. **Produktvision** (2-3 Saetze)
2. **Funktionale Anforderungen** (nummeriert, knapp)
3. **Nicht-funktionale Anforderungen** (Tech-Stack-Vorgaben aus dem Request, Performance, Qualitaet)
4. **User Stories** im Format "Als <Rolle> moechte ich <Funktion>, damit <Nutzen>." mit
   jeweils einer Liste von **Akzeptanzkriterien** (Given/When/Then oder Checkliste).
5. **Definition of Done** fuer das gesamte Projekt.

Konzentriere dich auf das WAS (fachlich), nicht auf das WIE (technisch).
"""
    resp = rt().llm.invoke([("system", sys_prompt), ("human", human_prompt)])
    requirements = resp.content

    (rt().output_dir / "requirements.md").write_text(requirements, encoding="utf-8")

    rt().bus.emit(
        "agent_thought",
        node="product_owner",
        message=f"Anforderungen erstellt ({len(requirements)} chars)",
        run_id=run_id,
    )
    rt().bus.emit(
        "node_end",
        node="product_owner",
        message="requirements.md geschrieben",
        run_id=run_id,
    )
    return {"requirements": requirements}


def architect_node(state: OrchestratorState) -> OrchestratorState:
    """
    Architect Agent (LLM):
    Erstellt architecture.md UND zerlegt die Implementierung in 2-5 Work Items.
    System-Prompt: prompts/multi_agent/architect.md (+ JSON-Format-Anweisung).
    """
    run_id = state["run_id"]
    rt().bus.emit(
        "node_start",
        node="architect",
        message="entwerfe Architektur + Work-Items",
        run_id=run_id,
    )

    sys_prompt = (
        "## STRIKTE OUTPUT-VORGABE (HOECHSTE PRIORITAET)\n"
        "Antworte AUSSCHLIESSLICH als ein einzelnes valides JSON-Objekt. "
        "KEIN Markdown drumherum, KEINE Codeblocks, KEIN Vor- oder Nachtext. "
        "Das JSON-Objekt MUSS exakt zwei Felder haben:\n"
        "  - 'architecture' (String, Markdown-Inhalt erlaubt INNERHALB des Strings)\n"
        "  - 'work_items'   (Liste von Objekten mit 'title' und 'prompt')\n"
        "Die nachfolgende Rollenbeschreibung gilt fuer den Inhalt; die Form bleibt JSON.\n"
        "Die Datei 'architecture.md' wird NICHT von dir geschrieben - der Orchestrator "
        "speichert den Wert von 'architecture' selbst. Du gibst NUR JSON zurueck.\n\n"
        "## Rollenbeschreibung\n"
        + rt().role_prompts["architect"]
    )
    human_prompt = f"""
Anforderungen (vom Product Owner):
---
{state["requirements"]}
---

Original-Request (zur Sicherheit, falls Tech-Stack-Details fehlen):
---
{state["user_request"]}
---

Liefere AUSSCHLIESSLICH dieses JSON-Objekt (kein Markdown drumherum, keine Erklaerungen):
{{
  "architecture": "Markdown-Text mit: Komponenten-Uebersicht, Datenmodell (Tabellen + Felder), API-Endpunkten (Methode, Pfad, Payload, Response), Web-Component-Liste, Dateilayout (Tree), wichtigen Tech-Entscheidungen.",
  "work_items": [
    {{
      "title": "Kurzer Titel",
      "prompt": "Vollstaendiger eigenstaendiger Prompt fuer Codex CLI. Enthaelt Kontext aus der Architektur, Zieldatei(en), Sprache, Tech-Stack, erwartetes Output-Format."
    }}
  ]
}}
"""
    architecture = ""
    items_raw: List[Dict[str, Any]] = []
    try:
        data = llm_invoke_json(
            rt().llm, sys_prompt, human_prompt, rt().bus, run_id, node="architect"
        )
        architecture = data.get("architecture", "") or ""
        items_raw = data.get("work_items", []) or []
    except Exception as exc:  # noqa: BLE001
        rt().bus.emit(
            "error",
            node="architect",
            message=f"JSON-Parse-Fehler (auch nach Repair): {exc}",
            run_id=run_id,
        )

    work_items: List[WorkItem] = []
    for i, it in enumerate(items_raw, start=1):
        wid = f"wi{i:02d}_{short_id()}"
        work_items.append(
            WorkItem(
                id=wid,
                title=it.get("title", f"task_{i}"),
                prompt=it.get("prompt", ""),
            )
        )
        rt().bus.emit(
            "agent_thought",
            node="architect",
            message=f"plant {wid}: {it.get('title','')}",
            run_id=run_id,
            payload={"work_item": wid},
        )

    if architecture:
        (rt().output_dir / "architecture.md").write_text(architecture, encoding="utf-8")

    rt().bus.emit(
        "node_end",
        node="architect",
        message=f"Architektur + {len(work_items)} Work-Items erstellt",
        run_id=run_id,
    )
    return {
        "architecture": architecture,
        "work_items": work_items,
        "review_iteration": 0,
        "review_status": "unknown",
        "review_feedback": "",
    }


def _build_developer_prompt(
    wi: WorkItem,
    architecture: str,
    iteration: int,
    review_feedback: str,
) -> str:
    """
    Setzt den Developer-Prompt aus Rollenbeschreibung, Architektur-Kontext, Work-Item
    und ggf. Reviewer-Korrekturhinweisen zusammen.
    """
    role_prompt = rt().role_prompts["developer"]
    arch_excerpt = (architecture or "").strip()
    if len(arch_excerpt) > 3500:
        arch_excerpt = arch_excerpt[:3500] + "\n[... Architektur-Auszug gekuerzt ...]"

    correction_block = ""
    if iteration > 0 and review_feedback.strip():
        correction_block = (
            "\n## Korrektur-Lauf (Iteration {it})\n"
            "Der Reviewer hat die erste Implementierung mit 'Fail' bewertet. "
            "Im aktuellen Arbeitsverzeichnis liegt bereits Code. **Aendere ausschliesslich "
            "die unten genannten Stellen**, lasse den Rest der Implementierung intakt. "
            "Schreibe keinen Code von Grund auf neu.\n\n"
            "### Konkrete Korrektur-Anweisungen vom Reviewer\n"
            "{fb}\n"
        ).format(it=iteration, fb=review_feedback.strip())

    return (
        f"{role_prompt}\n\n"
        "## Architektur (vom Architect Agent)\n"
        f"{arch_excerpt}\n\n"
        f"## Work-Item: {wi['title']}\n"
        f"{wi['prompt']}\n"
        f"{correction_block}"
    )


def developer_node(state: OrchestratorState) -> OrchestratorState:
    """
    Developer Agent (Codex CLI):
    Implementiert jedes Work-Item eigenstaendig. Parallelisierbar.
    Im Korrektur-Lauf (review_iteration == 1) bekommt Codex zusaetzlich
    konkrete Korrektur-Anweisungen vom Reviewer.
    """
    run_id = state["run_id"]
    items = state.get("work_items", [])
    iteration = int(state.get("review_iteration", 0))
    review_feedback = state.get("review_feedback", "") or ""
    architecture = state.get("architecture", "") or ""
    max_workers = max(1, int(state.get("max_parallel_jobs", 2)))

    rt().bus.emit(
        "node_start",
        node="developer",
        message=(
            f"implementiere {len(items)} Work-Items via Codex "
            f"(parallel={max_workers}, iteration={iteration})"
        ),
        run_id=run_id,
    )

    artifacts: List[Artifact] = list(state.get("dev_artifacts", [])) if iteration > 0 else []
    errors: List[Dict[str, Any]] = list(state.get("errors", []))

    def _run(wi: WorkItem) -> Artifact:
        prompt = _build_developer_prompt(wi, architecture, iteration, review_feedback)
        job_id = wi["id"] if iteration == 0 else f"{wi['id']}_iter{iteration}"
        res = rt().dev_runner.run_with_retry(prompt, job_id=job_id)
        if res.exit_code != 0:
            errors.append(
                {
                    "role": "developer",
                    "iteration": iteration,
                    "work_item": wi["id"],
                    "exit_code": res.exit_code,
                    "stderr": res.stderr[:500],
                }
            )
        return Artifact(
            work_item_id=wi["id"],
            title=wi["title"],
            content=res.stdout,
            exit_code=res.exit_code,
            timed_out=res.timed_out,
            role="developer",
            iteration=iteration,
        )

    if not items:
        rt().bus.emit("warning", node="developer", message="keine work_items", run_id=run_id)
        return {"dev_artifacts": artifacts, "errors": errors}

    new_artifacts: List[Artifact] = []
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(_run, wi): wi for wi in items}
        for fut in as_completed(futures):
            wi = futures[fut]
            try:
                new_artifacts.append(fut.result())
            except Exception as exc:  # noqa: BLE001
                rt().bus.emit(
                    "error",
                    node="developer",
                    message=f"job {wi['id']} crashed: {exc}",
                    run_id=run_id,
                    job_id=wi["id"],
                )
                errors.append(
                    {
                        "role": "developer",
                        "iteration": iteration,
                        "work_item": wi["id"],
                        "exit_code": -1,
                        "stderr": str(exc),
                    }
                )

    artifacts.extend(new_artifacts)

    suffix = "" if iteration == 0 else f"_iter{iteration}"
    artifacts_dir = rt().output_dir / "artifacts" / "developer"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    for a in new_artifacts:
        (
            artifacts_dir
            / f"{a['work_item_id']}{suffix}__{safe_name(a['title'])}.md"
        ).write_text(
            f"# [Developer iter={a['iteration']}] {a['title']}\n\n"
            f"exit_code: {a['exit_code']}\n\n---\n\n{a['content']}\n",
            encoding="utf-8",
        )

    rt().bus.emit(
        "node_end",
        node="developer",
        message=(
            f"{len(new_artifacts)} neue Dev-Artefakte (iter={iteration}), "
            f"gesamt={len(artifacts)}, Fehler={len(errors)}"
        ),
        run_id=run_id,
    )
    return {"dev_artifacts": artifacts, "errors": errors}


def _build_tester_prompt(
    wi: WorkItem,
    dev_artifact: Optional[Artifact],
    iteration: int,
) -> str:
    role_prompt = rt().role_prompts["tester"]
    dev_summary = ""
    if dev_artifact is not None:
        head = (dev_artifact.get("content") or "").strip()
        if len(head) > 2000:
            head = head[:2000] + "\n[... gekuerzt ...]"
        dev_summary = (
            "\n## Zusammenfassung der Developer-Implementierung\n"
            f"---\n{head}\n---\n"
        )

    iter_note = ""
    if iteration > 0:
        iter_note = (
            f"\n## Hinweis (Iteration {iteration})\n"
            "Der Code wurde nach einem 'Fail'-Review angepasst. "
            "Aktualisiere bestehende Tests bei Bedarf und ergaenze neue Tests fuer "
            "die korrigierten Stellen.\n"
        )

    return (
        f"{role_prompt}\n\n"
        f"## Work-Item: {wi['title']}\n"
        f"## Urspruengliche Entwickler-Aufgabe (Kontext)\n"
        f"---\n{wi['prompt']}\n---\n"
        f"{dev_summary}"
        f"{iter_note}\n"
        "## Konkrete Vorgaben fuer die Tests\n"
        "- Verwende pytest.\n"
        "- Lege Tests in ./tests/ ab (Pfad relativ zum Projekt-Root, lege den Ordner an falls noetig).\n"
        "- Decke Happy-Path UND mindestens 2 Edge Cases / Fehlerfaelle ab.\n"
        "- Fuer HTTP-APIs: nutze TestClient/HTTPX gegen die FastAPI-App.\n"
        "- Keine Mocks, wo echte Aufrufe einfach moeglich sind (SQLite-Test-DB ist ok).\n"
        "- Fuege ggf. notwendige Test-Dependencies in requirements-dev.txt hinzu.\n"
        "- Aendere produktiven Code NUR, wenn er offensichtlich nicht testbar ist; "
        "  dokumentiere solche Aenderungen in der Antwort.\n"
        "- Gib am Ende eine kurze Liste der angelegten Testdateien aus."
    )


def tester_node(state: OrchestratorState) -> OrchestratorState:
    """
    Tester Agent (Codex CLI):
    Erzeugt Tests fuer den vom Developer geschriebenen Code im selben Workdir.
    """
    run_id = state["run_id"]
    work_items = state.get("work_items", [])
    dev_artifacts = state.get("dev_artifacts", [])
    iteration = int(state.get("review_iteration", 0))
    max_workers = max(1, int(state.get("max_parallel_jobs", 2)))

    rt().bus.emit(
        "node_start",
        node="tester",
        message=(
            f"erstelle Tests via Codex fuer {len(work_items)} Work-Items "
            f"(parallel={max_workers}, iteration={iteration})"
        ),
        run_id=run_id,
    )

    errors: List[Dict[str, Any]] = list(state.get("errors", []))

    # Lookup: pro Work-Item das aktuellste Dev-Artefakt (groesste iteration).
    dev_by_id: Dict[str, Artifact] = {}
    for a in dev_artifacts:
        cur = dev_by_id.get(a["work_item_id"])
        if cur is None or a.get("iteration", 0) >= cur.get("iteration", 0):
            dev_by_id[a["work_item_id"]] = a

    test_jobs: List[WorkItem] = [
        WorkItem(
            id=(
                f"test_{wi['id']}"
                if iteration == 0
                else f"test_{wi['id']}_iter{iteration}"
            ),
            title=f"Tests fuer {wi['title']}",
            prompt=_build_tester_prompt(wi, dev_by_id.get(wi["id"]), iteration),
        )
        for wi in work_items
    ]

    artifacts: List[Artifact] = list(state.get("test_artifacts", [])) if iteration > 0 else []

    def _run(tj: WorkItem) -> Artifact:
        res = rt().test_runner.run_with_retry(tj["prompt"], job_id=tj["id"])
        if res.exit_code != 0:
            errors.append(
                {
                    "role": "tester",
                    "iteration": iteration,
                    "work_item": tj["id"],
                    "exit_code": res.exit_code,
                    "stderr": res.stderr[:500],
                }
            )
        return Artifact(
            work_item_id=tj["id"],
            title=tj["title"],
            content=res.stdout,
            exit_code=res.exit_code,
            timed_out=res.timed_out,
            role="tester",
            iteration=iteration,
        )

    if not test_jobs:
        rt().bus.emit("warning", node="tester", message="keine Test-Jobs", run_id=run_id)
        return {"test_artifacts": artifacts, "errors": errors}

    new_artifacts: List[Artifact] = []
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(_run, tj): tj for tj in test_jobs}
        for fut in as_completed(futures):
            tj = futures[fut]
            try:
                new_artifacts.append(fut.result())
            except Exception as exc:  # noqa: BLE001
                rt().bus.emit(
                    "error",
                    node="tester",
                    message=f"job {tj['id']} crashed: {exc}",
                    run_id=run_id,
                    job_id=tj["id"],
                )
                errors.append(
                    {
                        "role": "tester",
                        "iteration": iteration,
                        "work_item": tj["id"],
                        "exit_code": -1,
                        "stderr": str(exc),
                    }
                )

    artifacts.extend(new_artifacts)

    suffix = "" if iteration == 0 else f"_iter{iteration}"
    artifacts_dir = rt().output_dir / "artifacts" / "tester"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    for a in new_artifacts:
        (
            artifacts_dir
            / f"{a['work_item_id']}{suffix}__{safe_name(a['title'])}.md"
        ).write_text(
            f"# [Tester iter={a['iteration']}] {a['title']}\n\n"
            f"exit_code: {a['exit_code']}\n\n---\n\n{a['content']}\n",
            encoding="utf-8",
        )

    rt().bus.emit(
        "node_end",
        node="tester",
        message=(
            f"{len(new_artifacts)} neue Test-Artefakte (iter={iteration}), "
            f"gesamt={len(artifacts)}, Fehler={len(errors)}"
        ),
        run_id=run_id,
    )
    return {"test_artifacts": artifacts, "errors": errors}


def _artifacts_as_context(
    artifacts: List[Artifact],
    max_chars: int = 6000,
    label: str = "",
    only_latest_iteration: bool = True,
) -> str:
    if only_latest_iteration and artifacts:
        latest_per_item: Dict[str, Artifact] = {}
        for a in artifacts:
            cur = latest_per_item.get(a["work_item_id"])
            if cur is None or a.get("iteration", 0) >= cur.get("iteration", 0):
                latest_per_item[a["work_item_id"]] = a
        artifacts = list(latest_per_item.values())

    parts: List[str] = []
    used = 0
    for a in artifacts:
        block = (
            f"\n### [{label or a.get('role','?')} iter={a.get('iteration',0)}] "
            f"{a['title']} ({a['work_item_id']}, exit={a['exit_code']})\n\n"
            f"{a['content']}\n"
        )
        if used + len(block) > max_chars:
            parts.append(
                f"\n[... weitere Artefakte ausgelassen, Limit {max_chars} chars ...]\n"
            )
            break
        parts.append(block)
        used += len(block)
    return "".join(parts) if parts else "(keine Artefakte)"


def reviewer_node(state: OrchestratorState) -> OrchestratorState:
    """
    Reviewer Agent (LLM):
    Bewertet Code + Tests gegen Anforderungen und Architektur.
    Liefert strukturiertes JSON mit verdict + developer_corrections, damit ein
    Pass/Fail-Loop moeglich ist.
    """
    run_id = state["run_id"]
    iteration = int(state.get("review_iteration", 0))
    rt().bus.emit(
        "node_start",
        node="reviewer",
        message=f"fuehre Code-Review durch (iteration={iteration})",
        run_id=run_id,
    )

    dev_ctx = _artifacts_as_context(state.get("dev_artifacts", []), label="developer")
    test_ctx = _artifacts_as_context(state.get("test_artifacts", []), label="tester")
    arch = (state.get("architecture", "") or "")[:3000]
    reqs = (state.get("requirements", "") or "")[:3000]

    sys_prompt = (
        "## STRIKTE OUTPUT-VORGABE (HOECHSTE PRIORITAET)\n"
        "Antworte AUSSCHLIESSLICH als ein einzelnes valides JSON-Objekt. "
        "KEIN Markdown drumherum, KEINE Codeblocks, KEIN Vor- oder Nachtext. "
        "Das JSON-Objekt MUSS exakt diese Felder haben:\n"
        "  - 'verdict':  'Pass' oder 'Fail'\n"
        "  - 'summary':  Markdown-Kurzfazit (2-4 Saetze)\n"
        "  - 'findings': Markdown-Liste mit Befunden\n"
        "  - 'developer_corrections': Markdown-Liste konkreter Korrektur-Anweisungen "
        "(leer bei Pass)\n"
        "Setze 'Fail' nur, wenn es echte funktionale Luecken oder Bugs gibt. "
        "Stilistische Wuensche allein sind kein 'Fail'.\n"
        "Die nachfolgende Rollenbeschreibung gilt fuer den Inhalt; die Form bleibt JSON.\n\n"
        "## Rollenbeschreibung\n"
        + rt().role_prompts["reviewer"]
    )

    iteration_note = ""
    if iteration > 0:
        iteration_note = (
            "\n\nHinweis: Dies ist die Bewertung NACH einem Korrektur-Lauf. "
            "Sei tendenziell milder, sofern die ursspruenglich genannten Punkte "
            "behoben wurden."
        )

    human_prompt = f"""
## Anforderungen (Product Owner)
{reqs}

## Architektur (Architect)
{arch}

## Developer-Artefakte (aktuelle Iteration)
{dev_ctx}

## Tester-Artefakte (aktuelle Iteration)
{test_ctx}
{iteration_note}

Antworte AUSSCHLIESSLICH als JSON in genau folgendem Format:
{{
  "verdict": "Pass" | "Fail",
  "summary": "Markdown-Kurzfazit (2-4 Saetze)",
  "findings": "Markdown-Liste mit Befunden",
  "developer_corrections": "Markdown-Liste konkreter Korrektur-Anweisungen (leer bei Pass)"
}}
"""
    verdict = "unknown"
    summary = ""
    findings = ""
    corrections = ""
    parse_error: Optional[str] = None
    raw = ""
    try:
        data = llm_invoke_json(
            rt().llm, sys_prompt, human_prompt, rt().bus, run_id, node="reviewer"
        )
        v = str(data.get("verdict", "")).strip().lower()
        if v.startswith("pass"):
            verdict = "pass"
        elif v.startswith("fail"):
            verdict = "fail"
        summary = str(data.get("summary", "")).strip()
        findings = str(data.get("findings", "")).strip()
        corrections = str(data.get("developer_corrections", "")).strip()
    except Exception as exc:  # noqa: BLE001
        parse_error = str(exc)
        rt().bus.emit(
            "error",
            node="reviewer",
            message=f"JSON-Parse-Fehler (auch nach Repair): {exc}",
            run_id=run_id,
        )
        # Soft fallback: kein Loop, generischer Hinweis im Bericht.
        summary = "(Reviewer-Antwort konnte nicht als JSON geparst werden.)"
        findings = "(siehe events.jsonl / raw Logs)"

    review_md_lines: List[str] = []
    review_md_lines.append(f"# Review (Iteration {iteration})\n")
    review_md_lines.append(f"**Verdict:** {verdict.upper()}\n")
    if parse_error:
        review_md_lines.append(f"\n> Hinweis: JSON-Parse-Fehler ({parse_error}). "
                               f"Volltext der LLM-Antwort folgt unter 'Findings'.\n")
    review_md_lines.append("## Kurzfazit\n")
    review_md_lines.append(summary or "(leer)")
    review_md_lines.append("\n## Findings\n")
    review_md_lines.append(findings or "(leer)")
    review_md_lines.append("\n## Developer-Korrektur-Anweisungen\n")
    review_md_lines.append(corrections or "(leer)")
    review_md = "\n".join(review_md_lines)

    # Pro Iteration eigene Datei + immer aktuelle als review.md.
    (rt().output_dir / f"review_iter{iteration}.md").write_text(review_md, encoding="utf-8")
    (rt().output_dir / "review.md").write_text(review_md, encoding="utf-8")

    rt().bus.emit(
        "node_end",
        node="reviewer",
        message=f"review.md geschrieben (verdict={verdict})",
        run_id=run_id,
    )
    return {
        "review_report": review_md,
        "review_status": verdict,
        "review_feedback": corrections,
    }


def route_after_review(state: OrchestratorState) -> str:
    """
    Conditional Edge: bei 'Fail' und Iteration < 1 erneut Developer ansteuern,
    sonst Final-Report. JSON-Parse-Fehler ('unknown') laufen direkt zum Final-Report.
    """
    verdict = state.get("review_status", "unknown")
    iteration = int(state.get("review_iteration", 0))
    if verdict == "fail" and iteration < 1:
        rt().bus.emit(
            "info",
            node="reviewer",
            message="verdict=fail -> starte Korrektur-Lauf (iteration 1)",
            run_id=state["run_id"],
        )
        return "developer_redo"
    return "done"


def increment_iteration_node(state: OrchestratorState) -> OrchestratorState:
    """
    Setzt review_iteration auf 1, bevor erneut Developer/Tester laufen.
    """
    rt().bus.emit(
        "info",
        node="reviewer",
        message="erhoehe review_iteration -> 1",
        run_id=state["run_id"],
    )
    return {"review_iteration": 1}


def final_report_node(state: OrchestratorState) -> OrchestratorState:
    run_id = state["run_id"]
    rt().bus.emit(
        "node_start",
        node="final_report",
        message="erstelle Zusammenfassung",
        run_id=run_id,
    )

    dev_artifacts = state.get("dev_artifacts", [])
    test_artifacts = state.get("test_artifacts", [])
    errors = state.get("errors", [])
    verdict = state.get("review_status", "unknown")
    iteration = int(state.get("review_iteration", 0))

    lines: List[str] = []
    lines.append(f"# Orchestrator Run {run_id} (Multi-Agent, rollenspezifisch)\n")
    lines.append(f"- Zeit: {datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}")
    lines.append(f"- Output: {state.get('output_dir')}")
    lines.append(f"- Review-Verdict: **{verdict.upper()}**")
    lines.append(f"- Review-Iterationen: {iteration} (0 = einmaliger Lauf, 1 = inkl. Korrektur)")
    lines.append(f"- Dev-Artefakte: {len(dev_artifacts)}")
    lines.append(f"- Test-Artefakte: {len(test_artifacts)}")
    lines.append(f"- Fehler: {len(errors)}\n")

    lines.append("## Rollen-Pipeline\n")
    lines.append("1. Product Owner (LLM) -> requirements.md")
    lines.append("2. Architect (LLM)     -> architecture.md + work_items")
    lines.append("3. Developer (Codex)   -> code/ + artifacts/developer/")
    lines.append("4. Tester (Codex)      -> code/tests/ + artifacts/tester/")
    lines.append("5. Reviewer (LLM)      -> review.md (Pass/Fail)")
    lines.append("   -> bei Fail (max. 1 Iteration): zurueck zu Developer + Tester + Reviewer")
    lines.append("6. Final Report        -> summary.md\n")

    lines.append("## User Request\n")
    lines.append(state.get("user_request", "") + "\n")

    lines.append("## Anforderungen (Auszug)\n")
    reqs = state.get("requirements", "") or "(leer)"
    lines.append(
        reqs[:1500]
        + ("\n\n[... siehe requirements.md ...]" if len(reqs) > 1500 else "")
        + "\n"
    )

    lines.append("## Architektur (Auszug)\n")
    arch = state.get("architecture", "") or "(leer)"
    lines.append(
        arch[:1500]
        + ("\n\n[... siehe architecture.md ...]" if len(arch) > 1500 else "")
        + "\n"
    )

    lines.append("## Work Items\n")
    for wi in state.get("work_items", []):
        lines.append(f"- **{wi['id']}** — {wi['title']}")
    lines.append("")

    lines.append("## Developer-Artefakte (Zusammenfassung)\n")
    for a in dev_artifacts:
        head = (a["content"] or "")[:300].replace("\n", " ")
        lines.append(
            f"### [iter={a.get('iteration',0)}] {a['title']} "
            f"({a['work_item_id']}, exit={a['exit_code']})\n\n{head}...\n"
        )

    lines.append("## Tester-Artefakte (Zusammenfassung)\n")
    for a in test_artifacts:
        head = (a["content"] or "")[:300].replace("\n", " ")
        lines.append(
            f"### [iter={a.get('iteration',0)}] {a['title']} "
            f"({a['work_item_id']}, exit={a['exit_code']})\n\n{head}...\n"
        )

    lines.append("## Review (Auszug)\n")
    review = state.get("review_report", "") or "(leer)"
    lines.append(
        review[:2000]
        + ("\n\n[... siehe review.md ...]" if len(review) > 2000 else "")
        + "\n"
    )

    if errors:
        lines.append("\n## Fehler\n")
        for e in errors:
            lines.append(f"- {e}")

    summary = "\n".join(lines)
    (rt().output_dir / "summary.md").write_text(summary, encoding="utf-8")

    rt().bus.emit(
        "node_end",
        node="final_report",
        message="summary.md geschrieben",
        run_id=run_id,
    )
    return {"final_report": summary}


# ============================================================
# Graph
# ============================================================

def build_graph():
    g = StateGraph(OrchestratorState)
    g.add_node("product_owner", product_owner_node)
    g.add_node("architect", architect_node)
    g.add_node("developer", developer_node)
    g.add_node("tester", tester_node)
    g.add_node("reviewer", reviewer_node)
    g.add_node("increment_iteration", increment_iteration_node)
    g.add_node("final_report", final_report_node)

    g.add_edge(START, "product_owner")
    g.add_edge("product_owner", "architect")
    g.add_edge("architect", "developer")
    g.add_edge("developer", "tester")
    g.add_edge("tester", "reviewer")

    # Conditional Edge: Pass -> final_report; Fail (Iteration 0) -> increment_iteration -> developer
    g.add_conditional_edges(
        "reviewer",
        route_after_review,
        {
            "developer_redo": "increment_iteration",
            "done": "final_report",
        },
    )
    g.add_edge("increment_iteration", "developer")
    g.add_edge("final_report", END)

    return g.compile()


# ============================================================
# Setup / CLI
# ============================================================

def preflight_checks(
    output_dir: Path,
    dry_run: bool,
    codex_cmd: List[str],
    prompts_dir: Path,
) -> List[str]:
    problems: List[str] = []
    launcher = codex_cmd[0] if codex_cmd else ""
    resolved = resolve_cmd(codex_cmd) if codex_cmd else None
    if resolved is None:
        if launcher in ("npx", "npx.cmd"):
            problems.append(
                "Node/npx nicht auf PATH gefunden. Installiere Node.js (https://nodejs.org), "
                "dann startet Codex CLI ueber 'npx @openai/codex exec'."
            )
        else:
            problems.append(
                f"Launcher '{launcher}' nicht gefunden (weder auf PATH noch unter bekannten "
                "Installationsorten). Default ist 'codex exec'. "
                "Installiere via 'npm install -g @openai/codex', "
                "ueberschreibe per --codex-cmd (z.B. 'npx --yes @openai/codex exec') "
                f"oder gib den vollen Pfad an (z.B. '{KNOWN_CODEX_PATHS[0]} exec')."
            )
    if not os.getenv("OPENAI_API_KEY"):
        problems.append(
            "OPENAI_API_KEY nicht gesetzt (fuer Codex CLI sowie PO/Architect/Reviewer)."
        )
    if not prompts_dir.is_dir():
        problems.append(f"Prompts-Verzeichnis nicht gefunden: {prompts_dir}")
    else:
        for role, fname in ROLE_FILES.items():
            if not (prompts_dir / fname).is_file():
                problems.append(f"Rollen-Prompt fehlt: {prompts_dir / fname}")
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        test_file = output_dir / ".write_check"
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink()
    except Exception as exc:  # noqa: BLE001
        problems.append(f"Output-Verzeichnis nicht beschreibbar: {exc}")
    return problems


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "LangGraph Multi-Agent Orchestrator (PO/Architect/Dev/Tester/Reviewer) "
            "mit Codex CLI und Pass/Fail-Loop."
        )
    )
    p.add_argument("--request", "-r", type=str, default=None, help="User-Request als Text.")
    p.add_argument("--request-file", type=str, default=None, help="Datei mit User-Request.")
    p.add_argument(
        "--output-dir",
        "-o",
        type=str,
        default=r"C:\Users\sebas\Nextcloud\PC\Studium\KIS4\Projekt\Project-Output-Codex-MultiAgent",
        help="Output-Verzeichnis.",
    )
    default_prompts_dir = Path(__file__).resolve().parents[1] / "prompts" / "multi_agent"
    p.add_argument(
        "--prompts-dir",
        type=str,
        default=str(default_prompts_dir),
        help="Verzeichnis mit den Rollen-System-Prompts (product_owner.md, architect.md, ...).",
    )
    p.add_argument("--max-parallel-jobs", type=int, default=1)
    p.add_argument("--stream-mode", choices=["events", "raw", "events+raw"], default="events+raw")
    p.add_argument("--timeout", type=int, default=600, help="Sekunden je Codex-Aufruf.")
    p.add_argument("--openai-model", type=str, default=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                   help="Modell fuer PO/Architect/Reviewer (LLM-Agenten).")
    p.add_argument(
        "--codex-model",
        type=str,
        default=os.getenv("CODEX_MODEL", "gpt-5.5"),
        help="Modell, das die Codex CLI verwendet (per -m an codex exec uebergeben). Default: 'gpt-5.5'.",
    )
    p.add_argument(
        "--codex-cmd",
        type=str,
        default=os.getenv("CODEX_CMD", "codex exec"),
        help=(
            "Wie die Codex CLI gestartet wird. Default: 'codex exec'. "
            "Alternativ z.B. 'npx --yes @openai/codex exec'."
        ),
    )
    p.add_argument("--dry-run", action="store_true", help="Nur Preflight, kein Run.")
    return p.parse_args()


# ============================================================
# Default-User-Request: verkaufsfertiger Sneaker-Webshop
# ============================================================

DEFAULT_USER_REQUEST = """\
Baue einen vollstaendigen, verkaufsfertigen Sneaker-Webshop unter dem Markennamen
"SneakerHaus". Das Projekt ist NICHT als Studienprojekt-Demo gekennzeichnet, sondern
soll wie ein echtes, kleines E-Commerce-Produkt wirken.

# Tech-Stack (verbindlich)
- Backend: Python 3.11+ mit FastAPI, Pydantic v2, SQLAlchemy 2.x ORM, SQLite
  (DB-Datei z.B. ./data/shop.db, Pfad konfigurierbar ueber Umgebungsvariable).
- WICHTIG: FastAPI-App mit `docs_url=None, redoc_url=None, openapi_url=None`
  initialisieren. Es darf KEIN oeffentliches Swagger / ReDoc / OpenAPI geben.
- Globaler Exception-Handler:
  * `RequestValidationError` -> HTTP 400 mit JSON
    `{"error": {"code": "validation_error", "message": "..."}}`
  * `HTTPException` -> JSON `{"error": {"code": "<status_code>", "message": "<detail>"}}`
  * `Exception` -> HTTP 500 mit JSON
    `{"error": {"code": "internal_error", "message": "Es ist ein Fehler aufgetreten."}}`
    (Stacktraces NIEMALS an den Client; nur ins Server-Log).
- Frontend: native Web Components in Vanilla JavaScript (KEIN React/Vue/Angular/Svelte).
- Styling: Tailwind CSS via CDN, modernes responsives Layout (Mobile-First).
- Backend serviert das Frontend statisch (StaticFiles) UND stellt JSON-APIs unter `/api/...`.
- CORS so konfigurieren, dass das eigene Frontend das Backend ansprechen kann.
- Empfohlenes Verzeichnis-Layout:
    ./backend/app/main.py             (FastAPI app, mounted StaticFiles)
    ./backend/app/database.py         (SQLAlchemy Engine + SessionLocal + init_db)
    ./backend/app/models.py           (ORM Models)
    ./backend/app/schemas.py          (Pydantic Schemas)
    ./backend/app/api/                (Router: products, cart, orders, reviews)
    ./backend/app/seed.py             (Seed-Daten)
    ./frontend/index.html
    ./frontend/components/*.js        (Web Components)
    ./frontend/styles/*.css           (optional, primaer Tailwind)
    ./tests/                          (pytest, vom Tester-Agent gefuellt)
    ./requirements.txt
    ./README.md

# Branding & Endkunden-Polish (verbindlich)
- Markenname "SneakerHaus" konsequent in Header, Footer, README, <title>.
- Header zeigt Logo-Text "SneakerHaus", Navigation (Shop, Warenkorb), Mini-Cart-Badge.
- Im sichtbaren UI taucht NIEMALS "FastAPI", "Backend", "API", "Swagger", "/docs",
  "uvicorn" oder ein Stacktrace auf.
- Loading-Zustand mit Tailwind Skeletons (`animate-pulse`), nicht "Lade...".
- Eigene `<not-found>` Web Component fuer unbekannte Routen.
- Freundliche, deutsche Fehlertexte im Frontend (z.B. "Dieses Produkt ist leider nicht
  mehr verfuegbar." statt "404" / "Error").

# Domaene: Sneaker-Webshop
Mindestens 8 verschiedene Sneaker als Seed-Daten in der DB. Pro Sneaker:
  id, name, brand (Nike, Adidas, New Balance, Puma, Asics, Reebok, Converse, ...),
  price (EUR, Decimal/float), currency='EUR',
  short_description, long_description,
  image_url (oeffentlich erreichbare Bild-URL, z.B. Unsplash/Picsum -
    keine lokalen Binaerdateien, KEINE Platzhalter wie 'TODO').
    Bilder muessen pro Sneaker tatsaechlich UNTERSCHIEDLICH sein.
  sizes (Liste verfuegbarer EU-Groessen, z.B. [40, 41, 42, 43, 44, 45]),
  color, material, stock (int), rating (float 0..5, vorbefuellt), is_new (bool).
Preise und Bestaende realistisch und unterschiedlich.

# Funktionsumfang (alle Bereiche MUESSEN end-to-end funktionieren)

## 1. Landingpage / Produktuebersicht
- Backend: GET /api/products
  -> Liste aller Sneaker (id, name, brand, price, currency, image_url,
     short_description, is_new, rating).
  -> Optional: Query-Parameter `?brand=<name>&search=<text>` (case-insensitive contains
     auf name + short_description).
- Frontend: Web Component `<product-list api-url="/api/products">`.
  * Hero-Section ueber dem Grid mit Headline ("Sneaker, die bewegen."),
    kurzem Subtext und einem CTA-Button ("Jetzt entdecken"), der ans Grid scrollt.
  * Markenfilter als Chip-Buttons (alle Brands aus dem geladenen Datensatz, plus "Alle").
  * Suchfeld (debounced ~250ms), filtert client-seitig auf das geladene Produkt-Array
    (kein Refetch pro Tastendruck).
  * Sortierung per Dropdown: "Neu zuerst", "Preis aufsteigend", "Preis absteigend",
    "Bestbewertet".
  * Responsive Kachel-Grid (1/2/3/4 Spalten je nach Breakpoint), Cards mit Schatten,
    abgerundeten Ecken, Hover-Effekt, "Neu"-Badge bei is_new=true, Sterne-Anzeige
    fuer rating, "Details"-Link auf `/#/product/{id}`.

## 2. Produktdetailseite
- Backend: GET /api/products/{id} -> volle Detaildaten inkl. long_description, sizes,
  color, material, stock, rating. 404 (im Error-Handler-JSON-Format) bei unbekannter ID.
- Frontend: Web Component `<product-detail>`, dynamisches Routing via Hash-Router
  (`/#/product/{id}`).
  * Grosses Produktbild + alle Detailfelder.
  * Groessen-Auswahl als Buttons (ausgewaehlte Groesse hervorgehoben).
  * Mengen-Auswahl (Stepper, min 1).
  * "In den Warenkorb"-Button: ruft `POST /api/cart/items`. Bei Erfolg:
    Mini-Cart-Badge im Header aktualisieren + Inline-Bestaetigung "Zum Warenkorb hinzugefuegt".
  * Anzeige Sterne-Rating + Anzahl Reviews. Liste aller Reviews mit Author, Sterne,
    Datum, Kommentar. Formular zum Hinzufuegen einer eigenen Review (Author optional,
    Rating 1..5 als Sterne-Auswahl, Kommentar). Bei Submit: `POST /api/products/{id}/reviews`,
    Liste neu laden.

## 3. Reviews-API
- GET /api/products/{id}/reviews
  -> `{"average_rating": float, "count": int, "reviews": [...]}`,
     Reviews mit `id, author, rating(1..5), comment, created_at(ISO8601)`.
- POST /api/products/{id}/reviews
  -> Body `{"author": str|null, "rating": int(1..5), "comment": str(<=1000)}`,
     Response 201 mit der angelegten Review.
- Validierung: rating ausserhalb 1..5 -> 400 im Error-Handler-Format.
- Aggregat (average_rating, count) bei jeder Aenderung neu berechnen.

## 4. Warenkorb
- Persistenz in SQLite, pro Session-Token (Cookie ODER LocalStorage-ID, einer von beiden,
  konsistent verwendet).
- Endpoints:
    GET    /api/cart                    -> `{items[], item_count, subtotal, total}`
    POST   /api/cart/items              -> Body `{product_id, size, quantity>=1}`
    PATCH  /api/cart/items/{item_id}    -> Body `{quantity>=1}`
    DELETE /api/cart/items/{item_id}    -> 204
- Items in der Response enthalten aufgeloeste Produktdaten (name, brand, price, image_url),
  size, quantity, line_total. subtotal == sum(line_total). total == subtotal
  (Versand bleibt 0 oder explizit ausgewiesen, frei waehlbar - aber konsistent).
- Frontend: Web Component `<shopping-cart>` auf Route `/#/cart`.
  * Zeigt jede Position mit Bild, Name, Brand, Groesse, Stepper (Mengen-PATCH), Einzel-
    und Gesamtpreis, "Entfernen"-Button (DELETE).
  * Mini-Cart-Badge im Header zeigt item_count.
  * Leerer-Warenkorb-Zustand ("Dein Warenkorb ist leer.") mit CTA "Weiter shoppen".
  * Sichtbarer "Zur Kasse"-Button am Ende, der zu `/#/checkout` navigiert.

## 5. Checkout & Bestellbestaetigung (Mock-Payment)
- Backend:
    POST   /api/orders
      Body: `{"shipping": {"name", "street", "zip", "city", "country", "email"},
              "payment_method": "invoice" | "credit_card_demo"}`
      Verhalten: nimmt aktuellen Cart der Session, erzeugt Order + OrderItems,
      LEERT den Cart, antwortet 201 mit
      `{"order_id", "status": "confirmed", "created_at",
        "shipping": {...}, "payment_method", "items": [...], "subtotal", "total"}`.
      Validierung: leerer Cart -> 400 ("Dein Warenkorb ist leer.").
    GET    /api/orders/{id}             -> dieselbe Bestellung (404 wenn unbekannt).
- Datenmodell: Order(id, created_at, status, shipping_*, payment_method,
  subtotal, total, session_token), OrderItem(id, order_id, product_id, name_snapshot,
  brand_snapshot, price_snapshot, image_url_snapshot, size, quantity, line_total).
- Frontend:
    `<checkout-page>` auf Route `/#/checkout`:
      * Adressformular (Name, Strasse, PLZ, Stadt, Land=Default "Deutschland", E-Mail).
      * Zahlungsmethode als Radio-Buttons: "Auf Rechnung" (invoice),
        "Kreditkarte (Demo)" (credit_card_demo). KEIN echtes PSP, KEINE echten
        Kreditkartendaten - nur Auswahl.
      * Live-Bestelluebersicht aus `/api/cart`.
      * "Jetzt kaufen"-Button: ruft `POST /api/orders`, navigiert bei Erfolg zu
        `/#/order/{order_id}`. Bei Fehlern freundliche Inline-Meldung.
    `<order-confirmation>` auf Route `/#/order/{id}`:
      * Holt `GET /api/orders/{id}`, zeigt Bestellnummer, Datum, Lieferadresse,
        Zahlungsmethode, alle Positionen, Gesamtsumme, freundlichen Bestaetigungstext
        ("Vielen Dank fuer deine Bestellung bei SneakerHaus!").
      * CTA "Weiter shoppen" zurueck zur Startseite.

## 6. Footer & Legal
- Footer auf jeder Seite (in `index.html` oder als globale `<site-footer>`-Komponente):
  * Linke Spalte: Markenclaim "SneakerHaus - Sneaker, die bewegen.".
  * Mittlere Spalten: Links zu `/#/legal/imprint`, `/#/legal/terms`, `/#/legal/contact`.
  * Rechte Spalte: Copyright-Hinweis mit aktuellem Jahr.
- Web Components fuer die Legal-Pages mit realistischen Dummy-Inhalten (DE):
    `<imprint-page>`     (Impressum mit Firma, Adresse, Kontakt - alles fiktiv,
                          aber strukturiert wie ein echtes Impressum)
    `<terms-page>`       (kurze AGB / Widerrufsbelehrung in Stichpunkten)
    `<contact-page>`     (Kontaktformular: Name, E-Mail, Nachricht; Submit zeigt
                          "Vielen Dank, wir melden uns." - kein Backend-Endpoint noetig)

## 7. Routing-Konvention
Hash-Router im Frontend mit folgenden Routen:
    `#/`                  -> <product-list>
    `#/product/{id}`      -> <product-detail>
    `#/cart`              -> <shopping-cart>
    `#/checkout`          -> <checkout-page>
    `#/order/{id}`        -> <order-confirmation>
    `#/legal/imprint`     -> <imprint-page>
    `#/legal/terms`       -> <terms-page>
    `#/legal/contact`     -> <contact-page>
    Unbekannt              -> <not-found>

# Qualitaetsanforderungen
- Lauffaehig mit:
    pip install -r requirements.txt
    uvicorn backend.app.main:app --reload
- Beim ersten Start MUSS die DB automatisch angelegt und mit Sneaker-Seed-Daten
  gefuellt werden (idempotent: kein Doppel-Seed bei Neustart).
- Frontend muss unter http://127.0.0.1:8000/ erreichbar sein (vom Backend serviert).
- `GET /docs`, `GET /redoc`, `GET /openapi.json` muessen 404 (oder analog) liefern.
- Keine TODO-Platzhalter, keine leeren Funktionen. Alle oben genannten Bereiche
  end-to-end nutzbar (Uebersicht -> Detail -> Cart -> Checkout -> Bestellbestaetigung).
- Modernes, aufgeraeumtes Tailwind-Design (Cards mit Schatten, abgerundete Ecken,
  klare Typo, gut lesbare Preise, Hover-States, fokussierte Buttons).
- README.md (im Projekt-Root des Codes) mit Kurzbeschreibung "SneakerHaus", Setup,
  Start, kurzem Feature-Ueberblick - in Endkunden-/Demo-Tonalitaet, ohne
  Backend-/FastAPI-Jargon im Marketing-Teil.
"""


def load_request(args: argparse.Namespace) -> str:
    if args.request:
        return args.request
    if args.request_file:
        return Path(args.request_file).read_text(encoding="utf-8")
    return DEFAULT_USER_REQUEST


def main() -> int:
    global RUNTIME
    args = parse_args()

    run_id = "run_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + "_" + short_id()
    output_dir = Path(args.output_dir) / run_id
    prompts_dir = Path(args.prompts_dir)

    codex_cmd = [tok for tok in args.codex_cmd.split() if tok]

    problems = preflight_checks(output_dir, args.dry_run, codex_cmd, prompts_dir)
    if problems:
        print(f"{C.BOLD}{C.YELLOW}Preflight-Hinweise:{C.RESET}")
        for p in problems:
            print(f"  - {p}")
        critical = any(
            "PATH" in p
            or "OPENAI_API_KEY" in p
            or "Rollen-Prompt fehlt" in p
            or "Prompts-Verzeichnis" in p
            for p in problems
        )
        if critical and not args.dry_run:
            print(f"{C.BOLD}{C.RED}Abbruch: kritische Voraussetzungen fehlen.{C.RESET}")
            return 2
    if args.dry_run:
        print(
            f"{C.GREEN}Dry-Run ok.{C.RESET} "
            f"(codex-cmd: {' '.join(codex_cmd)}, prompts: {prompts_dir})"
        )
        return 0

    # Rollen-Prompts einlesen (Preflight hat bereits gecheckt, dass sie existieren).
    role_prompts = load_role_prompts(prompts_dir)

    bus = EventBus()
    bus.subscribe(make_console_subscriber(args.stream_mode))
    bus.subscribe(make_jsonl_subscriber(output_dir / "events.jsonl"))

    # Beide Codex-Runner teilen sich dasselbe code/-Verzeichnis, damit der Tester
    # die Implementierung lesen und Tests daneben anlegen kann.
    code_dir = output_dir / "code"
    dev_runner = CodexRunner(
        bus=bus,
        run_id=run_id,
        raw_dir=output_dir / "raw" / "developer",
        timeout=args.timeout,
        base_cmd=codex_cmd,
        work_dir=code_dir,
        node_label="codex_developer",
        model=args.codex_model,
    )
    test_runner = CodexRunner(
        bus=bus,
        run_id=run_id,
        raw_dir=output_dir / "raw" / "tester",
        timeout=args.timeout,
        base_cmd=codex_cmd,
        work_dir=code_dir,
        node_label="codex_tester",
        model=args.codex_model,
    )

    llm = ChatOpenAI(model=args.openai_model, temperature=0.2)

    RUNTIME = Runtime(
        bus=bus,
        dev_runner=dev_runner,
        test_runner=test_runner,
        llm=llm,
        output_dir=output_dir,
        role_prompts=role_prompts,
    )

    request = load_request(args)
    bus.emit(
        "run_start",
        node="orchestrator",
        message=(
            f"start run mit output={output_dir}, parallel={args.max_parallel_jobs}, "
            f"llm_model={args.openai_model}, codex_model={args.codex_model}, "
            f"prompts={prompts_dir}"
        ),
        run_id=run_id,
    )

    initial: OrchestratorState = {
        "run_id": run_id,
        "user_request": request,
        "output_dir": str(output_dir),
        "max_parallel_jobs": args.max_parallel_jobs,
        "work_items": [],
        "dev_artifacts": [],
        "test_artifacts": [],
        "review_report": "",
        "review_status": "unknown",
        "review_iteration": 0,
        "review_feedback": "",
        "final_report": "",
        "errors": [],
    }

    graph = build_graph()
    try:
        result = graph.invoke(initial)
    except Exception as exc:  # noqa: BLE001
        bus.emit(
            "error",
            node="orchestrator",
            message=f"Graph crashed: {exc}",
            run_id=run_id,
        )
        return 1

    bus.emit(
        "run_end",
        node="orchestrator",
        message=(
            f"fertig. dev_artefakte={len(result.get('dev_artifacts', []))} "
            f"test_artefakte={len(result.get('test_artifacts', []))} "
            f"verdict={result.get('review_status','unknown')} "
            f"iterations={result.get('review_iteration',0)} "
            f"fehler={len(result.get('errors', []))}"
        ),
        run_id=run_id,
    )

    print(f"\n{C.BOLD}{C.GREEN}Ergebnisse:{C.RESET} {output_dir}")
    print("  - requirements.md      <- Product Owner")
    print("  - architecture.md      <- Architect")
    print("  - artifacts/developer/ <- Codex Developer")
    print("  - artifacts/tester/    <- Codex Tester")
    print("  - review.md            <- Reviewer (Pass/Fail)")
    print("  - summary.md           <- Final Report")
    print("  - events.jsonl")
    print("  - raw/")
    print("  - code/                <- vollstaendige App (Backend + Frontend + Tests)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
