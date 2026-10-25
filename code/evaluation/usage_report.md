# Model Usage Report — Ghost Data Still Exists
**HackerRank Orchestrate (October 2026)**  
**Challenge:** Ghost Data Still Exists — AI-Powered Deletion Audit Agent  
**Date:** October 2026  
**Evaluation Mode:** Final Full-Dataset Production Run (`dataset/deletion_requests.csv` -> `output.csv`)  

---

## 1. Executive Summary

This report documents the runtime model consumption, token counts, and API costs incurred during the final execution of the deletion audit agent over all 518 evaluation requests in `dataset/deletion_requests.csv`.

To ensure 100% determinism, eliminate latency and hallucination risks, maintain complete data privacy, and ensure predictable evaluation reproducibility, the solution employs a **pure deterministic architecture**. All entity recognition, document extraction, replica querying, identity resolution, policy evaluation, timeline reconstruction, and JSON serialization are executed using native, deterministic Python modules (`sqlite3`, `json`, `re`, `zlib`, `base64`, `csv`).

Consequently, **zero external model API calls** were made during the generation of the final 518-case `output.csv`.

---

## 2. Quantitative Model Usage Breakdown

| Metric | Recorded Value | Notes |
| :--- | :--- | :--- |
| **Model Provider(s)** | None (`N/A`) | Fully self-contained deterministic system |
| **Model Identifier(s)** | Pure Deterministic Engine | No external LLM inference relied upon |
| **Total Model API Calls** | **0** | Zero remote or local model calls |
| **Total Input Tokens** | **0** | No prompt tokens processed |
| **Total Output Tokens** | **0** | No generation tokens produced |
| **Total Tokens** | **0** | Exact total |
| **Average Input Tokens / Request** | **0.00** | Across all 518 requests |
| **Average Output Tokens / Request** | **0.00** | Across all 518 requests |
| **Average Total Tokens / Request** | **0.00** | Across all 518 requests |
| **Estimated Total Model Cost (USD)** | **$0.00** | Pure Python standard library execution |
| **Estimated Cost Per Request (USD)** | **$0.00** | Pure Python standard library execution |

---

## 3. Per-Model Detail Breakdown

| Model Provider | Model Name | Call Count | Input Tokens | Output Tokens | Total Tokens | Estimated Cost (USD) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| N/A (Standard Library) | `code/main.py` | 0 | 0 | 0 | 0 | $0.00 |
| **Total** | | **0** | **0** | **0** | **0** | **$0.00** |

---

## 4. Hardware and Computational Resource Profile

The entire 518-case audit was benchmarked on standard local CPU compute:
- **Total Pipeline Execution Time:** ~5.2 seconds for all 518 cases (average ~10.0 ms per case).
- **Peak Memory Footprint:** < 120 MB RAM (including full in-memory SQLite replicas and parsed JSON/log manifests).
- **Network Calls:** 0 (strictly zero external network dependencies).
- **Environment Compatibility:** Python 3.10+ on Windows, Linux, and macOS.
