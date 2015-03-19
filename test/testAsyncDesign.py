__author__ = 'Yifu Huang'

from src.azureformation.scheduler import scheduler
from datetime import datetime, timedelta
import importlib
import sys
import time

MODULE = 'test.testAsyncDesign'
CALL = [
    ['StorageAccount', 'create'],
    ['CloudService', 'create'],
    ['VirtualMachine', 'create'],
    ['Service', 'wait_async'],
    ['Service', 'wait_dm'],
    ['Service', 'wait_vm'],
]
# service: azure key id
# storage account, cloud service and virtual machine: service -> azure key id


def call(module_name, class_name, class_args, func_name, func_args):
    module = importlib.import_module(module_name)
    cls = getattr(module, class_name)
    func = getattr(cls(*class_args), func_name)
    func(*func_args)


class Service():

    def __init__(self, a, b, c):
        self.a = a
        self.b = b
        self.c = c

    def wait_async(self, id, next):
        print self.__class__.__name__ + ' ' + sys._getframe().f_code.co_name + ' ' + 'start'
        exec_time = datetime.now() + timedelta(seconds=3)
        if next == 1:
            scheduler.add_job(call, 'date', run_date=exec_time, args=[MODULE, CALL[next][0], (1, ), CALL[next][1], (1, 2)])
        elif next == 4:
            scheduler.add_job(call, 'date', run_date=exec_time, args=[MODULE, CALL[next][0], (1, 2, 3), CALL[next][1], (1, 2)])
        else:
            scheduler.add_job(call, 'date', run_date=exec_time, args=[MODULE, CALL[next][0], (1, 2, 3), CALL[next][1], (1, 2, 3)])
        print self.__class__.__name__ + ' ' + sys._getframe().f_code.co_name + ' ' + 'end'

    def wait_dm(self, cs, dm):
        print self.__class__.__name__ + ' ' + sys._getframe().f_code.co_name + ' ' + 'start'
        exec_time = datetime.now() + timedelta(seconds=3)
        scheduler.add_job(call, 'date', run_date=exec_time, args=[MODULE, CALL[5][0], (1, 2, 3), CALL[5][1], (1, 2, 3, 3)])
        print self.__class__.__name__ + ' ' + sys._getframe().f_code.co_name + ' ' + 'end'

    def wait_vm(self, cs, dm, vm, next=None):
        print self.__class__.__name__ + ' ' + sys._getframe().f_code.co_name + ' ' + 'start'
        exec_time = datetime.now() + timedelta(seconds=3)
        if next is not None:
            scheduler.add_job(call, 'date', run_date=exec_time, args=[MODULE, CALL[next][0], (1, 2, 3), CALL[next][1], (1, 5)])
        print self.__class__.__name__ + ' ' + sys._getframe().f_code.co_name + ' ' + 'end'


class StorageAccount():

    def __init__(self, service):
        self.service = service
        self.a = service.a
        self.b = service.b
        self.c = service.c
        pass

    def create(self, ex, tu):
        print self.__class__.__name__ + ' ' + sys._getframe().f_code.co_name + ' ' + 'start'
        exec_time = datetime.now() + timedelta(seconds=3)
        scheduler.add_job(call, 'date', run_date=exec_time, args=[MODULE, CALL[3][0], (self.a, self.b, self.c), CALL[3][1], (1, 1)])
        print self.__class__.__name__ + ' ' + sys._getframe().f_code.co_name + ' ' + 'end'


class CloudService():

    def __init__(self, service):
        pass

    def create(self, ex, tu):
        print self.__class__.__name__ + ' ' + sys._getframe().f_code.co_name + ' ' + 'start'
        exec_time = datetime.now() + timedelta(seconds=3)
        scheduler.add_job(call, 'date', run_date=exec_time, args=[MODULE, CALL[2][0], (1, ), CALL[2][1], (1, 2)])
        print self.__class__.__name__ + ' ' + sys._getframe().f_code.co_name + ' ' + 'end'


class VirtualMachine():

    def __init__(self, service):
        pass

    def create(self, ex, tu):
        print self.__class__.__name__ + ' ' + sys._getframe().f_code.co_name + ' ' + 'start'
        exec_time = datetime.now() + timedelta(seconds=3)
        scheduler.add_job(call, 'date', run_date=exec_time, args=[MODULE, CALL[3][0], (1, 2, 3), CALL[3][1], (1, 4)])
        print self.__class__.__name__ + ' ' + sys._getframe().f_code.co_name + ' ' + 'end'


if __name__ == '__main__':
    # create storage account first
    service = Service(1, 2, 3)
    exec_time = datetime.now() + timedelta(seconds=3)
    scheduler.add_job(call, 'date', run_date=exec_time, args=[MODULE, CALL[0][0], (service, ), CALL[0][1], (1, 2)])
    # keep main thread alive
    while True:
        print 'main'
        time.sleep(10)