# Gunicorn configuration for Cloud Run
import multiprocessing
import os

# Server socket
bind = f"0.0.0.0:{os.environ.get('PORT', 8080)}"
backlog = 2048

# Worker processes - simplified for Cloud Run
workers = 1  # Single worker for Cloud Run
worker_class = "sync"  # Use sync worker for better compatibility
worker_connections = 1000
threads = 1
max_requests = 1000
max_requests_jitter = 50

# Timeouts
timeout = 30  # Reduced timeout for Cloud Run
keepalive = 2
graceful_timeout = 30

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "firetools"

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Performance - simplified for Cloud Run
preload_app = False  # Disable preload for better compatibility
# worker_tmp_dir removed - use default
