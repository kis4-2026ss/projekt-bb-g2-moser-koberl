import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 1. API-Key und Umgebung einrichten
# Ersetze 'dein-api-key-hier' mit deinem echten OpenAI API-Key
os.environ["OPENAI_API_KEY"] = "dein-api-key-hier"

# Wir nutzen gpt-4o für logisch anspruchsvolle Aufgaben.
# Eine niedrige Temperature (0.2) sorgt für deterministischere, sauberere Code-Generierung.
llm = ChatOpenAI(model="gpt-4o", temperature=0.2)

# Die gemeinsame Aufgabenstellung für beide Ansätze
anforderung_text = (
    "Erstelle eine Python-Klasse `Warenkorb` für eine E-Commerce-Seite. "
    "Funktionen:\n"
    "- Produkte hinzufügen (Parameter: name, preis, menge, kategorie).\n"
    "- Standard-Versandkosten betragen 5€. Ab einem Gesamtwert von 50€ ist der Versand kostenlos.\n"
    "- Unterstütze zwei Rabattcodes:\n"
    "  1. 'PROMO10': Zieht 10% vom Gesamtwert der Produkte ab.\n"
    "  2. 'VERSANDFREI': Setzt die Versandkosten auf 0€.\n"
    "- Methode `berechne_endpreis()`: Berechnet den finalen Zahlbetrag inklusive Rabatten und Versand."
)

print("=====================================================================")
# =====================================================================
# ANSATZ 1: Single-Agent (Kontrollgruppe)
# =====================================================================
print("--- Starte Ansatz 1: Single-Agent ---")

single_prompt = ChatPromptTemplate.from_template(
    "Du bist ein Softwareentwickler. Löse die folgende Aufgabe komplett in einem Rutsch.\n\n"
    "Aufgabe:\n{anforderung}\n\n"
    "Schreibe zuerst die Python-Klasse. Schreibe direkt danach umfassende Unit-Tests (unter Verwendung von `unittest`), "
    "die auch Edge Cases (z.B. exakt 50€ Einkaufswert, negative Mengen, Reihenfolge von Rabatt und Versandkosten) prüfen. "
    "Gib nur den fertigen Code und die Tests aus, ohne zusätzliche Erklärungen."
)

single_chain = single_prompt | llm | StrOutputParser()
ergebnis_single = single_chain.invoke({"anforderung": anforderung_text})

print("[Single-Agent] Durchlauf beendet.")


print("=====================================================================")
# =====================================================================
# ANSATZ 2: Multi-Agenten-System mit LangChain (LCEL)
# =====================================================================
print("--- Starte Ansatz 2: Multi-Agenten-System (LangChain) ---")

# Agent A: Der reine Programmierer (schreibt nur den Code)
dev_prompt = ChatPromptTemplate.from_template(
    "Du bist ein Softwareentwickler. Löse die folgende Aufgabe und schreibe die Python-Klasse.\n\n"
    "Aufgabe:\n{anforderung}\n\n"
    "Gib NUR den reinen Python-Code der Klasse aus. Keine Unit-Tests, keine Markdown-Erklärungen, kein Smalltalk."
)
dev_chain = dev_prompt | llm | StrOutputParser()

# Agent B: Der QA-Experte / Reviewer (prüft, korrigiert und testet)
tester_prompt = ChatPromptTemplate.from_template(
    "Du bist ein QA- und Code-Review-Experte. Hier ist der Code, den ein Kollege für folgende "
    "Anforderung geschrieben hat:\n"
    "Anforderung:\n{anforderung}\n\n"
    "Code des Kollegen:\n{code_von_dev}\n\n"
    "Schritt 1: Prüfe den Code intensiv auf logische Fehler und Edge Cases (z.B. exakt 49.99€ vs 50€, negative Mengen, "
    "ob der 10%-Rabatt fälschlicherweise auch auf die Versandkosten angewendet wird, oder ob der Versand trotz Rabatt "
    "unter 50€ kostenlos bleibt).\n"
    "Schritt 2: Falls du Fehler findest, korrigiere den Code der Klasse.\n"
    "Schritt 3: Schreibe umfassende Unit-Tests mit Pythons `unittest`-Modul für die (korrigierte) Klasse.\n\n"
    "Gib das Ergebnis übersichtlich aus: Zuerst eine kurze Liste gefundener/korrigierter Fehler (falls vorhanden), "
    "dann die finale Klasse und direkt danach die Unit-Tests."
)
tester_chain = tester_prompt | llm | StrOutputParser()

# Ausführung der Pipeline
print("[Multi-Agent] Dev-Agent generiert Code-Entwurf...")
code_entwurf = dev_chain.invoke({"anforderung": anforderung_text})

print("[Multi-Agent] Tester-Agent führt Review durch und schreibt Unit-Tests...")
ergebnis_multi = tester_chain.invoke({
    "anforderung": anforderung_text,
    "code_von_dev": code_entwurf
})

print("[Multi-Agenten-System] Durchlauf beendet.")


# =====================================================================
# AUSGABE DER ERGEBNISSE FÜR DEINE EVALUATION
# =====================================================================
print("\n=====================================================================")
print("=== EXPERIMENT-AUSWERTUNG ===")
print("=====================================================================\n")

print("👉 ERGEBNIS ANSATZ 1 (SINGLE-AGENT):")
print("-" * 40)
print(ergebnis_single)

print("\n" + "="*60 + "\n")

print("👉 ERGEBNIS ANSATZ 2 (MULTI-AGENTEN-SYSTEM):")
print("-" * 40)
print(ergebnis_multi)