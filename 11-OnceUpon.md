# 11 · Once Upon
**AI-Powered Personalised Children's Storytelling App**

---

## Problem Statement

Parents and educators struggle to find bedtime stories that are both personalised to a child's interests and age-appropriate. Generic story libraries are static and quickly exhaust a child's attention. Creating custom stories manually is time-consuming and creatively demanding for most adults.

---

## Research-Backed Implementation

Inspired by the University of Chicago Applied Data Science capstone project of the same name, students build a system that allows children or parents to customise story characters, themes, settings, and moral lessons. The LLM generates a unique, structured story on demand. The UChicago project demonstrated that AI-generated personalised stories significantly increased child engagement compared to static story libraries.

---

## Solution Overview

Users select or describe a set of story parameters — character names, personality traits, story setting, theme, and a moral lesson. The app assembles these inputs into a structured generation prompt and produces a complete, age-appropriate story with a clear narrative arc: introduction, challenge, resolution, and moral. Stories are saved per child profile so parents can revisit them. A parent dashboard logs all generated stories for review.

---

## Key Features

- Story parameter builder: character names, traits, setting, theme, and moral lesson
- Age-range selector that adjusts vocabulary, length, and complexity
- Structured story output with clear narrative arc (introduction, challenge, resolution, moral)
- Illustrated chapter breaks using AI-generated scene descriptions
- Save and replay: story library persisted per child profile
- Parent dashboard to review all generated stories for that account
- Read-aloud mode with text highlighted sentence by sentence

---

## Difficulty

🟢 **Beginner** — constrained input → structured generative output with persistent story library. The main challenge is prompt engineering for consistent story quality and age-appropriate tone.

---

## Domain

Education / Children's Technology
