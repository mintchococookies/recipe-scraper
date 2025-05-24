import requests
import time
import os
import threading
import queue
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Optional, Dict, Any, List
from datadog_api_client import ApiClient, Configuration
from datadog_api_client.v2.api.logs_api import LogsApi
from datadog_api_client.v2.model.content_encoding import ContentEncoding
from datadog_api_client.v2.model.http_log import HTTPLog
from datadog_api_client.v2.model.http_log_item import HTTPLogItem

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
            print(logs)
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

class DatadogLogger:
    def __init__(self):
        # Create a thread pool with a maximum of 2 worker threads
        self.executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="datadog_logger")
        self._is_shutdown = False

    def _send_log(self, message: str, labels: Optional[Dict[str, str]] = None) -> bool:
        """
        Internal method to send a log message to Datadog
        """
        if self._is_shutdown:
            print("Logger is shut down, cannot send logs")
            return False
            
        try:
            configuration = Configuration()
            
            # Convert labels to Datadog tags format
            tags = []
            if labels:
                tags = [f"{k}:{v}" for k, v in labels.items()]
            
            log_item = HTTPLogItem(
                ddsource="recipe-scraper",
                ddtags=",".join(tags) if tags else None,
                message=str(message),
                service="recipe-scraper-backend"
            )
            
            body = HTTPLog([log_item])
            
            with ApiClient(configuration) as api_client:
                api_instance = LogsApi(api_client)
                response = api_instance.submit_log(
                    content_encoding=ContentEncoding.DEFLATE,
                    body=body
                )
                return True  # If we get here, the log was accepted (202)
        except Exception as e:
            print(f"Failed to send log to Datadog: {str(e)}")
            return False

    def log(self, message: str, labels: Optional[Dict[str, str]] = None) -> None:
        """
        Asynchronously send a log message to Datadog using a thread pool
        
        Args:
            message: The message to log
            labels: Optional dictionary of labels to attach to the log entry
        """
        if not self._is_shutdown:
            # Submit the logging task to the thread pool
            self.executor.submit(self._send_log, message, labels)

    def shutdown(self, timeout: int = 5) -> None:
        """
        Explicitly shutdown the thread pool with a timeout
        
        Args:
            timeout: Number of seconds to wait for pending tasks
        """
        if not self._is_shutdown:
            self._is_shutdown = True
            try:
                # First try graceful shutdown
                self.executor.shutdown(wait=True, timeout=timeout)
            except TimeoutError:
                print("Timeout waiting for Datadog logs to flush, forcing shutdown")
                # Force shutdown by cancelling pending tasks
                self.executor.shutdown(wait=False)

# Create logger instances
# grafana_logger = GrafanaLogger(
#     user_id=os.getenv('GRAFANA_USER_ID'),
#     api_key=os.getenv('GRAFANA_TOKEN')
# )

datadog_logger = DatadogLogger()