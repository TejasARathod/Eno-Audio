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
