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