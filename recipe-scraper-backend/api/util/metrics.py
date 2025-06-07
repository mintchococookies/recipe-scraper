import time
from functools import wraps
from flask import request
from .logging import datadog_logger

def track_latency(endpoint_name):
    """
    Decorator to track endpoint latency and log it to Datadog.
    
    Args:
        endpoint_name (str): Name of the endpoint being tracked
        
    Returns:
        function: Decorated function that tracks and logs latency
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            start_time = time.time()
            try:
                result = f(*args, **kwargs)
                status = 200
            except Exception as e:
                status = 500
                raise e
            finally:
                latency = (time.time() - start_time) * 1000  # Convert to milliseconds
                datadog_logger.log(
                    f"Endpoint latency for {endpoint_name}",
                    {
                        "endpoint": endpoint_name,
                        "latency_ms": latency,
                        "status": status,
                        "method": request.method,
                        "url": request.url
                    }
                )
            return result
        return wrapped
    return decorator 