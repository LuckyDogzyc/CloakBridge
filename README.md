# CloakBridge

CloakBridge is a local privacy gateway for office documents and external AI.

## Security Rules

- Original sensitive documents stay on the local machine.
- Sensitive dictionaries and token mappings stay on the local machine.
- External providers receive sanitized content only.
- The backend binds to `127.0.0.1` by default.
- The public repository contains synthetic data only.

## MVP Scope

- `.txt`
- `.docx`
- `.xlsx`

PDF, PPT, CAD, drawings, images, OCR, and heavy local LLMs are outside the first version.

## Local Backend

```bash
python -m uvicorn cloakbridge.main:app --app-dir backend --host 127.0.0.1 --port 8765
```

## WebUI

```bash
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`.
