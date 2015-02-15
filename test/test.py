__author__ = 'Yifu Huang'


class A:
    def __init__(self):
        print 'init from A'

    def __repr__(self):
        return self.__class__.__name__


class B(A):
    pass


A()
B()