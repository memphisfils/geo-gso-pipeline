"""
Celery configuration for GEO/GSO Pipeline.
"""

broker_url = 'redis://localhost:6379/0'
result_backend = 'redis://localhost:6379/1'

task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
timezone = 'UTC'
enable_utc = True

task_acks_late = True
task_reject_on_worker_lost = True
task_time_limit = 300 
task_soft_time_limit = 240 

worker_prefetch_multiplier = 1
worker_max_tasks_per_child = 50

task_annotations = {
    'src.tasks.generate_article_task': {'rate_limit': '10/m'},
}


result_expires = 3600  
