NEW REQUIREMENTS & INSTALLATION

Purpose

This document lists the pip installation steps and quick verification commands to reproduce the working environment for this project on macOS (zsh). It highlights packages installed during debugging and optional steps for enabling transformer-based sentiment models (which may crash on some macOS setups).

Assumptions

- You're using the project's virtualenv located at `./env` (created in the repo root).
- You're on macOS with zsh (commands below assume zsh).

Checklist

- [ ] Activate the project virtualenv
- [ ] Install all project requirements
- [ ] Install specific additional packages used during debugging
- [ ] (Optional) Enable transformers safely
- [ ] Verify imports succeed

Quick install steps (recommended)

1) Activate the virtualenv (preferred):

```bash
source ./env/bin/activate
```

2) Install everything from the project `requirements.txt` (idempotent):

```bash
pip install -r requirements.txt
```

3) Install packages that were added/verified during debugging (explicit pins used in this project):

```bash
pip install "langchain==0.3.13" "langchain-community==0.3.13" "langchain-huggingface==0.1.2" "textblob==0.18.0.post0" "loguru==0.7.3"
```

(If you prefer to use the repo's pip binary without activating the env, use `./env/bin/pip install ...`.)

Optional: transformers & pytorch (use with caution)

The HuggingFace/transformers sentiment pipeline can provide better accuracy but may trigger native (bus) errors on some macOS / CPU builds. If you want to try it:

```bash
# install transformers and a compatible torch build (choose appropriate torch for your CPU/GPU)
pip install transformers==4.57.3 torch
```

Notes and safe approaches

- If transformer-based models crash your process, prefer the TextBlob fallback (pure Python) for stability — the pipeline currently defaults to TextBlob to avoid native crashes.
- To use transformers safely:
  - Run the transformer model in a separate worker/subprocess, or
  - Use a hosted inference API (Hugging Face Inference Endpoint, etc.), or
  - Try installing a different torch wheel (e.g., CPU-only) that matches your macOS architecture.

Quick import verification

Run this to check that core packages import correctly (while the venv is activated):

```bash
python - <<'PY'
try:
    import importlib
    for pkg in ("loguru","langchain","textblob","langchain_huggingface"):
        importlib.import_module(pkg)
        print(pkg, "OK")
except Exception as e:
    print("IMPORT ERROR:", e)
    raise
PY
```

If you see any `IMPORT ERROR`, re-run `pip install <package>` inside the virtualenv.

If you want, I can:
- Add these explicit package pins to `requirements.txt` (PR), or
- Add a small `scripts/verify_env.sh` helper to automate the steps above.

File created: `NEW_REQUIREMENTS.md` — follow the steps above to reproduce the working environment.
