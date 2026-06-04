#!/usr/bin/env python3
"""Genera i notebook didattici (versione studente in content/ e versione
soluzione in solutions/) a partire da un'unica definizione di ogni esercizio.

Ogni esercizio e' definito UNA volta: enunciato + soluzione + test. Lo script
produce automaticamente le due versioni allineate, cosi' non possono divergere.

Uso:
    uv run python tools/build_notebooks.py
"""

import os
import base64
import nbformat as nbf
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell

# Cartelle di destinazione (relative alla radice del repository).
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT_DIR = os.path.join(ROOT, "content")
SOLUTIONS_DIR = os.path.join(ROOT, "solutions")
BRANDING_DIR = os.path.join(ROOT, "branding")

# Colori del brand Open Innova.
BRAND_NAVY = "#19213c"
BRAND_GREEN = "#6bb889"

STUDENT_BODY = "    pass  # <- scrivi qui la tua soluzione"

KERNEL_META = {
    "kernelspec": {"name": "python", "display_name": "Python (Pyodide)", "language": "python"},
    "language_info": {"name": "python"},
}


# --- Costruttori di blocchi --------------------------------------------------

def md(text):
    """Cella di markdown (uguale per studente e soluzione)."""
    return {"kind": "md", "text": text}


def code(lines):
    """Cella di codice senza test, uguale per studente e soluzione.

    Usata per esempi eseguibili e per la cella 'indovina cosa stampa'.
    """
    return {"kind": "code", "src": "\n".join(lines)}


def divider(n, titolo, sfida=False):
    etichetta = f"[SFIDA] ESERCIZIO {n}" if sfida else f"ESERCIZIO {n}"
    base = f"# == {etichetta}: {titolo} "
    return base + "=" * max(4, 64 - len(base))


def test_block(asserts):
    """Blocco try/except identico in tutti gli esercizi."""
    lines = ["", "# [TEST] (non modificare)", "try:"]
    lines += ["    " + a for a in asserts]
    lines += [
        '    print("[OK] Corretto!")',
        "except AssertionError as e:",
        '    print(f"[X] Test fallito: {e}")',
        "except Exception as e:",
        '    print(f"[!] Errore nel codice: {type(e).__name__}: {e}")',
    ]
    return lines


def ex(n, titolo, enunciato, sol, test, stu=None, sfida=False):
    """Esercizio con verifica automatica.

    n          numero dell'esercizio
    titolo     titolo breve (compare nell'intestazione)
    enunciato  lista di righe di commento (senza il '# ' iniziale)
    sol        righe di codice della SOLUZIONE (def/class completa)
    test       righe 'assert ...' (senza indentazione)
    stu        versione studente; se assente, derivata sostituendo il corpo
               con `pass` (vale per le funzioni a una sola def)
    sfida      True per gli esercizi [SFIDA]
    """
    if stu is None:
        stu = [sol[0], STUDENT_BODY]
    header = [divider(n, titolo, sfida)] + ["# " + r for r in enunciato]
    return {"kind": "ex", "header": header, "sol": sol, "stu": stu, "test": test}


# --- Costruzione dei notebook ------------------------------------------------

# Metadati che fanno apparire la cella con l'input "collassato" (input nascosto)
# nell'interfaccia JupyterLab/JupyterLite: la cella si esegue e mostra l'output,
# ma il codice del test resta fuori dalla vista normale dello studente.
HIDDEN_META = {"jupyter": {"source_hidden": True}}


def _func_source(item, use_solution):
    """Cella VISIBILE con l'enunciato e la funzione/classe da completare."""
    body = item["sol"] if use_solution else item["stu"]
    return "\n".join(item["header"] + [""] + body)


def _test_source(item):
    """Cella col solo blocco di test (senza la riga vuota iniziale)."""
    return "\n".join(test_block(item["test"])).lstrip("\n")


def _cells_for(block, use_solution):
    """Restituisce la lista di celle per un blocco.

    Un esercizio genera DUE celle: la funzione (visibile) e il test. Nella
    versione studente la cella del test e' collassata (source_hidden); nella
    versione soluzione resta visibile, cosi' il docente legge i casi testati.
    """
    if block["kind"] == "md":
        return [new_markdown_cell(block["text"])]
    if block["kind"] == "code":
        return [new_code_cell(block["src"])]
    func_cell = new_code_cell(_func_source(block, use_solution))
    metadata = {} if use_solution else dict(HIDDEN_META)
    test_cell = new_code_cell(_test_source(block), metadata=metadata)
    return [func_cell, test_cell]


CREDITO = md(
    "---\n"
    "*Materiale a cura di Open Innova S.R.L. (openinnova.it), distribuito con "
    "licenza Creative Commons Attribuzione 4.0 Internazionale (CC BY 4.0). "
    "Riusabile e modificabile citando la fonte.*"
)


def brand_banner():
    """Banner brandizzato Open Innova (cella markdown) inserito in cima a ogni
    notebook. Il logo bianco viene incorporato come data-URI (resa isolata,
    robusta rispetto al sanitizer del markdown). Se l'immagine non venisse resa,
    restano comunque sfondo navy + testo via attributi `style`."""
    with open(os.path.join(BRANDING_DIR, "logo-white.svg"), "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    logo = f'data:image/svg+xml;base64,{b64}'
    html = (
        f'<div style="background:{BRAND_NAVY};border-left:6px solid {BRAND_GREEN};'
        'border-radius:8px;padding:16px 20px;display:flex;align-items:center;'
        'gap:18px;color:#ffffff;font-family:sans-serif;">'
        f'<img src="{logo}" alt="Open Innova" style="height:48px;width:auto;" />'
        '<div>'
        f'<div style="font-size:1.35em;font-weight:700;color:#ffffff;">Bootcamp Python</div>'
        f'<div style="font-size:0.95em;color:{BRAND_GREEN};">Open Innova &middot; impara a programmare nel browser</div>'
        '</div></div>'
    )
    return md(html)


BANNER = brand_banner()


def write_pair(slug, blocks):
    blocks = [BANNER] + list(blocks) + [CREDITO]
    for use_solution, folder, suffix in [
        (False, CONTENT_DIR, ""),
        (True, SOLUTIONS_DIR, "_SOL"),
    ]:
        cells = []
        for b in blocks:
            cells.extend(_cells_for(b, use_solution))
        nb = new_notebook(cells=cells)
        nb.metadata = KERNEL_META
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, f"{slug}{suffix}.ipynb")
        with open(path, "w", encoding="utf-8") as f:
            nbf.write(nb, f)
    print(f"  generato: content/{slug}.ipynb  e  solutions/{slug}_SOL.ipynb")


# ===========================================================================
#  NOTEBOOK 1 -- Strutture dati e cicli
# ===========================================================================

NB1 = [
    md(
        "# Giorno 1 - Strutture dati e cicli\n"
        "\n"
        "Benvenuto nel primo notebook. Qui prendi confidenza con la **sintassi di "
        "Python** usando concetti che gia' conosci da C e Java: condizioni, cicli e "
        "strutture dati.\n"
        "\n"
        "**Cosa imparerai:**\n"
        "- `if` / `elif` / `else`, cicli `for` e `while`, `break` e `continue`\n"
        "- lo *scope* (visibilita') delle variabili\n"
        "- le strutture dati di Python: **tuple**, **liste**, **dizionari**\n"
        "- le **list comprehension** (una scorciatoia molto pythonica)\n"
        "\n"
        "**Durata:** circa 2-3 ore. Esegui ogni cella con **Shift + Invio** e leggi il "
        "messaggio del test: `[OK]` = corretto, `[X]` = risultato sbagliato, `[!]` = "
        "errore nel codice.\n"
        "\n"
        "> **Se vieni da C/Java:** in Python i blocchi NON usano le parentesi graffe "
        "`{ }`: contano **l'indentazione** (gli spazi a inizio riga) e i due punti `:`. "
        "Non servono il `;` a fine riga ne' dichiarare il tipo delle variabili."
    ),
    md(
        "## Condizioni: `if` / `elif` / `else`\n"
        "\n"
        "```python\n"
        "voto = 7\n"
        "if voto >= 6:\n"
        "    print(\"promosso\")\n"
        "elif voto == 5:\n"
        "    print(\"recupero\")\n"
        "else:\n"
        "    print(\"bocciato\")\n"
        "```\n"
        "\n"
        "L'operatore `%` (modulo) da' il resto della divisione: `10 % 3` vale `1`. "
        "Un numero e' pari se `n % 2 == 0`."
    ),
    ex(
        1, "pari o dispari",
        ["Restituisci la stringa \"pari\" o \"dispari\" a seconda del numero n.",
         "Esempio: pari_o_dispari(4) -> \"pari\""],
        ["def pari_o_dispari(n):",
         "    if n % 2 == 0:",
         "        return \"pari\"",
         "    else:",
         "        return \"dispari\""],
        ['assert pari_o_dispari(4) == "pari", "numero pari"',
         'assert pari_o_dispari(7) == "dispari", "numero dispari"',
         'assert pari_o_dispari(0) == "pari", "lo zero e\' pari"',
         'assert pari_o_dispari(-3) == "dispari", "numero negativo"'],
    ),
    ex(
        2, "il massimo di tre",
        ["Restituisci il maggiore tra a, b e c.",
         "Vincolo: NON usare la funzione max(), ma if/elif/else.",
         "Esempio: massimo(1, 8, 3) -> 8"],
        ["def massimo(a, b, c):",
         "    if a >= b and a >= c:",
         "        return a",
         "    elif b >= a and b >= c:",
         "        return b",
         "    else:",
         "        return c"],
        ['assert massimo(1, 2, 3) == 3, "il maggiore e\' l\'ultimo"',
         'assert massimo(9, 2, 3) == 9, "il maggiore e\' il primo"',
         'assert massimo(1, 8, 3) == 8, "il maggiore e\' quello centrale"',
         'assert massimo(5, 5, 5) == 5, "tutti uguali"'],
    ),
    md(
        "## Cicli: `for` e `range`\n"
        "\n"
        "`range(1, 11)` genera i numeri da 1 a 10 (l'estremo destro e' escluso). "
        "Per costruire una lista si parte da una lista vuota e si usa `.append()`:\n"
        "\n"
        "```python\n"
        "quadrati = []\n"
        "for i in range(1, 6):\n"
        "    quadrati.append(i * i)\n"
        "# quadrati == [1, 4, 9, 16, 25]\n"
        "```\n"
        "\n"
        "> **Se vieni da C/Java:** una lista Python e' come un `ArrayList`/array dinamico: "
        "cresce da sola con `.append()`, non devi dichiararne la dimensione."
    ),
    ex(
        3, "la tabellina",
        ["Restituisci la lista [n, 2n, 3n, ..., 10n].",
         "Esempio: tabellina(3) -> [3, 6, 9, 12, 15, 18, 21, 24, 27, 30]"],
        ["def tabellina(n):",
         "    risultato = []",
         "    for i in range(1, 11):",
         "        risultato.append(n * i)",
         "    return risultato"],
        ['assert tabellina(1) == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], "tabellina dell\'1"',
         'assert tabellina(5) == [5, 10, 15, 20, 25, 30, 35, 40, 45, 50], "tabellina del 5"',
         'assert tabellina(0) == [0, 0, 0, 0, 0, 0, 0, 0, 0, 0], "tabellina dello 0"',
         'assert len(tabellina(7)) == 10, "ci sono dieci elementi"'],
    ),
    ex(
        4, "FizzBuzz",
        ["Restituisci la lista dei numeri da 1 a n, ma sostituisci:",
         "- i multipli di 3 con \"Fizz\"",
         "- i multipli di 5 con \"Buzz\"",
         "- i multipli di 15 con \"FizzBuzz\"",
         "Esempio: fizzbuzz(5) -> [1, 2, \"Fizz\", 4, \"Buzz\"]"],
        ["def fizzbuzz(n):",
         "    risultato = []",
         "    for i in range(1, n + 1):",
         "        if i % 15 == 0:",
         "            risultato.append(\"FizzBuzz\")",
         "        elif i % 3 == 0:",
         "            risultato.append(\"Fizz\")",
         "        elif i % 5 == 0:",
         "            risultato.append(\"Buzz\")",
         "        else:",
         "            risultato.append(i)",
         "    return risultato"],
        ['assert fizzbuzz(5) == [1, 2, "Fizz", 4, "Buzz"], "fino a 5"',
         'assert fizzbuzz(15)[-1] == "FizzBuzz", "il 15 diventa FizzBuzz"',
         'assert fizzbuzz(3) == [1, 2, "Fizz"], "il 3 diventa Fizz"',
         'assert fizzbuzz(1) == [1], "solo il numero 1"'],
    ),
    md(
        "## Iterare e contare\n"
        "\n"
        "Si puo' ciclare direttamente sui caratteri di una stringa o sugli elementi di "
        "una lista. Il metodo `.lower()` rende tutto minuscolo (utile per confronti che "
        "non distinguono maiuscole/minuscole). L'operatore `in` controlla l'appartenenza:\n"
        "\n"
        "```python\n"
        "for c in \"Casa\".lower():\n"
        "    if c in \"aeiou\":\n"
        "        print(c)   # stampa a, a\n"
        "```"
    ),
    ex(
        5, "conta le vocali",
        ["Conta quante vocali (a, e, i, o, u) ci sono nel testo.",
         "Non distinguere maiuscole e minuscole.",
         "Esempio: conta_vocali(\"Casa\") -> 2"],
        ["def conta_vocali(testo):",
         "    vocali = \"aeiou\"",
         "    conta = 0",
         "    for carattere in testo.lower():",
         "        if carattere in vocali:",
         "            conta += 1",
         "    return conta"],
        ['assert conta_vocali("casa") == 2, "parola semplice"',
         'assert conta_vocali("ciao") == 3, "tre vocali di fila"',
         'assert conta_vocali("AEIOU") == 5, "tutte maiuscole"',
         'assert conta_vocali("xyz") == 0, "nessuna vocale"',
         'assert conta_vocali("") == 0, "stringa vuota"'],
    ),
    ex(
        6, "inverti la lista",
        ["Restituisci la lista al contrario.",
         "Vincolo: NON usare .reverse() ne' lo slicing [::-1]; usa un ciclo.",
         "Esempio: inverti([1, 2, 3]) -> [3, 2, 1]"],
        ["def inverti(lista):",
         "    risultato = []",
         "    for elemento in lista:",
         "        risultato.insert(0, elemento)",
         "    return risultato"],
        ['assert inverti([1, 2, 3]) == [3, 2, 1], "tre elementi"',
         'assert inverti([]) == [], "lista vuota"',
         'assert inverti([42]) == [42], "un solo elemento"',
         'assert inverti(["a", "b"]) == ["b", "a"], "stringhe"'],
    ),
    ex(
        7, "somma dei pari",
        ["Somma solo gli elementi pari della lista di numeri.",
         "Esempio: somma_pari([1, 2, 3, 4]) -> 6"],
        ["def somma_pari(numeri):",
         "    totale = 0",
         "    for n in numeri:",
         "        if n % 2 == 0:",
         "            totale += n",
         "    return totale"],
        ['assert somma_pari([1, 2, 3, 4]) == 6, "numeri misti"',
         'assert somma_pari([1, 3, 5]) == 0, "nessun pari"',
         'assert somma_pari([]) == 0, "lista vuota"',
         'assert somma_pari([2, 4, 6]) == 12, "tutti pari"'],
    ),
    md(
        "## Dizionari\n"
        "\n"
        "Un dizionario associa **chiavi** a **valori**: `{\"Anna\": 8, \"Luca\": 6}`. "
        "Si scorre con `.items()`, che restituisce coppie (chiave, valore):\n"
        "\n"
        "```python\n"
        "voti = {\"Anna\": 8, \"Luca\": 6}\n"
        "for nome, voto in voti.items():\n"
        "    print(nome, voto)\n"
        "```\n"
        "\n"
        "> **Se vieni da Java:** il dizionario e' l'equivalente di una `HashMap`. "
        "L'operatore `in` (`chiave in d`) dice se una chiave esiste gia'."
    ),
    ex(
        8, "inverti il dizionario",
        ["Da {chiave: valore} produci {valore: chiave}.",
         "Esempio: inverti_dizionario({\"a\": 1, \"b\": 2}) -> {1: \"a\", 2: \"b\"}"],
        ["def inverti_dizionario(d):",
         "    risultato = {}",
         "    for chiave, valore in d.items():",
         "        risultato[valore] = chiave",
         "    return risultato"],
        ['assert inverti_dizionario({"a": 1, "b": 2}) == {1: "a", 2: "b"}, "caso base"',
         'assert inverti_dizionario({}) == {}, "dizionario vuoto"',
         'assert inverti_dizionario({"x": 10}) == {10: "x"}, "un solo elemento"'],
    ),
    ex(
        9, "conta le occorrenze",
        ["Restituisci un dizionario {elemento: numero_di_volte}.",
         "Esempio: conta_occorrenze([\"a\", \"b\", \"a\"]) -> {\"a\": 2, \"b\": 1}"],
        ["def conta_occorrenze(lista):",
         "    risultato = {}",
         "    for elemento in lista:",
         "        if elemento in risultato:",
         "            risultato[elemento] += 1",
         "        else:",
         "            risultato[elemento] = 1",
         "    return risultato"],
        ['assert conta_occorrenze(["a", "b", "a"]) == {"a": 2, "b": 1}, "lettere ripetute"',
         'assert conta_occorrenze([]) == {}, "lista vuota"',
         'assert conta_occorrenze([1, 1, 1]) == {1: 3}, "stesso elemento"'],
    ),
    md(
        "## List comprehension e l'esercizio [SFIDA]\n"
        "\n"
        "La **list comprehension** e' un modo compatto di costruire una lista in una riga:\n"
        "\n"
        "```python\n"
        "pari = [n for n in range(10) if n % 2 == 0]   # [0, 2, 4, 6, 8]\n"
        "```\n"
        "\n"
        "Una **tupla** e' come una lista ma immutabile (non si modifica): `(3, 4)`. "
        "Si usa spesso per coppie di valori, come le coordinate di un punto.\n"
        "\n"
        "La **distanza dall'origine** del punto (x, y) e' la radice di x^2 + y^2 "
        "(in Python: `(x ** 2 + y ** 2) ** 0.5`)."
    ),
    ex(
        10, "il punto piu' vicino all'origine",
        ["Ricevi una lista di tuple (x, y) e restituisci la tupla con la distanza",
         "euclidea minima dall'origine (0, 0).",
         "Esempio: punto_piu_vicino([(1, 1), (5, 5), (0, 1)]) -> (0, 1)"],
        ["def punto_piu_vicino(punti):",
         "    migliore = None",
         "    distanza_migliore = None",
         "    for x, y in punti:",
         "        distanza = (x ** 2 + y ** 2) ** 0.5",
         "        if distanza_migliore is None or distanza < distanza_migliore:",
         "            distanza_migliore = distanza",
         "            migliore = (x, y)",
         "    return migliore"],
        ['assert punto_piu_vicino([(1, 1), (5, 5), (0, 1)]) == (0, 1), "il piu\' vicino"',
         'assert punto_piu_vicino([(3, 4)]) == (3, 4), "un solo punto"',
         'assert punto_piu_vicino([(2, 0), (0, 3)]) == (2, 0), "punti sugli assi"'],
        sfida=True,
    ),
    md(
        "## Bonus: lo *scope* delle variabili - indovina cosa stampa\n"
        "\n"
        "Leggi con attenzione il codice della cella qui sotto. **Prima di eseguirlo**, "
        "prova a indovinare: cosa stamperanno le due `print`?\n"
        "\n"
        "Scrivi qui la tua previsione (doppio clic per modificare questa cella):\n"
        "\n"
        "- Prima riga, penso stampi: `...`\n"
        "- Seconda riga, penso stampi: `...`\n"
        "\n"
        "Poi esegui la cella sotto e confronta."
    ),
    code([
        "contatore = 10",
        "",
        "def prova():",
        "    contatore = 99   # assegnare qui crea una NUOVA variabile locale?",
        "    return contatore",
        "",
        "print(prova())      # cosa stampa?",
        "print(contatore)    # e questa?",
    ]),
    md(
        "### La spiegazione\n"
        "\n"
        "Stampa **99** e poi **10**.\n"
        "\n"
        "Dentro `prova()`, l'assegnamento `contatore = 99` crea una variabile **locale** "
        "alla funzione, che esiste solo li' dentro: per questo `prova()` restituisce 99. "
        "La variabile **globale** `contatore`, fuori dalla funzione, resta 10: la funzione "
        "non l'ha toccata.\n"
        "\n"
        "Per modificare davvero la variabile globale servirebbe la parola chiave `global` "
        "(`global contatore`), ma di solito e' meglio **evitare** le variabili globali e "
        "far restituire il valore alla funzione, come negli esercizi precedenti.\n"
        "\n"
        "> **Se vieni da C/Java:** in Python basta un assegnamento dentro la funzione per "
        "creare una variabile locale che \"nasconde\" quella esterna con lo stesso nome."
    ),
]


# ===========================================================================
#  NOTEBOOK 2 -- Funzioni e librerie built-in
# ===========================================================================

NB2 = [
    md(
        "# Giorno 2 - Funzioni e librerie\n"
        "\n"
        "Oggi approfondisci le **funzioni** (parametri di default, numero variabile di "
        "argomenti, ricorsione) e usi alcune **librerie della libreria standard** di "
        "Python: `math`, `random` e `json`. Sono gli stessi strumenti che useremo per "
        "costruire il nostro assistente virtuale.\n"
        "\n"
        "**Cosa imparerai:**\n"
        "- definire funzioni con parametri di **default** e con `*args`\n"
        "- la **ricorsione** (una funzione che chiama se stessa)\n"
        "- i moduli `math` (matematica), `random` (numeri casuali), `json` (dati)\n"
        "\n"
        "**Durata:** circa 2-3 ore.\n"
        "\n"
        "> **Se vieni da C/Java:** una funzione Python si definisce con `def` e non "
        "dichiara il tipo di ritorno. Se non scrivi `return`, la funzione restituisce "
        "automaticamente `None` (l'equivalente di `null`).\n"
        "\n"
        "**Nota su `os` e `sys`:** in JupyterLite Python gira nel browser e il file "
        "system e' \"finto\". Quindi NON leggiamo/scriviamo file reali. Possiamo pero' "
        "leggere qualche informazione, come mostra la cella qui sotto. Eseguila pure."
    ),
    code([
        "import sys",
        "",
        "print(\"Versione di Python:\", sys.version)",
        "print(\"Piattaforma:\", sys.platform)",
    ]),
    md(
        "Per usare una libreria la si **importa** una volta sola. Esegui questa cella "
        "prima degli esercizi: rende disponibili `math`, `random` e `json` in tutto il "
        "notebook."
    ),
    code([
        "import math",
        "import random",
        "import json",
    ]),
    md(
        "## Funzioni con piu' rami e valori di ritorno\n"
        "\n"
        "Una funzione puo' restituire valori diversi a seconda dell'input. Ricorda che "
        "`return` interrompe subito la funzione.\n"
        "\n"
        "```python\n"
        "def segno(n):\n"
        "    if n > 0:\n"
        "        return \"positivo\"\n"
        "    elif n < 0:\n"
        "        return \"negativo\"\n"
        "    return \"zero\"\n"
        "```"
    ),
    ex(
        1, "la calcolatrice",
        ["Ricevi due numeri e un'operazione tra \"+\", \"-\", \"*\", \"/\".",
         "Restituisci il risultato. Se si divide per zero, restituisci None.",
         "Esempio: calcola(8, 2, \"/\") -> 4.0"],
        ["def calcola(a, b, operazione):",
         "    if operazione == \"+\":",
         "        return a + b",
         "    elif operazione == \"-\":",
         "        return a - b",
         "    elif operazione == \"*\":",
         "        return a * b",
         "    elif operazione == \"/\":",
         "        if b == 0:",
         "            return None",
         "        return a / b"],
        ['assert calcola(2, 3, "+") == 5, "somma"',
         'assert calcola(10, 4, "-") == 6, "differenza"',
         'assert calcola(3, 5, "*") == 15, "prodotto"',
         'assert calcola(8, 2, "/") == 4, "divisione"',
         'assert calcola(5, 0, "/") is None, "divisione per zero -> None"'],
    ),
    md(
        "## Parametri di default\n"
        "\n"
        "Un parametro puo' avere un **valore predefinito**: se chi chiama non lo passa, "
        "viene usato quello.\n"
        "\n"
        "```python\n"
        "def potenza(base, esponente=2):\n"
        "    return base ** esponente\n"
        "potenza(5)      # 25 (esponente vale 2)\n"
        "potenza(5, 3)   # 125\n"
        "```\n"
        "\n"
        "> **Se vieni da Java:** ti risparmiano le tante versioni *overloaded* dello "
        "stesso metodo: un solo `def` con valori di default."
    ),
    ex(
        2, "saluta in piu' lingue",
        ["Restituisci un saluto. La lingua di default e' l'italiano (\"it\");",
         "supporta anche inglese (\"en\") e spagnolo (\"es\").",
         "Esempio: saluta(\"Anna\") -> \"Ciao, Anna!\"",
         "Esempio: saluta(\"Anna\", \"en\") -> \"Hello, Anna!\""],
        ["def saluta(nome, lingua=\"it\"):",
         "    if lingua == \"en\":",
         "        return f\"Hello, {nome}!\"",
         "    elif lingua == \"es\":",
         "        return f\"Hola, {nome}!\"",
         "    else:",
         "        return f\"Ciao, {nome}!\""],
        ['assert saluta("Anna") == "Ciao, Anna!", "default italiano"',
         'assert saluta("Anna", "it") == "Ciao, Anna!", "italiano esplicito"',
         'assert saluta("Anna", "en") == "Hello, Anna!", "inglese"',
         'assert saluta("Anna", "es") == "Hola, Anna!", "spagnolo"'],
    ),
    md(
        "## Il modulo `math`\n"
        "\n"
        "`math.sqrt(x)` calcola la radice quadrata, `math.pi` e' il valore di greco pi. "
        "Per confrontare numeri con la virgola si evita `==` (per via dei minimi errori "
        "di arrotondamento) e si controlla che la differenza sia piccolissima:\n"
        "\n"
        "```python\n"
        "abs(math.sqrt(2) - 1.41421356) < 1e-6\n"
        "```"
    ),
    ex(
        3, "distanza tra due punti",
        ["Calcola la distanza euclidea tra due punti p1 e p2, dati come tuple (x, y).",
         "Usa math.sqrt.",
         "Esempio: distanza((0, 0), (3, 4)) -> 5.0"],
        ["def distanza(p1, p2):",
         "    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)"],
        ['assert distanza((0, 0), (3, 4)) == 5.0, "triangolo 3-4-5"',
         'assert distanza((0, 0), (0, 0)) == 0.0, "stesso punto"',
         'assert distanza((1, 1), (1, 1)) == 0.0, "punti coincidenti"',
         'assert abs(distanza((0, 0), (1, 1)) - 2 ** 0.5) < 1e-9, "diagonale del quadrato"'],
    ),
    ex(
        4, "area del cerchio",
        ["Calcola l'area di un cerchio dato il raggio. Usa math.pi.",
         "Esempio: area_cerchio(1) -> 3.1415..."],
        ["def area_cerchio(raggio):",
         "    return math.pi * raggio ** 2"],
        ['assert abs(area_cerchio(1) - math.pi) < 1e-9, "raggio 1"',
         'assert area_cerchio(0) == 0, "raggio 0"',
         'assert abs(area_cerchio(2) - 4 * math.pi) < 1e-9, "raggio 2"'],
    ),
    md(
        "## Il modulo `random`\n"
        "\n"
        "`random.randint(1, 6)` restituisce un intero casuale tra 1 e 6 (estremi "
        "inclusi). I numeri sono \"pseudo-casuali\": fissando il **seme** con "
        "`random.seed(42)` la sequenza diventa **ripetibile** (utile per i test).\n"
        "\n"
        "Suggerimento per l'esercizio: parti da un dizionario con tutte le sei facce a "
        "zero, `{1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}`, poi incrementa."
    ),
    ex(
        5, "simula i lanci di un dado",
        ["Simula n lanci di un dado a 6 facce con random.randint.",
         "Restituisci un dizionario {1: ..., 2: ..., ..., 6: ...} con i conteggi.",
         "Esempio: lanci_dado(100) -> {1: 18, 2: 15, ...} (i numeri variano)"],
        ["def lanci_dado(n):",
         "    conteggi = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}",
         "    for _ in range(n):",
         "        faccia = random.randint(1, 6)",
         "        conteggi[faccia] += 1",
         "    return conteggi"],
        ['random.seed(42)',
         'r1 = lanci_dado(600)',
         'random.seed(42)',
         'r2 = lanci_dado(600)',
         'assert r1 == r2, "con lo stesso seme i risultati sono identici"',
         'assert sum(r1.values()) == 600, "in totale 600 lanci"',
         'assert sorted(r1.keys()) == [1, 2, 3, 4, 5, 6], "ci sono tutte le sei facce"',
         'assert all(c > 0 for c in r1.values()), "ogni faccia esce almeno una volta"'],
    ),
    md(
        "## Il modulo `json`\n"
        "\n"
        "JSON e' un formato di testo per scambiare dati (lo useremo per la knowledge "
        "base dell'assistente). `json.loads` trasforma una **stringa JSON** in oggetti "
        "Python (dizionari, liste); `json.dumps` fa il contrario.\n"
        "\n"
        "```python\n"
        "d = json.loads('{\"nome\": \"Anna\", \"eta\": 17}')\n"
        "d[\"nome\"]   # \"Anna\"\n"
        "json.dumps({\"ok\": True})   # '{\"ok\": true}'\n"
        "```"
    ),
    ex(
        6, "leggi una persona da JSON",
        ["Ricevi una stringa JSON come '{\"nome\": \"Anna\", \"eta\": 17}'.",
         "Restituisci la stringa \"Anna ha 17 anni\". Usa json.loads.",
         "Esempio: parse_persona('{\"nome\": \"Anna\", \"eta\": 17}') -> \"Anna ha 17 anni\""],
        ["def parse_persona(stringa_json):",
         "    dati = json.loads(stringa_json)",
         "    return f\"{dati['nome']} ha {dati['eta']} anni\""],
        ['assert parse_persona(\'{"nome": "Anna", "eta": 17}\') == "Anna ha 17 anni", "caso base"',
         'assert parse_persona(\'{"nome": "Luca", "eta": 16}\') == "Luca ha 16 anni", "altro nome"',
         'assert parse_persona(\'{"nome": "Sara", "eta": 18}\') == "Sara ha 18 anni", "maggiorenne"'],
    ),
    ex(
        7, "costruisci una stringa JSON",
        ["Ricevi una lista di tuple (nome, voto) e costruisci una stringa JSON con la",
         "lista dei dizionari corrispondenti {\"nome\": ..., \"voto\": ...}. Usa json.dumps.",
         "Esempio: costruisci_json([(\"Anna\", 8)]) -> '[{\"nome\": \"Anna\", \"voto\": 8}]'"],
        ["def costruisci_json(lista_studenti):",
         "    studenti = []",
         "    for nome, voto in lista_studenti:",
         "        studenti.append({\"nome\": nome, \"voto\": voto})",
         "    return json.dumps(studenti)"],
        ['assert json.loads(costruisci_json([("Anna", 8)])) == [{"nome": "Anna", "voto": 8}], "un solo studente"',
         'assert json.loads(costruisci_json([("Anna", 8), ("Luca", 6)])) == [{"nome": "Anna", "voto": 8}, {"nome": "Luca", "voto": 6}], "due studenti"',
         'assert json.loads(costruisci_json([])) == [], "lista vuota"',
         'assert isinstance(costruisci_json([]), str), "restituisce una stringa"'],
    ),
    md(
        "## La ricorsione\n"
        "\n"
        "Una funzione **ricorsiva** chiama se stessa su un problema piu' piccolo, fino a "
        "un **caso base** che ferma la catena. Esempio, il fattoriale:\n"
        "`5! = 5 * 4 * 3 * 2 * 1`. Si puo' scrivere come `fattoriale(n) = n * "
        "fattoriale(n - 1)`, con caso base `fattoriale(1) = 1`.\n"
        "\n"
        "> **Se vieni da C/Java:** la ricorsione funziona esattamente come la' che "
        "conosci. Ricorda solo di gestire il caso base, altrimenti la funzione non si "
        "ferma mai."
    ),
    ex(
        8, "fattoriale (ricorsivo)",
        ["Calcola n! in modo ricorsivo. Per definizione 0! = 1.",
         "Esempio: fattoriale(5) -> 120"],
        ["def fattoriale(n):",
         "    if n <= 1:",
         "        return 1",
         "    return n * fattoriale(n - 1)"],
        ['assert fattoriale(0) == 1, "zero fattoriale"',
         'assert fattoriale(1) == 1, "uno fattoriale"',
         'assert fattoriale(5) == 120, "cinque fattoriale"',
         'assert fattoriale(6) == 720, "sei fattoriale"'],
    ),
    ex(
        9, "Fibonacci (ricorsivo)",
        ["Restituisci l'n-esimo numero di Fibonacci, in modo ricorsivo.",
         "La sequenza parte da: fibonacci(0) = 0, fibonacci(1) = 1, poi ogni numero",
         "e' la somma dei due precedenti.",
         "Esempio: fibonacci(7) -> 13"],
        ["def fibonacci(n):",
         "    if n < 2:",
         "        return n",
         "    return fibonacci(n - 1) + fibonacci(n - 2)"],
        ['assert fibonacci(0) == 0, "il primo numero"',
         'assert fibonacci(1) == 1, "il secondo numero"',
         'assert fibonacci(7) == 13, "indice 7"',
         'assert fibonacci(10) == 55, "indice 10"'],
    ),
    md(
        "## Numero variabile di argomenti: l'esercizio [SFIDA]\n"
        "\n"
        "Con `*args` una funzione accetta **quanti argomenti vuoi**, che arrivano come "
        "una tupla:\n"
        "\n"
        "```python\n"
        "def somma_tutti(*numeri):\n"
        "    return sum(numeri)\n"
        "somma_tutti(1, 2, 3)   # 6\n"
        "somma_tutti()          # 0\n"
        "```\n"
        "\n"
        "> **Se vieni da Java:** e' come i *varargs* (`int... numeri`)."
    ),
    ex(
        10, "la media di quanti numeri vuoi",
        ["Calcola la media di un numero variabile di argomenti.",
         "Se chiamata senza argomenti, restituisci 0.",
         "Esempio: media(2, 4) -> 3.0 ; media() -> 0"],
        ["def media(*numeri):",
         "    if len(numeri) == 0:",
         "        return 0",
         "    return sum(numeri) / len(numeri)"],
        ['assert media(10) == 10, "un solo numero"',
         'assert media(2, 4) == 3, "due numeri"',
         'assert media(1, 2, 3, 4) == 2.5, "quattro numeri"',
         'assert media() == 0, "nessun argomento -> 0"'],
        sfida=True,
    ),
]


# ===========================================================================
#  NOTEBOOK 3 -- Classi
# ===========================================================================

NB3 = [
    md(
        "# Giorno 3 - Classi\n"
        "\n"
        "Oggi impari le **classi**: il modo di Python per creare oggetti che uniscono "
        "dati (attributi) e comportamenti (metodi). Gli ultimi esercizi costruiscono i "
        "**mattoni del nostro progetto**: un assistente virtuale che cerca risposte "
        "dentro i tutorial del sito. Li riuserai nei prossimi giorni per il bot Telegram.\n"
        "\n"
        "**Cosa imparerai:**\n"
        "- definire una classe con `__init__`, attributi e metodi\n"
        "- attributi **di classe** vs attributi **di istanza**\n"
        "- `@property`, `@staticmethod`, `@classmethod`\n"
        "- l'**ereditarieta'** (una classe che estende un'altra)\n"
        "\n"
        "**Durata:** circa 2 ore.\n"
        "\n"
        "> **Se vieni da C++/Java:** i concetti sono gli stessi, cambia la sintassi. "
        "Il primo parametro dei metodi e' sempre `self` (l'oggetto stesso, come `this`) "
        "e va scritto esplicitamente. Per creare un oggetto NON si usa `new`: basta "
        "`Punto(3, 4)`. Non esiste `private`: per convenzione un nome con underscore "
        "iniziale (`_celsius`) si considera \"interno\"."
    ),
    md(
        "## La prima classe: `__init__` e metodi\n"
        "\n"
        "`__init__` e' il **costruttore**: viene eseguito quando crei l'oggetto e di "
        "solito salva i dati negli attributi (`self.x = x`). Gli altri metodi usano quei "
        "dati tramite `self`.\n"
        "\n"
        "```python\n"
        "class Cane:\n"
        "    def __init__(self, nome):\n"
        "        self.nome = nome\n"
        "    def abbaia(self):\n"
        "        return f\"{self.nome} dice Bau!\"\n"
        "\n"
        "fido = Cane(\"Fido\")\n"
        "fido.abbaia()   # \"Fido dice Bau!\"\n"
        "```"
    ),
    ex(
        1, "classe Punto",
        ["Crea una classe Punto con attributi x e y e un metodo distanza_da(altro)",
         "che calcola la distanza euclidea da un altro Punto.",
         "Esempio: Punto(0, 0).distanza_da(Punto(3, 4)) -> 5.0"],
        ["class Punto:",
         "    def __init__(self, x, y):",
         "        self.x = x",
         "        self.y = y",
         "",
         "    def distanza_da(self, altro):",
         "        return ((self.x - altro.x) ** 2 + (self.y - altro.y) ** 2) ** 0.5"],
        ['p = Punto(0, 0)',
         'assert p.x == 0 and p.y == 0, "gli attributi x e y sono salvati"',
         'assert Punto(0, 0).distanza_da(Punto(3, 4)) == 5.0, "distanza 3-4-5"',
         'assert Punto(1, 1).distanza_da(Punto(1, 1)) == 0.0, "stesso punto"',
         'assert Punto(0, 0).distanza_da(Punto(0, 5)) == 5.0, "distanza verticale"'],
        stu=["class Punto:",
             "    def __init__(self, x, y):",
             "        pass  # <- salva x e y in self.x e self.y",
             "",
             "    def distanza_da(self, altro):",
             "        pass  # <- scrivi qui la tua soluzione"],
    ),
    ex(
        2, "classe Rettangolo",
        ["Crea una classe Rettangolo con attributi base e altezza e i metodi",
         "area() e perimetro().",
         "Esempio: Rettangolo(3, 4).area() -> 12 ; .perimetro() -> 14"],
        ["class Rettangolo:",
         "    def __init__(self, base, altezza):",
         "        self.base = base",
         "        self.altezza = altezza",
         "",
         "    def area(self):",
         "        return self.base * self.altezza",
         "",
         "    def perimetro(self):",
         "        return 2 * (self.base + self.altezza)"],
        ['r = Rettangolo(3, 4)',
         'assert r.area() == 12, "area = base * altezza"',
         'assert r.perimetro() == 14, "perimetro = 2*(base+altezza)"',
         'assert Rettangolo(5, 5).area() == 25, "quadrato"',
         'assert Rettangolo(2, 10).perimetro() == 24, "rettangolo allungato"'],
        stu=["class Rettangolo:",
             "    def __init__(self, base, altezza):",
             "        pass  # <- salva base e altezza",
             "",
             "    def area(self):",
             "        pass  # <- scrivi qui la tua soluzione",
             "",
             "    def perimetro(self):",
             "        pass  # <- scrivi qui la tua soluzione"],
    ),
    md(
        "## I mattoni del progetto: `Chunk` e `Documento`\n"
        "\n"
        "Il nostro assistente lavorera' su pezzetti di testo presi dai tutorial. "
        "Chiamiamo **chunk** (\"porzione\") ognuno di questi pezzetti. Un **Documento** "
        "raccoglie piu' chunk e permette di cercarci dentro.\n"
        "\n"
        "Ricorda: `testo[:50]` prende i primi 50 caratteri di una stringa; "
        "`parola in testo` controlla se una parola compare nel testo."
    ),
    ex(
        3, "classe Chunk",
        ["Un Chunk e' una porzione di testo di un tutorial.",
         "Attributi: testo, fonte, link. Metodo anteprima() che restituisce i primi",
         "50 caratteri di testo seguiti da \"...\" (esattamente tre punti).",
         "Esempio: Chunk(\"Ciao mondo\", \"g\", \"l\").anteprima() -> \"Ciao mondo...\""],
        ["class Chunk:",
         "    def __init__(self, testo, fonte, link):",
         "        self.testo = testo",
         "        self.fonte = fonte",
         "        self.link = link",
         "",
         "    def anteprima(self):",
         "        return self.testo[:50] + \"...\""],
        ['c = Chunk("Ciao mondo", "guida.md", "http://x")',
         'assert c.testo == "Ciao mondo", "salva il testo"',
         'assert c.fonte == "guida.md", "salva la fonte"',
         'assert c.anteprima() == "Ciao mondo...", "anteprima di un testo corto"',
         'assert Chunk("a" * 100, "f", "l").anteprima() == "a" * 50 + "...", "taglia a 50 caratteri"',
         'assert Chunk("a" * 100, "f", "l").anteprima().endswith("..."), "finisce con tre punti"'],
        stu=["class Chunk:",
             "    def __init__(self, testo, fonte, link):",
             "        pass  # <- salva testo, fonte e link",
             "",
             "    def anteprima(self):",
             "        pass  # <- primi 50 caratteri di testo + \"...\""],
    ),
    ex(
        4, "classe Documento",
        ["Un Documento ha un titolo e una lista di Chunk.",
         "Metodi: numero_chunks() e cerca_parola(parola) che restituisce la lista dei",
         "Chunk il cui testo contiene parola (senza distinguere maiuscole/minuscole).",
         "Esempio: doc.cerca_parola(\"python\") -> [chunk1, chunk2]"],
        ["class Documento:",
         "    def __init__(self, titolo, chunks):",
         "        self.titolo = titolo",
         "        self.chunks = chunks",
         "",
         "    def numero_chunks(self):",
         "        return len(self.chunks)",
         "",
         "    def cerca_parola(self, parola):",
         "        trovati = []",
         "        for chunk in self.chunks:",
         "            if parola.lower() in chunk.testo.lower():",
         "                trovati.append(chunk)",
         "        return trovati"],
        ['c1 = Chunk("Python e\' un linguaggio", "g1", "l1")',
         'c2 = Chunk("Le funzioni in Python", "g2", "l2")',
         'c3 = Chunk("Le classi e gli oggetti", "g3", "l3")',
         'doc = Documento("Guida", [c1, c2, c3])',
         'assert doc.numero_chunks() == 3, "conta i chunk"',
         'assert doc.cerca_parola("python") == [c1, c2], "ricerca case-insensitive"',
         'assert doc.cerca_parola("classi") == [c3], "una sola corrispondenza"',
         'assert doc.cerca_parola("java") == [], "nessuna corrispondenza"'],
        stu=["class Documento:",
             "    def __init__(self, titolo, chunks):",
             "        pass  # <- salva titolo e chunks",
             "",
             "    def numero_chunks(self):",
             "        pass  # <- quanti chunk ci sono?",
             "",
             "    def cerca_parola(self, parola):",
             "        pass  # <- lista dei Chunk il cui testo contiene parola"],
    ),
    md(
        "## Attributo di classe vs attributo di istanza\n"
        "\n"
        "Un **attributo di classe** e' scritto dentro la classe ma fuori dai metodi: e' "
        "**condiviso** da tutte le istanze. Un **attributo di istanza** (`self.nome`) e' "
        "diverso per ogni oggetto. Se assegni un valore a un attributo di classe su una "
        "singola istanza, crei una copia locale che vale solo per quella istanza."
    ),
    ex(
        5, "classe Studente (attributo di classe)",
        ["La classe Studente ha un attributo di CLASSE scuola = \"Liceo Galilei\"",
         "(condiviso) e attributi di ISTANZA nome e voti (lista). Aggiungi il metodo",
         "media_voti() (0 se non ci sono voti).",
         "Esempio: Studente(\"Anna\", [8, 6, 10]).media_voti() -> 8.0"],
        ["class Studente:",
         "    scuola = \"Liceo Galilei\"",
         "",
         "    def __init__(self, nome, voti):",
         "        self.nome = nome",
         "        self.voti = voti",
         "",
         "    def media_voti(self):",
         "        if len(self.voti) == 0:",
         "            return 0",
         "        return sum(self.voti) / len(self.voti)"],
        ['a = Studente("Anna", [8, 6, 10])',
         'b = Studente("Luca", [5, 7])',
         'assert a.scuola == "Liceo Galilei", "attributo di classe condiviso"',
         'assert a.media_voti() == 8, "media di Anna"',
         'assert b.media_voti() == 6, "media di Luca"',
         'a.scuola = "Istituto Fermi"',
         'assert a.scuola == "Istituto Fermi", "Anna cambia la sua scuola"',
         'assert b.scuola == "Liceo Galilei", "Luca resta nella scuola di partenza"'],
        stu=["class Studente:",
             "    scuola = \"Liceo Galilei\"   # attributo di classe (gia\' scritto)",
             "",
             "    def __init__(self, nome, voti):",
             "        pass  # <- salva nome e voti",
             "",
             "    def media_voti(self):",
             "        pass  # <- media dei voti, 0 se la lista e\' vuota"],
    ),
    md(
        "## `@property`\n"
        "\n"
        "Una **property** e' un metodo che si usa come se fosse un attributo (senza "
        "parentesi). Serve a calcolare un valore al volo o a convertirlo. Con il "
        "*setter* puoi anche intercettare l'assegnamento.\n"
        "\n"
        "Formula: gradi Fahrenheit = celsius * 9 / 5 + 32.\n"
        "\n"
        "> **Se vieni da Java:** sostituisce la coppia getter/setter (`getCelsius()` / "
        "`setCelsius()`) con una sintassi che sembra un semplice attributo."
    ),
    ex(
        6, "classe Temperatura (@property)",
        ["Salva internamente solo i gradi celsius (in self._celsius). Esponi due",
         "property: celsius e fahrenheit, che si convertono automaticamente. Devono",
         "funzionare sia in lettura sia in scrittura (setter).",
         "Esempio: Temperatura(100).fahrenheit -> 212.0"],
        ["class Temperatura:",
         "    def __init__(self, celsius):",
         "        self._celsius = celsius",
         "",
         "    @property",
         "    def celsius(self):",
         "        return self._celsius",
         "",
         "    @celsius.setter",
         "    def celsius(self, valore):",
         "        self._celsius = valore",
         "",
         "    @property",
         "    def fahrenheit(self):",
         "        return self._celsius * 9 / 5 + 32",
         "",
         "    @fahrenheit.setter",
         "    def fahrenheit(self, valore):",
         "        self._celsius = (valore - 32) * 5 / 9"],
        ['t = Temperatura(100)',
         'assert t.celsius == 100, "legge i celsius"',
         'assert t.fahrenheit == 212, "100 C equivale a 212 F"',
         'assert Temperatura(0).fahrenheit == 32, "0 C equivale a 32 F"',
         't.fahrenheit = 32',
         'assert t.celsius == 0, "impostando i fahrenheit cambiano i celsius"'],
        stu=["class Temperatura:",
             "    def __init__(self, celsius):",
             "        pass  # <- salva il valore in self._celsius",
             "",
             "    @property",
             "    def celsius(self):",
             "        pass  # <- restituisci i gradi celsius salvati",
             "",
             "    @celsius.setter",
             "    def celsius(self, valore):",
             "        pass  # <- aggiorna self._celsius",
             "",
             "    @property",
             "    def fahrenheit(self):",
             "        pass  # <- converti da celsius a fahrenheit",
             "",
             "    @fahrenheit.setter",
             "    def fahrenheit(self, valore):",
             "        pass  # <- converti da fahrenheit e aggiorna self._celsius"],
    ),
    md(
        "## `@staticmethod` e `@classmethod`\n"
        "\n"
        "Un **metodo statico** (`@staticmethod`) non usa `self`: e' una funzione di "
        "utilita' che vive dentro la classe. Un **metodo di classe** (`@classmethod`) "
        "riceve la classe come primo parametro (`cls`) e di solito serve a costruire "
        "oggetti in modi alternativi (una \"fabbrica\").\n"
        "\n"
        "Utili qui: `\"@\" in stringa`, `stringa.split(\"@\")`, `stringa.isdigit()`, "
        "`len(stringa)`."
    ),
    ex(
        7, "classe Validatore (@staticmethod)",
        ["Crea una classe Validatore con due metodi statici:",
         "- email_valida(stringa): True se c'e' una @ e almeno un punto DOPO la @",
         "- telefono_valido(stringa): True se sono solo cifre, lunghe 9 o 10 caratteri",
         "Esempio: Validatore.email_valida(\"a@b.it\") -> True"],
        ["class Validatore:",
         "    @staticmethod",
         "    def email_valida(stringa):",
         "        if \"@\" not in stringa:",
         "            return False",
         "        dopo = stringa.split(\"@\")[-1]",
         "        return \".\" in dopo",
         "",
         "    @staticmethod",
         "    def telefono_valido(stringa):",
         "        return stringa.isdigit() and len(stringa) in (9, 10)"],
        ['assert Validatore.email_valida("a@b.it") == True, "email valida"',
         'assert Validatore.email_valida("ab.it") == False, "manca la @"',
         'assert Validatore.email_valida("a@bit") == False, "manca il punto dopo la @"',
         'assert Validatore.telefono_valido("3331234567") == True, "10 cifre"',
         'assert Validatore.telefono_valido("333123456") == True, "9 cifre"',
         'assert Validatore.telefono_valido("33312") == False, "troppo corto"',
         'assert Validatore.telefono_valido("333abc4567") == False, "contiene lettere"'],
        stu=["class Validatore:",
             "    @staticmethod",
             "    def email_valida(stringa):",
             "        pass  # <- c'e' una @ e almeno un punto dopo?",
             "",
             "    @staticmethod",
             "    def telefono_valido(stringa):",
             "        pass  # <- solo cifre, lunghe 9 o 10?"],
    ),
    ex(
        8, "Chunk.from_dict (@classmethod)",
        ["Riprendi la classe Chunk (qui sotto __init__ e anteprima sono gia' pronti)",
         "e aggiungi un classmethod from_dict(d) che crea un Chunk a partire da un",
         "dizionario {\"testo\": ..., \"fonte\": ..., \"link\": ...}.",
         "Esempio: Chunk.from_dict({\"testo\": \"x\", \"fonte\": \"f\", \"link\": \"l\"})"],
        ["class Chunk:",
         "    def __init__(self, testo, fonte, link):",
         "        self.testo = testo",
         "        self.fonte = fonte",
         "        self.link = link",
         "",
         "    def anteprima(self):",
         "        return self.testo[:50] + \"...\"",
         "",
         "    @classmethod",
         "    def from_dict(cls, d):",
         "        return cls(d[\"testo\"], d[\"fonte\"], d[\"link\"])"],
        ['d = {"testo": "Contenuto del tutorial", "fonte": "guida.md", "link": "http://x"}',
         'c = Chunk.from_dict(d)',
         'assert isinstance(c, Chunk), "restituisce un oggetto Chunk"',
         'assert c.testo == "Contenuto del tutorial", "testo preso dal dizionario"',
         'assert c.fonte == "guida.md", "fonte presa dal dizionario"',
         'assert c.link == "http://x", "link preso dal dizionario"'],
        stu=["class Chunk:",
             "    def __init__(self, testo, fonte, link):",
             "        self.testo = testo",
             "        self.fonte = fonte",
             "        self.link = link",
             "",
             "    def anteprima(self):",
             "        return self.testo[:50] + \"...\"",
             "",
             "    @classmethod",
             "    def from_dict(cls, d):",
             "        pass  # <- crea e restituisci un Chunk dai dati del dizionario d"],
    ),
    md(
        "## Ereditarieta'\n"
        "\n"
        "Una classe puo' **ereditare** da un'altra (`class Figlia(Genitore):`) e "
        "**ridefinire** i suoi metodi. La classe figlia riceve gratis attributi e metodi "
        "del genitore (incluso `__init__`).\n"
        "\n"
        "Nel progetto distingueremo le domande facili da quelle che richiedono un esperto."
    ),
    ex(
        9, "ereditarieta' delle Domande",
        ["Classe base Domanda con attributo testo e metodo rispondi() che restituisce",
         "\"Risposta generica\". Due sottoclassi che ridefiniscono rispondi():",
         "- DomandaSemplice -> \"Risposta semplice a: <testo>\"",
         "- DomandaComplessa -> \"Serve un esperto per: <testo>\""],
        ["class Domanda:",
         "    def __init__(self, testo):",
         "        self.testo = testo",
         "",
         "    def rispondi(self):",
         "        return \"Risposta generica\"",
         "",
         "",
         "class DomandaSemplice(Domanda):",
         "    def rispondi(self):",
         "        return f\"Risposta semplice a: {self.testo}\"",
         "",
         "",
         "class DomandaComplessa(Domanda):",
         "    def rispondi(self):",
         "        return f\"Serve un esperto per: {self.testo}\""],
        ['assert Domanda("x").rispondi() == "Risposta generica", "risposta della classe base"',
         'assert DomandaSemplice("ciao").rispondi() == "Risposta semplice a: ciao", "sottoclasse semplice"',
         'assert DomandaComplessa("aiuto").rispondi() == "Serve un esperto per: aiuto", "sottoclasse complessa"',
         'assert DomandaSemplice("x").testo == "x", "eredita __init__ dalla classe base"'],
        stu=["class Domanda:",
             "    def __init__(self, testo):",
             "        self.testo = testo",
             "",
             "    def rispondi(self):",
             "        return \"Risposta generica\"",
             "",
             "",
             "class DomandaSemplice(Domanda):",
             "    def rispondi(self):",
             "        pass  # <- \"Risposta semplice a: <testo>\"",
             "",
             "",
             "class DomandaComplessa(Domanda):",
             "    def rispondi(self):",
             "        pass  # <- \"Serve un esperto per: <testo>\""],
    ),
    md(
        "## L'esercizio [SFIDA]: mettere tutto insieme\n"
        "\n"
        "Ora costruisci il cuore dell'assistente. Usa la classe `Chunk` (gia' definita "
        "negli esercizi precedenti). L'assistente conserva una lista di chunk e sa "
        "cercare il primo che contiene una parola: e' la base del nostro progetto."
    ),
    ex(
        10, "classe AssistenteVirtuale",
        ["Crea la classe AssistenteVirtuale. All'inizio ha una lista chunks vuota.",
         "Metodi:",
         "- aggiungi_chunk(chunk): aggiunge un Chunk alla lista",
         "- cerca(parola): restituisce il PRIMO Chunk il cui testo contiene parola",
         "  (senza distinguere maiuscole/minuscole), oppure None se non trova niente."],
        ["class AssistenteVirtuale:",
         "    def __init__(self):",
         "        self.chunks = []",
         "",
         "    def aggiungi_chunk(self, chunk):",
         "        self.chunks.append(chunk)",
         "",
         "    def cerca(self, parola):",
         "        for chunk in self.chunks:",
         "            if parola.lower() in chunk.testo.lower():",
         "                return chunk",
         "        return None"],
        ['assistente = AssistenteVirtuale()',
         'assert assistente.chunks == [], "parte senza chunk"',
         'c1 = Chunk("Come si installa Python", "g1", "l1")',
         'c2 = Chunk("Come si usa il bot Telegram", "g2", "l2")',
         'assistente.aggiungi_chunk(c1)',
         'assistente.aggiungi_chunk(c2)',
         'assert len(assistente.chunks) == 2, "ha aggiunto due chunk"',
         'assert assistente.cerca("telegram") is c2, "trova il chunk giusto (case-insensitive)"',
         'assert assistente.cerca("python") is c1, "trova il primo chunk che contiene la parola"',
         'assert assistente.cerca("javascript") is None, "None se non trova niente"'],
        stu=["class AssistenteVirtuale:",
             "    def __init__(self):",
             "        pass  # <- inizializza self.chunks come lista vuota",
             "",
             "    def aggiungi_chunk(self, chunk):",
             "        pass  # <- aggiungi chunk alla lista",
             "",
             "    def cerca(self, parola):",
             "        pass  # <- restituisci il primo Chunk che contiene parola, o None"],
        sfida=True,
    ),
]


if __name__ == "__main__":
    print("Genero i notebook didattici...")
    write_pair("01_strutture_dati_e_cicli", NB1)
    if NB2:
        write_pair("02_funzioni_e_librerie", NB2)
    if NB3:
        write_pair("03_classi", NB3)
    print("Fatto.")
