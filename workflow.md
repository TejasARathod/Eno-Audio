# 📄 Project Assignment: eNO Safety Badge AI Pipeline

## Executive Summary

This V1 prototype represents a modular, containerized AI safety pipeline designed for low-latency threat detection. Its core objective is to transform raw environmental audio into deterministic emergency alerts using a cascaded logic of:

- **Physics** (loudness thresholds)  
- **Acoustics** (Voice Activity Detection)  
- **Semantics** (Large Language Model reasoning)

By balancing strict data privacy with edge-cloud analysis, the pipeline effectively serves both the **Wearer** and the **Emergency Operator**.

---

# 1️⃣ Project Development Journey

To maintain a professional workflow, the project simulated an industry-standard Agile development cycle from discovery to final testing.

## Day 1: Architecture & Logic

| Time | Task |
|------|------|
| 11:00 AM – 12:00 PM | Problem analysis and requirement gathering |
| 12:00 PM – 1:00 PM | Built functional end-to-end base architecture using Gemini |
| 1:00 PM – 2:30 PM | Lunch break |
| 2:30 PM – 4:00 PM | Code review and API parameter documentation check |
| 4:00 PM – 4:30 PM | Short break |
| 4:30 PM – 6:00 PM | Refined individual pipeline components |
| 6:00 PM – 6:30 PM | Short break |
| 6:30 PM – 8:00 PM | Finalized reasoning logic and implemented production safety checks |

## Day 2: Refinement & Submission

| Time | Task |
|------|------|
| 8:30 AM – 10:00 AM | R&D for architecture improvements and future work |
| 10:00 AM – 12:00 PM | Final documentation and submission testing |

---

# 2️⃣ System Workflow

The pipeline orchestrates five modular components that manage the lifecycle from raw audio to dispatch dashboard.

### 🎧 Ingestion (`audio_processor.py`)
- Uses Voice Activity Detection (VAD) to strip silence and segment speech.
- Evaluates shouting based on Peak dBFS threshold.
- Keeps audio strictly in RAM to ensure user privacy.

### 🧠 Analysis (`ai_reasoning.py`)
- Transcribes audio via Whisper.
- Performs threat reasoning via GPT-4o-mini.
- Uses `temperature=0.0` for deterministic outputs.
- Enforces structured JSON via Pydantic schema validation.

### ⚡ State Management (`incident_manager.py`)
- Groups related threats into a single `incident_id`.
- Uses a 30-second cooldown to prevent alert spam.

### 📡 Communication (`subscriber.py` & `main.py`)
- Broadcasts alerts via Redis Pub/Sub.
- Simulates a remote dispatch center.
- `main.py` orchestrates chronological data flow.

### 🐳 Infrastructure (Docker)
- Containerizes Python environment and dependencies (including ffmpeg).
- Isolates Redis database.
- Ensures cross-platform reliability and rapid deployment.

---

# 3️⃣ Data Processing, Threshold and Reasoning Optimization

During early testing, the system acted as an overly sensitive "Safety First" monitor, flagging nearly every audio sample.

## Domain-Driven Thresholding
- Initial loudness threshold: **-10.0 dBFS** → Too sensitive.
- Optimized threshold: **-3.0 dBFS** → Targets near-clipping distress sounds.

## Acoustic Feature Integration
- Added **RMS (Root Mean Square)** alongside Peak dBFS.
- Differentiates sudden noise spikes from sustained vocal intensity.

## Noise & Smoothing Tests
- Smoothed audio improved transcription clarity.
- Raw audio better preserved authentic “shouting” cues for LLM reasoning.

## Prompt Reasoning Refinements
- Implemented a strict "Evaluation Matrix" that forces the LLM to continuously cross-reference acoustic metrics
- Categorized case scenarios for better understanding.

### Insight
By tuning dBFS gating and integrating RMS, the system transitioned from overly reactive to highly surgical — significantly reducing false positives while maintaining safety integrity.

---

# 4️⃣ Production Fail-Safes

To ensure reliability under messy real-world conditions, multiple safeguards were engineered.

## 🔒 Audio & Data Integrity
- File and buffer validation.
- Acoustic clamping for `-inf` silence values.
- Automatic filtering of micro-chunks (< 0.1 seconds).

## 🌐 API & Environment Security
- Proactive OpenAI API key verification.
- Redis `.ping()` test with socket timeout.
- Corrupt cache recovery for `api_cache.json`.
- Graceful handling of OpenAI policy refusals.

## 🛡 Code Robustness
- Safe object extraction via `getattr`.
- Specific exception catching (no bare `except`).
- Timezone-aware UTC standardization.

---

# 5️⃣ Multi-Perspective Context Integration

Evaluating the system from both the Wearer’s and Operator’s perspectives revealed a shared critical gap: **Context**.

## Wearer’s Gap
Single-sentence analysis fails to capture escalating behavior patterns.

## Operator’s Gap
Isolated transcripts lack conversational lead-up required for confident dispatch decisions.

## Solution: 3-Turn Rolling Memory Buffer
- Stored strictly in RAM.
- Enables recognition of mounting threats.
- Provides a structured multi-turn timeline to operators.

---

# 6️⃣ Future Architecture Improvements

To evolve into a production-ready Edge AI wearable, the following upgrades are recommended:

### 🔄 Dynamic Memory Buffer Sizing
- RL-based adaptive sliding window.
- Expands during chaotic scenarios.
- Shrinks during calm periods to reduce API costs. [1]

### 🔋 Energy-Aware Degradation
- Battery-saving mode below 15%.
- Prioritizes critical SOS alerts over conversational memory. [1]

### 🧠 Black-Box Knowledge Distillation
- Train a tiny offline student model.
- Use cached GPT-4o-mini decisions.
- Reduce cloud dependency and subscription costs. [2]

### 🎛 DSP-Level Event-Gated Wake-Up
- Replace simple volume threshold.
- Use ultra-low-power DSP for distress pattern detection.
- Preserve battery without missing quiet emergencies. [3]

---

# 7️⃣ Personal Reflections & Limitations

## Hardware & Fine-Tuning
- Transition to GPU processing.
- Deeper parameter fine-tuning for real-time optimization.

## Architecture Upgrades
- Replace cloud API with local AudioLLM.
- Preferred candidate: NVIDIA Audio Flamingo 2 (Triton + Docker optimized).

## Data Scarcity
- Requires large-scale real-world threat datasets for robust stress testing.

## Domain Knowledge Constraints
- Limited deep acoustic physics expertise.
- Reverberant rooms and overlapping speech remain major V1 limitations.

---

# 📚 References

[1] Zarghani, A., & Abedi, S. (2025). *Designing Adaptive Algorithms Based on Reinforcement Learning for Dynamic Optimization of Sliding Window Size in Multi-Dimensional Data Streams.* arXiv:2507.06901.

[2] Kausar, F., et al. (2026). *Integrating Multi-Agent Simulation, Behavioral Forensics, and Trust-Aware Machine Learning for Adaptive Insider Threat Detection.* arXiv:2601.04243.

[3] Torkamani, M. J., & Zarin, I. (2025). *Adaptive Edge-Cloud Inference for Speech-to-Action Systems Using ASR and Large Language Models.* arXiv:2512.12769.
