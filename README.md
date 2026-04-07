# Once Upon App (MVP)

This app is built from `11-OnceUpon.md` and implements a beginner-friendly MVP of the personalized storytelling concept.

## Features implemented

- Story parameter builder
  - child name, age range, protagonist, traits, setting, theme, moral lesson
- Age-range aware story style
- Structured output sections
  - Introduction, Challenge, Resolution, Moral
- Illustrated chapter break prompts (scene descriptions)
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

- `stories.json` (auto-created on first story generation)

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
