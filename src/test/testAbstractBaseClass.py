__author__ = 'Yifu Huang'

from abc import *


class Base:
    def __init__(self):
        pass

    __metaclass__ = ABCMeta

    def hello(self, name):
        print(name)


class Sub(Base):
    def hello(self, name, address):
        super(Sub, self).hello(name)
        print(address)

    def __init__(self):
        pass


s = Sub()
s.hello("name", "address")