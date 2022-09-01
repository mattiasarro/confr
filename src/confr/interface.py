import os
import inspect

from confr import settings
from confr.utils import write_yaml, report_conf_init, read_yaml
from confr.models import Conf, ModifiedConf
from collections import namedtuple


global_conf = None # global config object which will hold an instance of Conf
Value = namedtuple("Value", ["key", "default"])


def get(k, default=None):
    return global_conf.get(k, default)


def set(k, v):
    return global_conf.set(k, v)


def bind(*args, subkeys=None):
    def decorator(orig):
        if inspect.isfunction(orig):
            def confr_wrapped_function(*args, **kwargs):
                overrides = _get_call_overrides(orig, args, kwargs, subkeys)
                return orig(*args, **kwargs, **overrides)

            return confr_wrapped_function
        else:
            class ConfrWrappedClass(orig):
                def __init__(self, *args, **kwargs):
                    overrides = _get_call_overrides(orig, args, kwargs, subkeys)
                    super().__init__(*args, **kwargs, **overrides)

            return ConfrWrappedClass

    if len(args): # used as confr.bind; args = (orig), subkeys = None
        return decorator(args[0])
    else: # used as confr.bind(subkeys="asd"); args = (), subkeys = "asd"
        return decorator


def value(key=None, default=None):
    return Value(key, default)


def init(
    conf=None,
    conf_files=None,
    conf_dir=settings.CONF_DIR,
    base_conf=settings.BASE_CONF,
    overrides=None,
    verbose=True,
    validate=None,
    conf_patches=(),
):
    global global_conf
    report_conf_init(global_conf, verbose)

    if conf:
        """Loads conf directly from conf dict."""
        global_conf = Conf([conf], overrides=overrides, verbose=verbose)

    elif conf_files:
        """Loads conf from conf files."""
        fps = [conf_files] if type(conf_files) == str else conf_files
        conf_dicts = [read_yaml(fp, verbose=verbose) for fp in fps]
        global_conf = Conf(conf_dicts, overrides=overrides, verbose=verbose)

    else:
        """Loads {conf_dir}/{base_conf}.yaml and all {conf_dir}/{conf_patch}.yaml files."""

        conf_files = [
            os.path.join(conf_dir, base + ".yaml")
            for base in ([base_conf] if base_conf else []) + list(conf_patches)
        ]

        fps = [conf_files] if type(conf_files) == str else conf_files
        conf_dicts = [read_yaml(fp, verbose=verbose) for fp in fps]
        global_conf = Conf(conf_dicts, overrides=overrides, verbose=verbose)


def modified_conf(**kwargs):
    return ModifiedConf(global_conf, **kwargs)


def write_conf_file(fp, except_keys=[]):
    ret = {}
    for k, v in global_conf.to_dict().items():
        if k not in except_keys:
            original_val = global_conf.c_original[k]
            if type(original_val) == str and original_val[0] in ["@", "$"]:
                ret[k] = original_val
            else:
                ret[k] = v

    write_yaml(fp, ret)
    print(f"Wrote configurations for: {list(ret.keys())}")


def _get_call_overrides(cls_or_fn, args, kwargs, subkeys):
    try:
        bound_args = inspect.signature(cls_or_fn).bind(*args, **kwargs)
    except Exception as e:
        raise Exception(f"Unable to substitute values for {cls_or_fn.__name__}. {e}")
    bound_args.apply_defaults()
    default_args = dict(bound_args.arguments)

    assert global_conf is not None, "Need to initialize config before executing configurable functions."
    try:
        ret = {}
        for k, v in default_args.items():
            if callable(v) and v == value: # kwarg=confr.value
                get_key = f"{subkeys}.{k}" if subkeys else k
                get_default = None
            elif isinstance(v, Value): # kwarg=confr.value(...)
                if v.key is None: # kwarg=confr.value(default="default")
                    get_key = f"{subkeys}.{k}" if subkeys else k
                    get_default = v.default
                else: # kwarg=confr.value("key", default="default")
                    if v.key[0] == ".":
                        get_key = subkeys + v.key if subkeys else v.key # path is potentially relative to subkey
                    else:
                        get_key = v.key # path is absolute
                    get_default = v.default
            else: # non-configurable value, e.g. kwarg=123
                continue
            ret[k] = global_conf.get(get_key, get_default)
        return ret
    except:
        print(f"Trying to assign configurations to {cls_or_fn.__name__}")
        raise
