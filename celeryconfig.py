"""
Celery configuration for GEO/GSO Pipeline.
"""

# Broker settings (use Redis or RabbitMQ)
broker_url = 'redis://localhost:6379/0'
result_backend = 'redis://localhost:6379/1'

# Task settings
task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
timezone = 'UTC'
enable_utc = True

# Task execution settings
task_acks_late = True
task_reject_on_worker_lost = True
task_time_limit = 300  # 5 minutes max per task
task_soft_time_limit = 240  # 4 minutes soft limit

# Worker settings
worker_prefetch_multiplier = 1
worker_max_tasks_per_child = 50

# Rate limiting
task_annotations = {
    'src.tasks.generate_article_task': {'rate_limit': '10/m'},
}

# Result expiration
result_expires = 3600  # 1 hour
