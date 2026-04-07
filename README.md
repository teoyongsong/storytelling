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

## Notes

- Current implementation uses a local template-based story generator.
- To upgrade, replace `generate_story()` in `app.py` with an LLM API call.
