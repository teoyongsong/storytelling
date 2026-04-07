import json
import os
from datetime import datetime
from pathlib import Path

import streamlit as st


DATA_FILE = Path("stories.json")


def load_data():
    if not DATA_FILE.exists():
        return {"profiles": {}, "stories": []}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def generate_story(params):
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


def scene_descriptions(params):
    return [
        f"Chapter 1 illustration: {params['protagonist']} and {params['child_name']} arriving at {params['setting']} at sunset.",
        f"Chapter 2 illustration: a tense moment around the theme of {params['theme']}, with expressive emotions.",
        f"Chapter 3 illustration: joyful resolution scene in {params['setting']} with warm lighting.",
    ]


def ensure_profile(data, child_name):
    if child_name not in data["profiles"]:
        data["profiles"][child_name] = {"created_at": datetime.utcnow().isoformat()}


def main():
    st.set_page_config(page_title="Once Upon", page_icon="📚", layout="wide")
    st.title("📚 Once Upon")
    st.caption("AI-Powered Personalized Children's Storytelling App (MVP)")

    data = load_data()

    tab_create, tab_library, tab_dashboard = st.tabs(
        ["Create Story", "Child Story Library", "Parent Dashboard"]
    )

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
                }
                story_text = generate_story(params)
                scenes = scene_descriptions(params)

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
                        for scene in item["scene_descriptions"]:
                            st.write(f"- {scene}")

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
        "Note: This MVP uses a local template generator. Replace generate_story() with an LLM API call for fully dynamic story generation."
    )


if __name__ == "__main__":
    main()
