from celery import Celery

app = Celery('tasks', result_backend='db+sqlite:///brocker.sqlite')

@app.task
def add(x, y):
    return x + y
