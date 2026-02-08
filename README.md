# SWE-bench Hackathon Entry — OpenLibrary Import Logic

This repository contains my solution for the **SWE-bench Verified** task: `internetarchive__openlibrary-c4eebe66`.

The task focuses on improving OpenLibrary’s import logic by avoiding unnecessary external API calls when relevant records already exist locally.

## 🎯 Problem Statement

### 🔴 Issue
OpenLibrary was making external API calls even when book records were already present locally with a `staged` or `pending` status.

### 📉 Why this matters
* **Unnecessary network calls:** Slows down the import pipeline.
* **Increased latency:** Users wait longer for imports.
* **Wasted compute resources:** Processing data that already exists.

### 🎯 Goal
Refactor `openlibrary/core/imports.py` so the system first checks local staged or pending records using a precise database query before triggering external requests.

---

## 🤖 The Solution — Self-Healing AI Agent
I built a custom AI Agent powered by **Claude 3.5 Haiku** (Anthropic API) to automatically generate and validate the fix.



### 📐 Architecture
```mermaid
graph TD
    A[Start Workflow] --> B[Setup Environment]
    B --> C{Attempt AI Fix}
    C -->|Claude 3.5 Haiku| D[Generate Code]
    D --> E{Smart Validation}
    E -->|Passes Logic Check| F[Apply AI Fix]
    E -->|Fails Logic Check| G[Trigger Fail-Safe]
    C -->|API Error| G
    G -->|Apply Manual Patch| H[Apply Deterministic Fix]
    F --> I[Run Tests]
    H --> I
    I --> J{Result}
    J -->|Green| K[Success ✅]