import os
import json
import time
import hashlib
import logging
from io import BytesIO
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field

# Load the API key from the .env file
load_dotenv()

logger = logging.getLogger(__name__)

# FAIL-SAFE 1: Pre-flight check for API Key
if not os.getenv("OPENAI_API_KEY"):
    logger.error("FAIL-SAFE: OPENAI_API_KEY is missing! API calls will fail.")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- 💾 CACHE CONFIGURATION ---
USE_CACHE = True
CACHE_FILE = "api_cache.json"

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.warning("FAIL-SAFE: api_cache.json is corrupted. Rebuilding a fresh cache.")
            return {"whisper": {}, "llm": {}}
    return {"whisper": {}, "llm": {}}

def save_cache(cache_data):
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(cache_data, f, indent=4)
    except Exception as e:
        logger.error(f"FAIL-SAFE: Failed to save cache to disk: {e}")

api_cache = load_cache()

# --- THE STRUCTURED OUTPUT SCHEMA ---
class AlertDecision(BaseModel):
    is_threat: bool = Field(description="True if the combined audio and text signals indicate a safety threat.")
    threat_category: str = Field(description="Categorize the threat (e.g., 'physical_violence', 'verbal_harassment', 'distress_call', 'none').")
    confidence_score: float = Field(description="Confidence in this assessment between 0.0 and 1.0.")
    reasoning: str = Field(description="A short explanation of WHY this decision was made, referencing the words, volume, and previous context.")

def transcribe_audio(audio_buffer: BytesIO) -> str:
    """Sends the in-memory audio chunk to OpenAI Whisper for transcription."""
    audio_bytes = audio_buffer.getvalue()
    
    if not audio_bytes or len(audio_bytes) == 0:
        logger.error("FAIL-SAFE: Received an empty audio buffer. Skipping transcription.")
        return ""

    cache_key = hashlib.md5(audio_bytes).hexdigest()
    if USE_CACHE and cache_key in api_cache["whisper"]:
        logger.info("🎙️ [CACHE HIT] Loaded Whisper transcript instantly.")
        return api_cache["whisper"][cache_key]

    start_time = time.perf_counter()
    try:
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_buffer,
            temperature=0.0
        )
        transcript = response.text.strip()
    except Exception as e:
        logger.error(f"Whisper API failed: {e}")
        transcript = ""
        
    latency = time.perf_counter() - start_time
    logger.info(f"Transcription Complete | Latency: {latency:.2f}s | Text: '{transcript}'")
    
    if USE_CACHE and transcript:
        api_cache["whisper"][cache_key] = transcript
        save_cache(api_cache)

    return transcript

# NEW: Added conversation_history parameter for the rolling buffer (THIS IS THE 5TH ARGUMENT!)
def analyze_threat(transcript: str, peak_dbfs: float, avg_dbfs: float, is_loud: bool, conversation_history: list = None) -> AlertDecision:
    """Fuses text, acoustic signals, and historical context to make a decision."""
    
    if conversation_history is None:
        conversation_history = []
        
    if len(transcript) < 2:
        logger.info("Transcript too short. Skipping LLM analysis.")
        return AlertDecision(is_threat=False, threat_category="none", confidence_score=1.0, reasoning="No coherent speech detected.")

    # --- CACHE CHECK (Now includes history so context changes the cache key!) ---
    history_str = " | ".join(conversation_history)
    cache_key = f"{transcript}|{peak_dbfs:.2f}|{avg_dbfs:.2f}|{is_loud}|{history_str}"
    
    if USE_CACHE and cache_key in api_cache["llm"]:
        logger.info("🧠 [CACHE HIT] Loaded LLM reasoning instantly.")
        return AlertDecision(**api_cache["llm"][cache_key])
    # -------------------

    start_time = time.perf_counter()
    
    # --- NEW UPGRADED SYSTEM PROMPT ---
    system_prompt = (
        "You are the reasoning engine for a real-time personal safety wearable. "
        "Analyze the current transcript, the recent conversation history, and the acoustic volume metrics to decide if an emergency alert is required.\n\n"
        "EVALUATION MATRIX:\n"
        "1. CRITICAL THREAT (High Alert): Explicit threats of harm, attack, or distress. Even if the volume is LOW (e.g., a whispered threat), flag it immediately. Also flag high volume combined with extreme/aggressive words.\n"
        "2. CAUTIONARY ESCALATION: High volume and high average volume combined with suspicious or argumentative words. Look at the Conversation History to see if an argument is escalating toward verbal harassment or a physical brawl.\n"
        "3. SAFE (Ignore): Low volume with casual, funny, sad, or standard environmental noise. Also ignore high peak volume if the words indicate non-threatening excitement (e.g., TV sports, laughing, jokes).\n\n"
        "Err on the side of caution for direct threats, but do not trigger alerts for casual arguments that show no signs of violence."
    )
    
    # Format the history for the LLM to read
    formatted_history = "\n".join([f"- Past Turn: '{text}'" for text in conversation_history])
    if not formatted_history:
        formatted_history = "None (Start of conversation)"
    
    user_prompt = (
        f"Conversation History (Oldest to Newest):\n{formatted_history}\n\n"
        f"Current Transcript to Analyze: '{transcript}'\n"
        f"Current Audio Signals:\n"
        f"- Peak Volume: {peak_dbfs:.2f} dBFS\n"
        f"- Average Volume (RMS): {avg_dbfs:.2f} dBFS\n"
        f"- Loudness Threshold Triggered: {is_loud}"
    )

    try:
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0,
            response_format=AlertDecision,
        )
        
        if completion.choices[0].message.refusal:
            logger.warning(f"FAIL-SAFE: OpenAI refused the prompt due to policy: {completion.choices[0].message.refusal}")
            decision = AlertDecision(is_threat=False, threat_category="error", confidence_score=0.0, reasoning="API Safety Refusal.")
        else:
            decision = completion.choices[0].message.parsed
            
    except Exception as e:
        logger.error(f"LLM Reasoning failed: {e}")
        decision = AlertDecision(is_threat=False, threat_category="error", confidence_score=0.0, reasoning="API Error.")

    latency = time.perf_counter() - start_time
    logger.info(f"Threat Analysis Complete | Latency: {latency:.2f}s | Threat: {decision.is_threat}")
    
    if USE_CACHE and decision.threat_category != "error":
        api_cache["llm"][cache_key] = decision.model_dump()
        save_cache(api_cache)

    return decision
