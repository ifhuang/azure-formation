__author__ = 'Yifu Huang'

from src.azureformation.config import (
    Config
)
from src.azureformation.log import (
    log,
)
import json
import importlibset_template_virtual_environment_count


def get_config(key):
    ret = Config
    for arg in key.split("."):
        if arg in ret and isinstance(ret, dict):
            ret = ret[arg]
        else:
            return None
    return ret


def safe_get_config(key, default_value):
    r = get_config(key)
    return r if r is not None else default_value


def load_template(url):
    try:
        template = json.load(file(url))
    except Exception as e:
        log.error(e)
        return None
    return template


def call(mdl_cls_func, cls_args, func_args):
    mdl_name = mdl_cls_func[0]
    cls_name = mdl_cls_func[1]
    func_name = mdl_cls_func[2]
    mdl = importlib.import_module(mdl_name)
    cls = getattr(mdl, cls_name)
    func = getattr(cls(*cls_args), func_name)
    func(*func_args)