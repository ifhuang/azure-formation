__author__ = 'Yifu Huang'


from src.azureformation.azureoperation.service import Service

class Pao():

    def __init__(self, a, b, c):
        self.a = a
        self.b = b
        self.c = c

    def funcA(self):
        print Service.__module__
        print Service.__name__
        print Service.add_virtual_machine.__name__

    def funcB(self):
        print 'funcB'


Pao(1, 2, 3).funcA()