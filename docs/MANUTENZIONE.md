# Manutenzione del repository (per i docenti)

Guida rapida per modificare gli esercizi e ripubblicare il sito.

## Prerequisiti (una volta sola)

Serve [uv](https://docs.astral.sh/uv/). Prepara l'ambiente locale:

```bash
uv venv
uv pip install -r requirements.txt nbformat nbclient ipykernel
```

`nbformat`, `nbclient` e `ipykernel` servono solo a generare e verificare i
notebook in locale; non fanno parte di quello che gira nel browser.

## Flusso di aggiornamento

Gli esercizi si modificano **in un solo posto**: `tools/build_notebooks.py`.
Lì ogni esercizio è definito una volta (enunciato, soluzione, test). Dopo aver
modificato lo script, rigenera, verifica e pubblica:

```bash
uv run python tools/build_notebooks.py && uv run python tools/verify_notebooks.py
git add -A && git commit -m "..." && git push
```

Cosa fa ciascun passo:

1. **`build_notebooks.py`** rigenera in modo allineato sia le versioni studente
   (`content/*.ipynb`) sia le soluzioni (`solutions/*_SOL.ipynb`). Non modificare
   i `.ipynb` a mano: verrebbero sovrascritti alla rigenerazione successiva.
2. **`verify_notebooks.py`** esegue tutti i notebook e controlla i criteri di
   accettazione: nelle soluzioni ogni test stampa `[OK] Corretto!`, nelle versioni
   studente ogni test fallisce in modo pulito (`[X]` o `[!]`), senza crash.
   Se segnala un problema, **non pubblicare**: correggi prima lo script.
3. **`git push`** su `main` fa ripartire il workflow GitHub Actions, che ricostruisce
   e ripubblica il sito su GitHub Pages in pochi minuti.

## Provare il sito in locale (facoltativo)

```bash
uv run jupyter lite build --contents content --output-dir dist
python3 -m http.server -d dist 8000   # poi apri http://localhost:8000/lab
```

## Se una modifica alla config non si applica

JupyterLite tiene una cache di build (`.jupyterlite.doit.db`). Se cambi `jupyter-lite.json` o `overrides.json` e non vedi l'effetto in locale, cancella cache e output e ribuilda:

```bash
rm -rf dist .jupyterlite.doit.db
uv run jupyter lite build --contents content --output-dir dist
```

(In CI il problema non si pone: ogni run parte da un checkout pulito.)

## Note utili

- La cartella `solutions/` è nel repository ma **non** viene pubblicata sul sito
  (il build include solo `content/`, e `jupyter_lite_config.json` la esclude
  comunque). Per gli studenti che usano solo il link del sito le soluzioni restano
  nascoste.
- Nelle versioni studente la cella con il test appare **collassata**
  (`source_hidden`): lo studente la esegue e vede solo il risultato. È un
  accorgimento visivo, non una protezione: chi vuole può sempre espanderla.
- Stato dei deploy: <https://github.com/ulivs-app/python-tutorial/actions>

## Tema e branding

- **Tema:** impostato in `overrides.json` con `@jupyterlab/apputils-extension:themes` → `theme`. Default `"JupyterLab Night"` (scuro). Altri valori: `"JupyterLab Dark"`, `"JupyterLab Light"`. Il tema `jupyterlab-night` è installato via `requirements.txt`.
- **Nome app, favicon, rimozione logo Jupyter:** in `jupyter-lite.json` (`appName`, `faviconUrl`, `disabledExtensions`).
- **Favicon e logo:** `content/favicon.svg` (servita dal sito, finisce in `dist/files/favicon.svg`) e `docs/logo.svg` (logo completo, solo nel repo), ripresi dal sito Open Innova.
- Tutto è guidato da file versionati: sopravvive ai rebuild della CI, nessuna modifica manuale a `dist/`.
- Nota: il logo immagine in alto a sinistra non è sostituibile via sola configurazione (servirebbe una piccola estensione JupyterLab); per questo l'header mostra il nome testuale + favicon.
