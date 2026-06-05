#!/usr/bin/env python3
"""Genera i notebook studente (content/) e soluzione (solutions/) a partire dai
notebook-SORGENTE in source/.

Fonte di verita': i notebook in source/NN.ipynb. Sono eseguibili (il docente li
apre in JupyterLab, esegue e verifica che i test passino). Le parti da nascondere
allo studente sono marcate con la convenzione nbgrader:

    def funzione(...):
        ### BEGIN SOLUTION
        <codice soluzione>
        ### END SOLUTION

Una cella e':
  - di TEST se contiene "# [TEST]" (blocco try/except con gli assert);
  - di ESERCIZIO se contiene "### BEGIN SOLUTION";
  - altrimenti viene copiata tal quale (markdown, import, esempi, ...).

Output:
  - content/NN.ipynb (studente): i blocchi soluzione diventano `pass`, le celle
    di test sono collassate (source_hidden), con banner in cima e credito in fondo;
  - solutions/NN_SOL.ipynb (docente): marcatori rimossi (soluzione visibile),
    test visibili, banner + credito.

Uso:  uv run python tools/build_notebooks.py
"""

import os
import base64
import nbformat as nbf
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE_DIR = os.path.join(ROOT, "source")
CONTENT_DIR = os.path.join(ROOT, "content")
SOLUTIONS_DIR = os.path.join(ROOT, "solutions")
BRANDING_DIR = os.path.join(ROOT, "branding")

# Colori del brand Open Innova.
BRAND_NAVY = "#19213c"
BRAND_GREEN = "#6bb889"

# Marcatori (convenzione nbgrader) e placeholder per lo studente.
BEGIN = "### BEGIN SOLUTION"
END = "### END SOLUTION"
STUDENT_PLACEHOLDER = "pass  # <- scrivi qui la tua soluzione"

# Pagina di benvenuto: il banner fra questi marcatori viene rigenerato dal build.
README_PATH = os.path.join(ROOT, "content", "README.md")
BANNER_START = "<!-- BANNER:START (rigenerato da build_notebooks.py, non modificare) -->"
BANNER_END = "<!-- BANNER:END -->"

KERNEL_META = {
    "kernelspec": {"name": "python", "display_name": "Python (Pyodide)", "language": "python"},
    "language_info": {"name": "python"},
}
# Metadati per collassare l'input di una cella (test nascosto allo studente).
HIDDEN_META = {"jupyter": {"source_hidden": True}}

# Slug dei 3 notebook (file in source/, content/ e, con suffisso _SOL, in solutions/).
SLUGS = [
    "01_strutture_dati_e_cicli",
    "02_funzioni_e_librerie",
    "03_classi",
]


# --- Banner e credito (iniettati nei notebook generati) ----------------------

def banner_text():
    """HTML del banner brandizzato; il logo bianco e' incorporato come data-URI."""
    with open(os.path.join(BRANDING_DIR, "logo-white.svg"), "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    logo = f"data:image/svg+xml;base64,{b64}"
    return (
        f'<div style="background:{BRAND_NAVY};border-left:6px solid {BRAND_GREEN};'
        'border-radius:8px;padding:16px 20px;display:flex;align-items:center;'
        'gap:18px;color:#ffffff;font-family:sans-serif;">'
        f'<img src="{logo}" alt="Open Innova" style="height:48px;width:auto;" />'
        '<div>'
        '<div style="font-size:1.35em;font-weight:700;color:#ffffff;">Bootcamp Python</div>'
        f'<div style="font-size:0.95em;color:{BRAND_GREEN};">Open Innova &middot; Python for beginners</div>'
        '</div></div>'
    )


CREDITO_TEXT = (
    "---\n"
    "*Materiale a cura di Open Innova S.R.L. (openinnova.it), distribuito con "
    "licenza Creative Commons Attribuzione 4.0 Internazionale (CC BY 4.0). "
    "Riusabile e modificabile citando la fonte.*"
)


# --- Trasformazioni sulle celle ----------------------------------------------

def is_test_cell(src):
    return "# [TEST]" in src


def is_exercise_cell(src):
    return BEGIN in src


def strip_markers(src):
    """Versione soluzione: rimuove solo le righe-marcatore, lascia la soluzione."""
    return "\n".join(
        line for line in src.split("\n") if line.strip() not in (BEGIN, END)
    )


def make_student(src):
    """Versione studente: ogni blocco BEGIN..END diventa un `pass` (all'indentazione
    del marcatore). Le righe fuori dai blocchi (incl. eventuali suggerimenti) restano."""
    lines = src.split("\n")
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.strip() == BEGIN:
            indent = line[: len(line) - len(line.lstrip())]
            out.append(indent + STUDENT_PLACEHOLDER)
            i += 1
            while i < len(lines) and lines[i].strip() != END:
                i += 1
            i += 1  # salta la riga END
        else:
            out.append(line)
            i += 1
    return "\n".join(out)


# --- Costruzione dei notebook ------------------------------------------------

def build_one(slug):
    src_nb = nbf.read(os.path.join(SOURCE_DIR, f"{slug}.ipynb"), as_version=4)
    banner = banner_text()

    student = [new_markdown_cell(banner)]
    solution = [new_markdown_cell(banner)]

    for cell in src_nb.cells:
        if cell.cell_type == "markdown":
            student.append(new_markdown_cell(cell.source))
            solution.append(new_markdown_cell(cell.source))
            continue
        src = cell.source
        if is_exercise_cell(src):
            student.append(new_code_cell(make_student(src)))
            solution.append(new_code_cell(strip_markers(src)))
        elif is_test_cell(src):
            student.append(new_code_cell(src, metadata=dict(HIDDEN_META)))
            solution.append(new_code_cell(src))
        else:
            student.append(new_code_cell(src))
            solution.append(new_code_cell(src))

    student.append(new_markdown_cell(CREDITO_TEXT))
    solution.append(new_markdown_cell(CREDITO_TEXT))

    os.makedirs(CONTENT_DIR, exist_ok=True)
    os.makedirs(SOLUTIONS_DIR, exist_ok=True)
    _write(os.path.join(CONTENT_DIR, f"{slug}.ipynb"), student)
    _write(os.path.join(SOLUTIONS_DIR, f"{slug}_SOL.ipynb"), solution)
    print(f"  generato: content/{slug}.ipynb  e  solutions/{slug}_SOL.ipynb")


def _write(path, cells):
    nb = new_notebook(cells=cells)
    nb.metadata = KERNEL_META
    with open(path, "w", encoding="utf-8") as f:
        nbf.write(nb, f)


def update_readme_banner():
    """Rigenera il banner nella pagina di benvenuto (content/README.md), nella
    regione fra BANNER_START e BANNER_END, usando lo stesso banner dei notebook."""
    if not os.path.exists(README_PATH):
        return
    txt = open(README_PATH, encoding="utf-8").read()
    block = f"{BANNER_START}\n{banner_text()}\n{BANNER_END}"
    if BANNER_START in txt and BANNER_END in txt:
        pre = txt[: txt.index(BANNER_START)]
        post = txt[txt.index(BANNER_END) + len(BANNER_END):]
        txt = pre + block + post
    else:  # marcatori assenti: inserisce il banner in cima
        txt = block + "\n\n" + txt
    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(txt)
    print("  aggiornato: content/README.md (banner)")


if __name__ == "__main__":
    print("Genero i notebook da source/ ...")
    for slug in SLUGS:
        build_one(slug)
    update_readme_banner()
    print("Fatto.")
