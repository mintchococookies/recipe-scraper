import requests
import time
import os
from typing import Optional, Dict, Any
from util.logging import logger

class GrafanaLogger:
    def __init__(self, user_id: int, api_key: str):
        self.user_id = user_id
        self.api_key = api_key
        self.base_url = "https://logs-prod-020.grafana.net/loki/api/v1/push"
        
    def log(self, message: str, labels: Optional[Dict[str, str]] = None) -> bool:
        """
        Send a log message to Grafana Loki
        
        Args:
            message: The message to log
            labels: Optional dictionary of labels to attach to the log entry
            
        Returns:
            bool: True if log was sent successfully, False otherwise
        """

        timestamp = str(int(time.time() * 1e9))  # Current time in nanoseconds
        
        logs = {
            "streams": [
                {
                    "stream": labels,
                    "values": [[timestamp, str(message)]]
                }
            ]
        }
        
        try:
            response = requests.post(
                url=self.base_url,
                auth=(self.user_id, self.api_key),
                json=logs,
                headers={"Content-Type": "application/json"}
            )
            return response.status_code == 204
        except Exception as e:
            print(f"Failed to send log to Grafana: {str(e)}")
            return False

logger = GrafanaLogger(
    user_id=os.getenv('GRAFANA_USER_ID'),
    api_key=os.getenv('GRAFANA_TOKEN')
)