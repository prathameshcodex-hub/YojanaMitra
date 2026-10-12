# YojanaMitra

**Team:** Bug Slayers  
**Project:** Government Scheme Eligibility Reverse-Matcher  
**Hackathon:** OpenForge Hackathon | SWAYAMBHU 2026-27  
**Track:** Track 1 — Open Weight AI & Open Source Tools

## About
YojanaMitra is a web-based prototype that helps users discover Indian government schemes that may match their profile. It provides preliminary matches, eligibility-related reasons and scheme source links.

## Features
- Profile-based scheme matching
- Potential matches and rejection reasons
- Document checklist support
- Government scheme links
- FastAPI backend and browser-based frontend
- AI-assisted extraction of eligibility information from document text

## Technology Stack
- Python, FastAPI, HTML, CSS and JavaScript
- JSON scheme dataset
- Ollama local inference runtime
- **Exact model:** Qwen3-1.7B (`qwen3:1.7b`)
- **Parameter count:** 1.7 billion
- **Model card:** https://huggingface.co/Qwen/Qwen3-1.7B
- **Model license:** Apache License 2.0
- **License URL:** https://www.apache.org/licenses/LICENSE-2.0
- **Ollama model entry:** https://ollama.com/library/qwen3

## AI Workflow and Current Status

The local Qwen3-1.7B model runs through Ollama in `backend/ai_extractor.py` to convert extracted document text into structured eligibility JSON.

When the application loads scheme data, it checks `backend/data/ai_extracted/` for matching extraction files. For a matching scheme, the integration adds new occupation terms without overwriting existing occupation rules. Other extracted fields are not automatically merged.

AI-derived additions remain marked `needs_official_verification`. They are preliminary candidates and must be checked against official government sources. The generated `backend/data/ai_extracted/` folder is excluded from Git, so extraction files must be generated locally for this integration to add occupations.
## Run Locally
Backend: open PowerShell and run `cd C:\Users\ADMIN\YojanaMitra\backend`, activate the virtual environment with `.\venv\Scripts\Activate.ps1`, then run `python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000`.

Frontend: open a second PowerShell window, run `cd C:\Users\ADMIN\YojanaMitra`, then run `npx -y http-server frontend -p 5500`. Open `http://127.0.0.1:5500`.

The AI extraction utility requires Ollama and the `qwen3:1.7b` model to be available locally. Refer to `backend/ai_extractor.py` for usage details.

## Data Verification
The website dataset is stored in `backend/data/schemes.json`. Eligibility criteria and application details must be checked against current official government sources.

## Disclaimer
YojanaMitra provides preliminary eligibility guidance only. A potential match does not guarantee official eligibility or receipt of benefits.

## License
Original project code is released under the MIT License. Qwen and third-party components remain subject to their respective licenses and terms.

## Team
**Bug Slayers**
