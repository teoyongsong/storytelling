# Once Upon App (MVP)

This app is built from `11-OnceUpon.md` and implements a beginner-friendly MVP of the personalized storytelling concept.

## Features implemented

- Story parameter builder
  - child name, age range, protagonist, traits, setting, theme, moral lesson
- Age-range aware story style
- Structured output sections
  - Introduction, Challenge, Resolution, Moral
- Illustrated chapter break prompts (scene descriptions)
- Optional images per chapter (Introduction, Challenge, Resolution), saved with the story
- Download a **complete storybook** as one HTML file (text + images + scene captions); open in a browser or print to PDF
- Story persistence in local JSON storage
- Child profile story library
- Parent dashboard with generation history

## Run locally

```bash
cd /home/teoyongsong/storytelling
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Data storage

- Stories are saved next to the app: `stories.json` in the same folder as `app.py` (not the shell’s current directory).
- The app keeps a copy in browser session state so stories still show after a rerun even if disk write fails briefly.
- **Streamlit Cloud**: the filesystem is ephemeral; stories can disappear after the app sleeps or redeploys. Use **Manage app → Reboot** awareness, or add an external database later for permanent cloud storage.

## OpenAI (optional)

In the app sidebar, choose **OpenAI** and either:

- set `OPENAI_API_KEY` in your environment, or
- paste an API key in the sidebar (only shown when needed), or
- on Streamlit Cloud: **App settings → Secrets** with:

```toml
OPENAI_API_KEY = "sk-..."
```

If you pick **Local template**, no API key is required.

## Notes

- Default generation is a local template; OpenAI uses the Chat Completions API (`generate_story_openai` in `app.py`).
