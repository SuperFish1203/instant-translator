$ErrorActionPreference = "Stop"

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    throw "Virtual environment not found. Expected .venv\\Scripts\\python.exe"
}

& .\.venv\Scripts\python.exe -m PyInstaller `
  --noconfirm `
  --noconsole `
  --name InstantTranslator `
  --paths src `
  src/instant_translator/app.py
