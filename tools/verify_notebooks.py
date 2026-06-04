#!/usr/bin/env python3
"""Esegue i notebook e verifica i criteri di accettazione:

- nelle SOLUZIONI ogni cella di test stampa "[OK] Corretto!" (mai [X]/[!]);
- nelle versioni STUDENTE ogni cella di test stampa "[X]" o "[!]" (mai crash
  e mai [OK]);
- nessuna cella solleva eccezioni non gestite.

Uso:  uv run python tools/verify_notebooks.py
"""

import os
import sys
import nbformat
from nbclient import NotebookClient

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def cell_text(cell):
    out = []
    for o in cell.get("outputs", []):
        if o.get("output_type") == "stream":
            out.append(o.get("text", ""))
        elif o.get("output_type") in ("execute_result", "display_data"):
            out.append(o.get("data", {}).get("text/plain", ""))
        elif o.get("output_type") == "error":
            out.append("CRASH:" + o.get("ename", ""))
    return "".join(out)


def run(path):
    nb = nbformat.read(path, as_version=4)
    client = NotebookClient(nb, timeout=120, kernel_name="python3")
    client.execute()
    return nb


def check(path, expect_solution):
    nb = run(path)
    problems = []
    test_cells = 0
    for i, cell in enumerate(nb.cells):
        if cell.get("cell_type") != "code":
            continue
        src = cell.get("source", "")
        text = cell_text(cell)
        if "CRASH:" in text:
            problems.append(f"  cella {i}: CRASH non gestito ({text.strip()})")
            continue
        if "# [TEST]" not in src:
            continue  # non e' una cella-esercizio con verifica
        test_cells += 1
        ok = "[OK] Corretto!" in text
        fail = ("[X] Test fallito" in text) or ("[!] Errore" in text)
        if expect_solution and not ok:
            problems.append(f"  cella {i}: soluzione NON passa -> {text.strip()[:80]}")
        if (not expect_solution) and (ok or not fail):
            problems.append(f"  cella {i}: studente non fallisce in modo pulito -> {text.strip()[:80]}")
    return test_cells, problems


def main():
    targets = [
        ("solutions/01_strutture_dati_e_cicli_SOL.ipynb", True),
        ("solutions/02_funzioni_e_librerie_SOL.ipynb", True),
        ("solutions/03_classi_SOL.ipynb", True),
        ("content/01_strutture_dati_e_cicli.ipynb", False),
        ("content/02_funzioni_e_librerie.ipynb", False),
        ("content/03_classi.ipynb", False),
    ]
    total_problems = 0
    for rel, expect_solution in targets:
        path = os.path.join(ROOT, rel)
        n, problems = check(path, expect_solution)
        etichetta = "SOLUZIONE (atteso [OK])" if expect_solution else "STUDENTE (atteso [X]/[!])"
        if problems:
            total_problems += len(problems)
            print(f"[FALLITO] {rel}  [{etichetta}]  ({n} test)")
            print("\n".join(problems))
        else:
            print(f"[OK] {rel}  [{etichetta}]  ({n} test verificati)")
    print()
    if total_problems:
        print(f"VERIFICA FALLITA: {total_problems} problemi.")
        sys.exit(1)
    print("VERIFICA SUPERATA: tutti i notebook rispettano i criteri.")


if __name__ == "__main__":
    main()
