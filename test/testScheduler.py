__author__ = 'Yifu Huang'

from src.azureformation.scheduler import (
    scheduler,
)
from datetime import (
    datetime,
    timedelta,
)
import time


def alarm(t):
    print('Alarm! This alarm was scheduled at %s.' % t)
    return {
        "key": "val"
    }

alarm_time = datetime.now() + timedelta(seconds=10)
scheduler.add_job(alarm, 'date', run_date=alarm_time, args=[datetime.now()])
while True:
    print 'main'
    time.sleep(10)