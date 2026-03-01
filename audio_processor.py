import os
import io
import math
import time
import logging
from pydub import AudioSegment
from pydub.silence import split_on_silence
from ai_reasoning import transcribe_audio, analyze_threat
from incident_manager import IncidentManager

# Set up our observability (latency logging)
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s', datefmt='%H:%M:%S')
logger = logging.getLogger(__name__)

class AudioTurn:
    """A data class to hold our segmented audio and its extracted signals."""
    def __init__(self, turn_id: int, buffer: io.BytesIO, avg_dbfs: float, duration_sec: float, peak_dbfs: float):
        self.turn_id = turn_id
        self.buffer = buffer
        self.duration_sec = duration_sec
        self.peak_dbfs = peak_dbfs
        self.avg_dbfs = avg_dbfs
        
        # Simple deterministic heuristic: 
        # -20 dBFS is roughly normal conversation. Above -3 dBFS is very loud/shouting.
        self.is_loud = peak_dbfs > -3.0

def process_audio_file(file_path: str) -> list[AudioTurn]:
    """
    Simulates ingesting audio by splitting a WAV file on silence.
    Extracts deterministic audio signals (duration, loudness).
    """
    start_time = time.perf_counter()
    logger.info(f"Ingesting audio file: {file_path}")
    
    # FAIL-SAFE 1: Pre-flight file check
    if not os.path.exists(file_path):
        logger.error(f"FAIL-SAFE: Audio file not found at {file_path}")
        return []

    try:
        # Load the audio file
        audio = AudioSegment.from_wav(file_path)
    except Exception as e:
        logger.error(f"FAIL-SAFE: Failed to decode audio {file_path}. It may be corrupted: {e}")
        return []

    logger.info("Running Voice Activity Detection (VAD) segmentation...")
    chunks = split_on_silence(
        audio,
        min_silence_len=500,
        silence_thresh=-40,
        keep_silence=200
    )

    turns = []
    valid_turn_id = 0 # Track valid turns separately from chunk index
    
    for i, chunk in enumerate(chunks):
        duration = len(chunk) / 1000.0
        
        # FAIL-SAFE 2: Drop micro-chunks that will crash Whisper or waste money
        if duration < 0.5:
            logger.debug(f"FAIL-SAFE: Skipping chunk {i} - too short ({duration}s)")
            continue

        # FAIL-SAFE 3: Prevent absolute silence from returning negative infinity (-inf)
        peak_volume = chunk.max_dBFS
        avg_volume = chunk.dBFS
        if math.isinf(peak_volume):
            peak_volume = -100.0
        if math.isinf(avg_volume):
            avg_volume = -100.0
        
        # Export to an IN-MEMORY buffer
        try:
            buffer = io.BytesIO()
            buffer.name = f"turn_{valid_turn_id}.wav"
            chunk.export(buffer, format="wav")
            buffer.seek(0)
        except Exception as e:
            logger.error(f"FAIL-SAFE: Could not export chunk {i} to memory buffer: {e}")
            continue
        
        turn = AudioTurn(
            turn_id=valid_turn_id, 
            buffer=buffer, 
            duration_sec=duration, 
            peak_dbfs=peak_volume, 
            avg_dbfs=avg_volume
        )
        turns.append(turn)
        
        logger.info(f"Segmented Turn {valid_turn_id:03d} | Duration: {duration:.2f}s | Peak Vol: {peak_volume:.2f} dBFS | Loud: {turn.is_loud}")
        valid_turn_id += 1

    vad_latency = time.perf_counter() - start_time
    logger.info(f"VAD & Ingestion Complete. Extracted {len(turns)} valid turns. (Latency: {vad_latency:.2f}s)")
    
    return turns

# Quick test sandbox
if __name__ == "__main__":
    test_file = "audio_files/heated_argument.wav" 
    turns = process_audio_file(test_file)
    
    # Initialize the manager
    manager = IncidentManager(cooldown_seconds=30)
    
    for turn in turns:
        print(f"\n--- Processing Turn {turn.turn_id} ---")
        transcript = transcribe_audio(turn.buffer)
        
        # FAIL-SAFE 4: Fixed argument order (avg_dbfs, then is_loud)
        decision = analyze_threat(transcript, turn.peak_dbfs, turn.avg_dbfs, turn.is_loud)
        
        # Check incident status
        incident_status = manager.should_fire_alert(decision.is_threat)
        
        if incident_status:
            manager.publish_alert(turn.turn_id, transcript, decision, incident_status)
        else:
            print("System Monitoring: No threat detected.")