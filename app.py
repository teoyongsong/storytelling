import base64
import html as html_module
import json
import os
import re
from datetime import datetime
from pathlib import Path

import streamlit as st

try:
    import markdown as md_lib
except ImportError:
    md_lib = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


DATA_FILE = Path(__file__).resolve().parent / "stories.json"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
SESSION_DATA_KEY = "app_data"


def _get_secret(key: str):
    try:
        return st.secrets.get(key)
    except (FileNotFoundError, RuntimeError, AttributeError):
        return None


def resolve_openai_key(pasted: str | None) -> str | None:
    for candidate in (
        _get_secret("OPENAI_API_KEY"),
        os.environ.get("OPENAI_API_KEY"),
        pasted,
    ):
        if candidate and str(candidate).strip():
            return str(candidate).strip()
    return None


def load_data_from_disk():
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    # Legacy: older versions wrote stories.json relative to process cwd
    legacy = Path.cwd() / "stories.json"
    if legacy.exists():
        try:
            with open(legacy, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {"profiles": {}, "stories": []}


def save_data(data):
    try:
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except OSError as e:
        st.warning(
            f"Could not write {DATA_FILE}: {e}. "
            "Stories still apply for this browser session. "
            "On Streamlit Cloud, disk may be read-only or reset when the app sleeps."
        )


def get_app_data():
    """Single in-memory copy so reruns do not drop stories if disk path or write fails."""
    if SESSION_DATA_KEY not in st.session_state:
        st.session_state[SESSION_DATA_KEY] = load_data_from_disk()
    return st.session_state[SESSION_DATA_KEY]


def generate_story_template(params):
    age_range = params["age_range"]
    child_name = params["child_name"]
    protagonist = params["protagonist"]
    traits = params["traits"]
    setting = params["setting"]
    theme = params["theme"]
    moral = params["moral"]

    if age_range == "3-5":
        style = "short sentences, simple words, warm and playful tone"
    elif age_range == "6-8":
        style = "moderate vocabulary, clear events, gentle suspense"
    else:
        style = "richer vocabulary, deeper emotions, slightly longer scenes"

    intro = (
        f"One evening in {setting}, {protagonist} met {child_name}, "
        f"a friend known for being {traits}. Together they discovered a mystery related to {theme}."
    )
    challenge = (
        f"As the moon rose, they faced a tricky problem: their plan almost failed because they rushed. "
        f"They paused, listened to each other, and tried again."
    )
    resolution = (
        f"By working as a team, they solved the mystery and helped everyone in {setting}. "
        f"Their courage and kindness turned a hard night into a joyful celebration."
    )
    ending = f"They learned that {moral}."

    story = (
        f"Story style guide: {style}\n\n"
        "## Introduction\n"
        f"{intro}\n\n"
        "## Challenge\n"
        f"{challenge}\n\n"
        "## Resolution\n"
        f"{resolution}\n\n"
        "## Moral\n"
        f"{ending}\n"
    )
    return story


def build_openai_user_prompt(params: dict) -> str:
    return f"""Write a children's story with these parameters:
- Audience age band: {params['age_range']} years (adjust vocabulary, length, and emotional intensity accordingly).
- Child name (can appear as a character or be addressed gently): {params['child_name']}
- Main character: {params['protagonist']}
- Personality traits: {params['traits']}
- Setting: {params['setting']}
- Theme: {params['theme']}
- Moral lesson to land naturally (not preachy): {params['moral']}

Requirements:
- Positive, age-appropriate tone; no graphic violence or scary horror.
- Clear narrative arc across the sections below.
- Use markdown with EXACTLY these headings (and nothing before the first heading except a blank line if needed):

## Introduction

## Challenge

## Resolution

## Moral

## Scene prompts (for illustrators)

Under "## Scene prompts (for illustrators)", add exactly three bullet lines starting with "- " describing distinct illustration moments (one sentence each)."""


def parse_story_and_scenes(full_text: str, params: dict) -> tuple[str, list[str]]:
    marker = "## Scene prompts (for illustrators)"
    if marker not in full_text:
        return full_text.strip(), scene_descriptions(params)
    story_part, scenes_part = full_text.split(marker, 1)
    scenes = []
    for line in scenes_part.splitlines():
        line = line.strip()
        if line.startswith("- "):
            scenes.append(line[2:].strip())
    if len(scenes) < 3:
        return full_text.strip(), scene_descriptions(params)
    return story_part.strip(), scenes[:3]


def generate_story_openai(api_key: str, params: dict, model: str) -> tuple[str, list[str]]:
    if OpenAI is None:
        raise RuntimeError("Install the openai package: pip install openai")

    client = OpenAI(api_key=api_key)
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a skilled children's storyteller. "
                    "Follow the user's output format exactly. Write only the story markdown requested."
                ),
            },
            {"role": "user", "content": build_openai_user_prompt(params)},
        ],
        temperature=0.8,
    )
    raw = (completion.choices[0].message.content or "").strip()
    return parse_story_and_scenes(raw, params)


def scene_descriptions(params):
    return [
        f"Chapter 1 illustration: {params['protagonist']} and {params['child_name']} arriving at {params['setting']} at sunset.",
        f"Chapter 2 illustration: a tense moment around the theme of {params['theme']}, with expressive emotions.",
        f"Chapter 3 illustration: joyful resolution scene in {params['setting']} with warm lighting.",
    ]


def normalize_illustrations(item: dict) -> list:
    raw = item.get("illustration_images")
    if not raw:
        return [None, None, None]
    out = list(raw)
    while len(out) < 3:
        out.append(None)
    return out[:3]


def split_story_sections(md: str) -> list[tuple[str, str]]:
    """Split markdown into (heading, body) pairs. First chunk may have empty heading (preamble)."""
    pattern = r"^##\s+(.+)$"
    bits = re.split(pattern, md, flags=re.MULTILINE)
    out: list[tuple[str, str]] = []
    if bits[0].strip():
        out.append(("", bits[0].strip()))
    for i in range(1, len(bits), 2):
        heading = bits[i].strip()
        body = bits[i + 1].strip() if i + 1 < len(bits) else ""
        out.append((heading, body))
    return out


def md_to_html_fragment(text: str) -> str:
    if not text:
        return ""
    if md_lib is None:
        return f"<p>{html_module.escape(text).replace(chr(10), '<br/>')}</p>"
    try:
        return md_lib.markdown(text, extensions=["nl2br", "fenced_code"])
    except Exception:
        return md_lib.markdown(text)


def illustration_figure(img: dict | None, caption: str | None) -> str:
    if not img or not img.get("b64"):
        return ""
    mime = img.get("mime") or "image/png"
    cap = ""
    if caption:
        cap = f"<figcaption>{html_module.escape(caption)}</figcaption>"
    return (
        f'<figure class="illustration">'
        f'<img src="data:{html_module.escape(mime)};base64,{img["b64"]}" alt="Illustration"/>'
        f"{cap}</figure>"
    )


def image_slot_for_heading(heading: str) -> int | None:
    key = heading.strip().lower()
    return {"introduction": 0, "challenge": 1, "resolution": 2}.get(key)


def build_storybook_html(item: dict) -> str:
    params = item["params"]
    title = html_module.escape(
        f"Once Upon — {params.get('child_name', 'Story')} ({params.get('theme', '')})"
    )
    subtitle = html_module.escape(
        f"{params.get('setting', '')} · Ages {params.get('age_range', '')}"
    )
    sections = split_story_sections(item.get("story") or "")
    imgs = normalize_illustrations(item)
    scenes = item.get("scene_descriptions") or []

    parts: list[str] = []
    for heading, body in sections:
        if heading:
            parts.append(f"<h2>{html_module.escape(heading)}</h2>")
        else:
            parts.append('<div class="preamble">')
            parts.append(md_to_html_fragment(body))
            parts.append("</div>")
            continue
        parts.append(md_to_html_fragment(body))
        slot = image_slot_for_heading(heading)
        if slot is not None and imgs[slot]:
            cap = scenes[slot] if slot < len(scenes) else None
            parts.append(illustration_figure(imgs[slot], cap))

    body_html = "\n".join(parts)
    css = """
    :root { font-family: Georgia, "Times New Roman", serif; color: #222; }
    body { max-width: 40rem; margin: 2rem auto; padding: 0 1rem; line-height: 1.55; }
    h1 { font-size: 1.6rem; margin-bottom: 0.25rem; }
    .subtitle { color: #555; margin-bottom: 2rem; font-size: 0.95rem; }
    h2 { font-size: 1.25rem; margin-top: 1.75rem; border-bottom: 1px solid #ddd; padding-bottom: 0.25rem; }
    .preamble { font-style: italic; color: #444; margin-bottom: 1rem; }
    .illustration { margin: 1.25rem 0; text-align: center; }
    .illustration img { max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 12px rgba(0,0,0,0.12); }
    .illustration figcaption { font-size: 0.85rem; color: #555; margin-top: 0.5rem; }
    """
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{title}</title>
<style>{css}</style>
</head>
<body>
<header>
<h1>{title}</h1>
<p class="subtitle">{subtitle}</p>
</header>
<article>
{body_html}
</article>
</body>
</html>"""


def ensure_profile(data, child_name):
    if child_name not in data["profiles"]:
        data["profiles"][child_name] = {"created_at": datetime.utcnow().isoformat()}


def main():
    st.set_page_config(page_title="Once Upon", page_icon="📚", layout="wide")
    st.title("📚 Once Upon")
    st.caption("AI-Powered Personalized Children's Storytelling App (MVP)")

    data = get_app_data()

    tab_create, tab_library, tab_dashboard = st.tabs(
        ["Create Story", "Child Story Library", "Parent Dashboard"]
    )

    with st.sidebar:
        st.header("Generation")
        gen_mode = st.radio(
            "Story source",
            ["Local template", "OpenAI"],
            horizontal=True,
        )
        openai_model = DEFAULT_OPENAI_MODEL
        openai_key_input = ""
        if gen_mode == "OpenAI":
            openai_model = st.text_input(
                "OpenAI model",
                value=DEFAULT_OPENAI_MODEL,
                help="e.g. gpt-4o-mini, gpt-4o",
            )
            key_from_env = bool(resolve_openai_key(None))
            openai_key_input = st.text_input(
                "OpenAI API key",
                type="password",
                value="",
                help="Optional if OPENAI_API_KEY is set in environment or Streamlit secrets.",
                disabled=key_from_env,
            )
            if key_from_env:
                st.caption("Using OPENAI_API_KEY from secrets or environment.")

    with tab_create:
        st.subheader("Story Parameter Builder")
        col1, col2 = st.columns(2)
        with col1:
            child_name = st.text_input("Child name", placeholder="e.g. Emma")
            age_range = st.selectbox("Age range", ["3-5", "6-8", "9-12"])
            protagonist = st.text_input("Main character name", placeholder="e.g. Luna the Fox")
            traits = st.text_input("Personality traits", placeholder="e.g. curious, brave")
        with col2:
            setting = st.text_input("Setting", placeholder="e.g. Whispering Forest")
            theme = st.text_input("Theme", placeholder="e.g. friendship")
            moral = st.text_input("Moral lesson", placeholder="e.g. honesty builds trust")

        if st.button("Generate Story", type="primary"):
            missing = [
                name
                for name, value in {
                    "child_name": child_name,
                    "protagonist": protagonist,
                    "traits": traits,
                    "setting": setting,
                    "theme": theme,
                    "moral": moral,
                }.items()
                if not value.strip()
            ]
            if missing:
                st.error(f"Please fill all fields. Missing: {', '.join(missing)}")
            else:
                params = {
                    "child_name": child_name.strip(),
                    "age_range": age_range,
                    "protagonist": protagonist.strip(),
                    "traits": traits.strip(),
                    "setting": setting.strip(),
                    "theme": theme.strip(),
                    "moral": moral.strip(),
                    "generation": gen_mode,
                }
                try:
                    if gen_mode == "OpenAI":
                        api_key = resolve_openai_key(openai_key_input or None)
                        if not api_key:
                            st.error(
                                "OpenAI selected but no API key found. "
                                "Set OPENAI_API_KEY in Streamlit secrets or environment, or paste a key above."
                            )
                            st.stop()
                        model = (openai_model or DEFAULT_OPENAI_MODEL).strip() or DEFAULT_OPENAI_MODEL
                        with st.spinner("Generating with OpenAI…"):
                            story_text, scenes = generate_story_openai(api_key, params, model)
                        params["openai_model"] = model
                    else:
                        story_text = generate_story_template(params)
                        scenes = scene_descriptions(params)
                except Exception as e:
                    st.error(f"Generation failed: {e}")
                    st.stop()

                ensure_profile(data, params["child_name"])
                data["stories"].append(
                    {
                        "timestamp": datetime.utcnow().isoformat(),
                        "params": params,
                        "story": story_text,
                        "scene_descriptions": scenes,
                    }
                )
                save_data(data)

                st.success("Story generated and saved.")
                st.markdown(story_text)
                st.markdown("### Illustrated Chapter Breaks (Scene Prompts)")
                for scene in scenes:
                    st.write(f"- {scene}")

    with tab_library:
        st.subheader("Saved Stories by Child")
        child_names = sorted(data["profiles"].keys())
        if not child_names:
            st.info("No child profiles yet. Generate your first story in the Create Story tab.")
        else:
            selected_child = st.selectbox("Select child profile", child_names)
            child_stories = [
                s for s in reversed(data["stories"]) if s["params"]["child_name"] == selected_child
            ]
            if not child_stories:
                st.info("No stories yet for this child.")
            else:
                for idx, item in enumerate(child_stories, start=1):
                    with st.expander(f"Story #{idx} — {item['timestamp']}"):
                        st.write(
                            f"Theme: {item['params']['theme']} | Setting: {item['params']['setting']} | Age: {item['params']['age_range']}"
                        )
                        st.markdown(item["story"])
                        st.markdown("**Scene prompts:**")
                        for scene in item.get("scene_descriptions") or []:
                            st.write(f"- {scene}")

                        st.markdown("---")
                        st.markdown("**Illustrations**")
                        st.caption(
                            "Add one image per chapter (Introduction, Challenge, Resolution). "
                            "They are woven into the exported storybook below the matching section."
                        )
                        stored = normalize_illustrations(item)
                        new_imgs: list = []
                        cols = st.columns(3)
                        for i in range(3):
                            with cols[i]:
                                label = f"Chapter {i + 1}"
                                up = st.file_uploader(
                                    label,
                                    type=["png", "jpg", "jpeg", "webp"],
                                    key=f"illu_{item['timestamp']}_{i}",
                                    help="Optional image for this chapter",
                                )
                                if up is not None:
                                    new_imgs.append(
                                        {
                                            "mime": up.type or "image/png",
                                            "b64": base64.b64encode(up.getvalue()).decode("ascii"),
                                        }
                                    )
                                else:
                                    new_imgs.append(stored[i])

                        if new_imgs != stored:
                            item["illustration_images"] = new_imgs
                            save_data(data)

                        thumbs = normalize_illustrations(item)
                        if any(thumbs):
                            st.caption("Preview")
                            pc = st.columns(3)
                            for i in range(3):
                                if thumbs[i]:
                                    with pc[i]:
                                        st.image(
                                            base64.b64decode(thumbs[i]["b64"]),
                                            caption=f"Chapter {i + 1}",
                                            use_container_width=True,
                                        )

                        st.markdown("**Complete storybook**")
                        st.caption(
                            "Download a single HTML file: story text plus images in reading order. "
                            "Open in a browser; use Print → Save as PDF if you want a PDF."
                        )
                        html_doc = build_storybook_html(item)
                        safe_ts = re.sub(r"[^\w\-]+", "_", item["timestamp"])[:32]
                        st.download_button(
                            "Download storybook (HTML)",
                            data=html_doc.encode("utf-8"),
                            file_name=f"once_upon_storybook_{safe_ts}.html",
                            mime="text/html",
                            key=f"dl_{item['timestamp']}",
                        )

    with tab_dashboard:
        st.subheader("Parent Dashboard")
        total_stories = len(data["stories"])
        total_children = len(data["profiles"])
        st.metric("Total stories generated", total_stories)
        st.metric("Child profiles", total_children)

        if total_stories > 0:
            st.markdown("### Recent activity")
            for item in list(reversed(data["stories"]))[:10]:
                p = item["params"]
                st.write(
                    f"{item['timestamp']} — {p['child_name']} | {p['theme']} | {p['setting']} | Moral: {p['moral']}"
                )

    st.divider()
    st.caption(
        "Use the sidebar to choose Local template or OpenAI. "
        "For deployment, set OPENAI_API_KEY in Streamlit Cloud → App settings → Secrets."
    )


if __name__ == "__main__":
    main()
