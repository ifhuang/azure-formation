__author__ = 'Yifu Huang'

from src.azureformation.scheduler import (
    scheduler,
)
from datetime import (
    datetime,
    timedelta,
)
import time
import importlib


def alarm(mdl, cls, func):
    mdl = importlib.import_module(mdl)
    cls = getattr(mdl, cls)
    func = getattr(cls('a', 'b', 'c'), func)
    func()

alarm_time = datetime.now() + timedelta(seconds=10)
scheduler.add_job(alarm, 'date', run_date=alarm_time, args=['test.testClass', 'Pao', 'funcA'])
while True:
    print 'main'
    time.sleep(10)