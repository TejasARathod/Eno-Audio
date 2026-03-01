import os
import uuid
import time
import json
import logging
from datetime import datetime, timezone
import redis 

logger = logging.getLogger(__name__)

class IncidentManager:
    def __init__(self, cooldown_seconds=60):
        self.active_incident_id = None
        self.last_alert_time = 0
        self.cooldown_seconds = cooldown_seconds
        
        host = os.getenv("REDIS_HOST", "redis")
        try:
            # FAIL-SAFE 1: Add a socket_timeout so a hanging network doesn't freeze the pipeline
            self.redis_client = redis.Redis(host=host, port=6379, decode_responses=True, socket_timeout=2.0)
            
            # FAIL-SAFE 2: Force a real connection test immediately. 
            self.redis_client.ping()
            logger.info("IncidentManager: Connected to Redis successfully.")
            
        except (redis.ConnectionError, redis.TimeoutError) as e:
            # Fixed bare except: Only catch actual connection issues
            logger.warning(f"FAIL-SAFE: Redis is unavailable. Alerts will only be printed locally. Error: {e}")
            self.redis_client = None

    def should_fire_alert(self, is_threat: bool) -> str:
        """
        Determines if we should start a new incident, 
        continue an existing one, or do nothing.
        """
        if not is_threat:
            return None

        current_time = time.time()
        
        # If we have an active incident and we're within the cooldown window
        if self.active_incident_id and (current_time - self.last_alert_time) < self.cooldown_seconds:
            logger.info(f"Existing Incident Active: {self.active_incident_id}. Appending turn context.")
            self.last_alert_time = current_time
            return "APPEND" 

        # Otherwise, start a brand new incident
        self.active_incident_id = str(uuid.uuid4())[:8] # Short readable ID
        self.last_alert_time = current_time
        logger.info(f"NEW THREAT DETECTED. Created Incident: INC-{self.active_incident_id}")
        return "NEW"

    # FIXED: Added conversation_history=None to the function arguments
    def publish_alert(self, turn_id, transcript, decision, incident_type, conversation_history=None):
        """Simulates publishing to a real-time message stream."""
        
        if conversation_history is None:
            conversation_history = []
        
        # FAIL-SAFE 3: Protect against a missing or malformed AI decision object
        if decision is None:
            logger.error("FAIL-SAFE: Missing decision object. Cannot publish alert.")
            return None
            
        # Safely extract attributes in case the Pydantic object failed upstream
        category = getattr(decision, 'threat_category', 'unknown')
        reasoning = getattr(decision, 'reasoning', 'No reasoning provided')
        confidence = getattr(decision, 'confidence_score', 0.0)

        # FAIL-SAFE 4: Use timezone-aware UTC (utcnow is deprecated)
        timestamp = datetime.now(timezone.utc).isoformat()

        alert_payload = {
            "event": "EMERGENCY_ALERT",
            "incident_id": f"INC-{self.active_incident_id}",
            "type": incident_type,
            "timestamp": timestamp,
            "badge_id": "badge_tejas_01",
            "data": {
                "transcript": transcript,
                "history": conversation_history, # FIXED: Added history into the actual payload!
                "category": category,
                "reasoning": reasoning,
                "confidence": confidence
            }
        }

        if self.redis_client:
            try:
                # We publish to the 'emergency_alerts' channel
                self.redis_client.publish('emergency_alerts', json.dumps(alert_payload))
            except Exception as e:
                logger.error(f"FAIL-SAFE: Failed to publish to Redis stream: {e}")
        
        # This is where you'd push to Redis or a Webhook. For now, we print prominently.
        print("\n" + "="*50)
        print(f"🚨 PUBLISHING TO ARC: {alert_payload['incident_id']}")
        print(f"REASON: {reasoning}")
        print("="*50 + "\n")
        
        return alert_payload
