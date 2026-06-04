# Bootcamp Python — Notebook didattici (Giorni 1-3)

Tre Jupyter notebook in italiano per imparare Python **direttamente nel browser**, senza installare nulla. Sono il materiale dei primi tre giorni di un bootcamp rivolto a studenti delle scuole superiori, pensato per chi conosce già un po' di programmazione (C, Java) ma è alle prime armi con Python.

## Link al sito

> **Pagina di benvenuto (consigliata per gli studenti):**
> **https://ulivs-app.github.io/python-tutorial/lab/index.html?path=README.md**
>
> Apri la home di JupyterLite: <https://ulivs-app.github.io/python-tutorial/>
>
> *(disponibili dopo il primo deploy di GitHub Pages)*

Cliccando il primo link si apre JupyterLite con la guida di benvenuto già **renderizzata** (i file `.md` si aprono in anteprima grazie a [overrides.json](overrides.json)). Gli esercizi girano nel browser tramite Pyodide (Python compilato in WebAssembly).

## I tre notebook

| # | Notebook | Argomenti |
|---|----------|-----------|
| 1 | `01_strutture_dati_e_cicli.ipynb` | `if`/`for`/`while`, scope, tuple, liste, dizionari, list comprehension |
| 2 | `02_funzioni_e_librerie.ipynb` | funzioni, parametri default, `*args`, ricorsione, `math`/`random`/`json` |
| 3 | `03_classi.ipynb` | classi, `__init__`, metodi, `@staticmethod`/`@classmethod`/`@property`, ereditarietà |

Ogni notebook contiene 10 esercizi con **verifica automatica**: lo studente scrive la soluzione e ottiene subito un feedback (`[OK]`, `[X]` o `[!]`).

## Come funziona

Tutto gira **nel browser dello studente**, senza server e senza installazioni: il codice Python viene eseguito da Pyodide (WebAssembly). Basta una connessione per caricare la pagina la prima volta. Niente account, niente setup.

GitHub Pages serve un sito statico generato da [JupyterLite](https://jupyterlite.readthedocs.io). Ad ogni `push` sul branch `main`, GitHub Actions ricostruisce e ripubblica il sito automaticamente.

## Per i docenti

> Guida operativa completa (rigenerare, verificare, pubblicare): [docs/MANUTENZIONE.md](docs/MANUTENZIONE.md).

**Dove stanno le soluzioni.** La cartella `solutions/` contiene le versioni complete (`*_SOL.ipynb`) con tutte le funzioni già risolte. Questa cartella **non viene pubblicata**: il build di JupyterLite include solo `content/`, e `jupyter_lite_config.json` la esclude esplicitamente come ulteriore garanzia. Gli studenti non possono vederla dal sito.

**Come modificare i notebook.** I notebook (sia studente che soluzione) sono generati da un unico script, `tools/build_notebooks.py`, che definisce ogni esercizio una sola volta (enunciato + soluzione + test) ed emette automaticamente le due versioni allineate. Per modificare un esercizio, cambia il contenuto nello script e rigenera:

```bash
uv venv
uv pip install -r requirements.txt nbformat nbclient ipykernel
uv run python tools/build_notebooks.py
```

Puoi anche editare i `.ipynb` a mano, ma ricordati di tenere allineate le due versioni (studente e `_SOL`).

**Provare in locale prima di pubblicare.**

```bash
uv run jupyter lite build --contents content --output-dir dist
python -m http.server -d dist 8000   # poi apri http://localhost:8000
```

**Aggiornare il sito pubblicato.** Fai commit e push sul branch `main`: GitHub Actions ribuilda e ripubblica in pochi minuti.

```bash
git add -A && git commit -m "aggiorna esercizi" && git push
```

## Per gli studenti

Apri il link al sito qui sopra, scegli il notebook del giorno e segui le istruzioni nella pagina di benvenuto. **Non serve installare niente.**

## Licenza

Materiale a cura di **Open Innova S.R.L.** ([openinnova.it](https://www.openinnova.it)), distribuito con licenza **[Creative Commons Attribuzione 4.0 Internazionale (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/deed.it)**.

Sei libero di riusarlo, modificarlo e ridistribuirlo, anche per fini commerciali, **a patto di citare la fonte**. Vedi il file [LICENSE](LICENSE) per i dettagli e per il testo di attribuzione consigliato.

## Setup iniziale di GitHub Pages (una volta sola)

1. Crea un repository su GitHub e fai push di questo codice.
2. Vai su **Settings → Pages → Source** e scegli **GitHub Actions**.
3. Attendi il primo build (qualche minuto): l'indirizzo del sito comparirà nella stessa pagina.
4. Sostituisci i placeholder `USERNAME`/`NOME-REPO` in questo README con i valori reali.
