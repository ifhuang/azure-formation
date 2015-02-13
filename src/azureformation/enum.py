__author__ = 'Yifu Huang'


class AKOwner:
    """
    For owner in AzureKey
    """
    User = 0
    Hackathon = 1


class EStatus:
    """
    For status in Experiment
    """
    Init = 0
    Starting = 1
    Running = 2
    Stopped = 3
    Deleted = 4
    Failed = 5
    Rollbacking = 6
    Rollbacked = 7


class VEProvider:
    """
    For provider in VirtualEnvironment
    """
    AzureVM = 0
    Docker = 1


class VEStatus:
    """
    For status in VirtualEnvironment
    """
    Init = 0
    Running = 1
    Stopped = 2
    Deleted = 3


class VERemoteProvider:
    """
    For remote provider in VirtualEnvironment
    """
    Guacamole = 0