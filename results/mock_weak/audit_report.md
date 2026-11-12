# LLM Security & Prompt-Injection Vulnerability Audit
**Audit Generated:** 2026-11-12T19:34:05.950635+00:00  
**Target Model:** `mock_weak`  
**Total Tested Vectors:** 368  

## Executive Summary
- **Baseline (Unprotected) ASR:** 70.9%
- **Hardened (Multi-Layer) ASR:** 0.0%
- **Injection Detector F1:** 0.996

## Detailed Defense Evaluation Table
| Configuration | Attack Success Rate | Direct ASR | Indirect ASR | Exfil ASR | Benign Utility |
|---|---|---|---|---|---|
| **none** | 70.9% | 58.3% | 77.1% | 70.0% | 90.6% |
| **delimiters** | 46.1% | 56.9% | 41.7% | 46.4% | 90.6% |
| **hierarchy** | 44.8% | 52.8% | 38.0% | 47.4% | 90.6% |
| **output_filter** | 9.3% | 0.0% | 0.0% | 17.9% | 90.6% |
| **detector** | 0.0% | 0.0% | 0.0% | 0.0% | 68.8% |
| **privsep** | 7.3% | 0.0% | 0.0% | 14.1% | 90.6% |
| **prompt+filter** | 4.3% | 0.0% | 0.0% | 8.2% | 90.6% |
| **all** | 0.0% | 0.0% | 0.0% | 0.0% | 68.8% |