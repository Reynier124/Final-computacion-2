from celery import Celery
import time
from datetime import datetime
from calculator_server.simpson_method import Simpson

app = Celery('tasks', broker='redis://localhost:6379/0')
app.conf.update(
    result_backend='redis://localhost:6379/0'
)

@app.task
def calculate_simpson_method(a,b,n,f,aprox):
    print("1.1")
    start_time = time.time()
    result, s, e = Simpson(a,b,n).calculate(f, aprox)
    end_time = time.time()
    timeExecution = end_time - start_time
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    all_info = (result, timeExecution, date)
    return all_info