---
name: brainstorming
description: "Use this skill before any creative activity — creating features, components, adding functionality, or modifying behavior. Explore the user's intent, requirements, and design before implementation."
---

# Brainstorming: From Ideas to Design

## Process

**Understanding the idea:**
- First check the current state of the project (files, documents, recent commits)
- Ask questions one at a time using the **AskUserQuestion** tool to refine the idea
- Prefer questions with answer options (using the `options` parameter in AskUserQuestion) when possible, but open questions are also fine
- One question per message — if a topic needs more exploration, split it into multiple questions
- Focus on understanding: purpose, constraints, success criteria

**Exploring approaches:**
- Propose 2-3 different approaches with pros and cons
- Present options using **AskUserQuestion** with `options` for each approach, including advantages in `description`
- Start with the recommended option and explain why

**Presenting the design:**
- Once you believe you understand what is being built, present the design
- Break it into sections of 200-300 words
- After each section, use **AskUserQuestion** to ask if everything looks good
- Cover: architecture, components, data flow, error handling, testing
- Be prepared to go back and clarify if something does not make sense

## After Design

**Documentation:**
- Write the validated design to `docs/plans/YYYY-MM-DD-<topic>-design.md`
- Commit the design document to git

**Implementation (if continuing):**
- Ask: "Are you ready to prepare the implementation?"
- Create a detailed implementation plan before writing any code

## Key Principles

- **One question at a time** — Do not overwhelm with multiple questions
- **Prefer answer options** — Easier to respond to than open questions, when possible
- **YAGNI** — Ruthlessly eliminate unnecessary features from all designs
- **Explore alternatives** — Always propose 2-3 approaches before deciding
- **Incremental validation** — Present the design in sections, validate each one
- **Be flexible** — Go back and clarify if something does not make sense
