import argparse
import sys
import logging
import time
import tracemalloc
from audio_processor import process_audio_file
from ai_reasoning import transcribe_audio, analyze_threat
from incident_manager import IncidentManager

# Set up clean logging for the demo
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def run_pipeline(file_path):
    print(f"\n🚀 STARTING SAFETY PIPELINE FOR: {file_path}")
    print("-" * 50)
    
    # Start tracking memory and time
    tracemalloc.start()
    start_time = time.perf_counter()
    
    # Initialize Incident Manager (30s cooldown for testing)
    manager = IncidentManager(cooldown_seconds=30)
    
    # 1. Ingestion & VAD
    turns = process_audio_file(file_path)
    if not turns:
        print("No speech detected or file error.")
        tracemalloc.stop()
        return None

    # NEW: Rolling Memory Buffer setup
    conversation_history = []
    MAX_HISTORY = 3  # How many previous turns the AI should remember

    # 2. Sequential Processing (Simulating real-time arrival)
    for turn in turns:
        print(f"\n[Turn {turn.turn_id} | Vol: {turn.peak_dbfs:.1f} dBFS]")
        
        # Transcription
        transcript = transcribe_audio(turn.buffer)
        if not transcript:
            continue

        # AI Reasoning (NEW: Pass the history in)
        decision = analyze_threat(transcript, turn.peak_dbfs, turn.avg_dbfs, turn.is_loud, conversation_history)
        
        # Incident Logic
        incident_status = manager.should_fire_alert(decision.is_threat)
        
        if incident_status:
            # NEW: Pass the history to the operator alert
            manager.publish_alert(turn.turn_id, transcript, decision, incident_status, conversation_history)
        else:
            print(f"✅ Monitoring... (Confidence: {decision.confidence_score:.2f})")

        # NEW: Update the rolling buffer AFTER the analysis
        # (We append it after so the current turn isn't duplicated in the "history")
        conversation_history.append(transcript)
        if len(conversation_history) > MAX_HISTORY:
            conversation_history.pop(0) # Remove the oldest turn to keep memory clean

    # Stop tracking
    end_time = time.perf_counter()
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    latency = end_time - start_time
    peak_mb = peak_mem / (1024 * 1024)

    print("-" * 50)
    print(f"🏁 PIPELINE FINISHED FOR {file_path}\n")
    
    # Return stats for the summary table
    return {
        "file": file_path.split("/")[-1],
        "turns": len(turns),
        "latency_sec": latency,
        "memory_mb": peak_mb
    }

def print_summary_table(stats_list):
    if not stats_list:
        return

    print("\n" + "="*70)
    print(f"{'🚀 RUNTIME PERFORMANCE SUMMARY':^70}")
    print("="*70)
    print(f"{'File Name':<25} | {'Turns':<6} | {'Latency (s)':<12} | {'Peak Mem (MB)':<12}")
    print("-" * 70)
    
    total_latency = 0
    total_memory = 0
    total_turns = 0

    for stat in stats_list:
        print(f"{stat['file']:<25} | {stat['turns']:<6} | {stat['latency_sec']:<12.2f} | {stat['memory_mb']:<12.2f}")
        total_latency += stat['latency_sec']
        total_memory += stat['memory_mb']
        total_turns += stat['turns']

    avg_latency = total_latency / len(stats_list)
    avg_memory = total_memory / len(stats_list)

    print("-" * 70)
    print(f"{'AVERAGE':<25} | {'-':<6} | {avg_latency:<12.2f} | {avg_memory:<12.2f}")
    print(f"{'TOTAL ESTIMATE':<25} | {total_turns:<6} | {total_latency:<12.2f} | {total_memory:<12.2f}")
    print("="*70 + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="eNO Badge AI Safety Pipeline")
    parser.add_argument("--file", type=str, help="Path to the WAV file to process")
    parser.add_argument("--all", action="store_true", help="Run all 5 test corpus files")
    
    args = parser.parse_args()

    test_files = [
        "audio_files/casual_chat.wav",
        "audio_files/heated_argument.wav",
        "audio_files/keyword_only.wav",
        "audio_files/false_positive_tv.wav",
        "audio_files/muffled_noise.wav"
    ]

    stats_collection = []

    if args.all:
        for f in test_files:
            stats = run_pipeline(f)
            if stats:
                stats_collection.append(stats)
        print_summary_table(stats_collection)
        
    elif args.file:
        stats = run_pipeline(args.file)
        if stats:
            print_summary_table([stats])
            
    else:
        print("Please provide a file with --file or use --all to run the corpus.")
