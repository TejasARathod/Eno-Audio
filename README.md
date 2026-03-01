# eNO Wearable Safety Badge: AI Threat Detection Pipeline

## 📖 Project Description
This repository contains the software pipeline for the audio processing assessment task. It calculates deterministic acoustic physics (Peak and Average dBFS) and fuses that data with a 3-turn rolling conversational memory buffer. A Large Language Model (GPT-4o-mini) then analyzes both the acoustic signals and semantic context to detect threats, instantly publishing emergency alerts to a local ARC Operator dashboard.

---

## 🚀 How to Run

### 1️⃣ Clone the repository

```bash
git clone https://github.com/TejasARathod/Eno-Audio.git
cd Eno-Audio
```

### 2️⃣ Set up your environment variables

Create a `.env` file in the root directory of the project and add your OpenAI API key:

```bash
echo "OPENAI_API_KEY=your_actual_api_key_here" > .env
```

### 3️⃣ Build and run the pipeline

The entire application is containerized. To spin up the Redis message broker and the AI pipeline, simply run:

```bash
docker compose up --build
```

### 4️⃣ View the results

The pipeline will automatically process the test audio corpus. You will see:

- Turn-by-turn AI analysis  
- Simulated ARC operator alerts  
- A final Runtime Performance Summary table  

All output is printed directly in your terminal.

## 📄 Workflow Documentation

For a detailed breakdown of the system architecture, development process, and production safeguards, please refer to the full workflow document:

👉 **[Read the Workflow Documentation](https://github.com/TejasARathod/Eno-Audio/blob/502615f543d8fb7905279a41195e461186b8bb92/workflow.md)**

This document explains the end-to-end pipeline logic, system modules, optimization decisions, and future architectural improvements.

## 📂 Generated Output Files

When the project directory is executed (`docker compose up --build`), the following files are automatically generated:

- **`api_cache.json`**  

- **`redis_final_alerts.log`**  

These files allow you to inspect the AI reasoning outputs and dispatched alerts independently after the pipeline finishes running.
