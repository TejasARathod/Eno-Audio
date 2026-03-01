import os
import redis
import json

def start_subscriber():
    # Connect to the Redis container
    host = os.getenv("REDIS_HOST", "redis")
    r = redis.Redis(host=host, port=6379, decode_responses=True)
    pubsub = r.pubsub()
    pubsub.subscribe('emergency_alerts')

    print("📡 ARC Subscriber active. Waiting for alerts...")

    for message in pubsub.listen():
        if message['type'] == 'message':
            try:
                data = json.loads(message['data'])
                
                incident_id = data.get('incident_id', 'UNKNOWN_INCIDENT')
                payload_data = data.get('data', {})
                reasoning = payload_data.get('reasoning', 'No reasoning provided')
                history = payload_data.get('history', [])
                transcript = payload_data.get('transcript', 'No transcript')
                
                # --- The terminal output for the Operator ---
                print(f"\n🚨 [RECEIVED ALERT] Incident: {incident_id}")
                print(f"   Category: {payload_data.get('category', 'unknown')}")
                
                if history:
                    print("   [Context History]:")
                    for past_turn in history:
                        print(f"      - {past_turn}")
                        
                print(f"   [Current Trigger]: '{transcript}'")
                print(f"   [AI Reasoning]   : {reasoning}")
                print("-" * 50)
                
                # --- Save to permanent log file ---
                with open("redis_final_alerts.log", "a", encoding="utf-8") as log_file:
                    log_file.write(f"[RECEIVED ALERT] Incident: {incident_id}\n")
                    log_file.write(f"Category: {payload_data.get('category', 'unknown')}\n")
                    if history:
                        log_file.write(f"Context History: {' | '.join(history)}\n")
                    log_file.write(f"Trigger: '{transcript}'\n")
                    log_file.write(f"Reason: {reasoning}\n")
                    log_file.write("-" * 50 + "\n")
                    log_file.flush()
                    
            except Exception as e:
                print(f"⚠️ Error parsing incoming alert: {e}")

if __name__ == "__main__":
    start_subscriber()
