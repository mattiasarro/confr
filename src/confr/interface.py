import os
import inspect

from confr import settings
from confr.utils import write_yaml, report_conf_init, read_yaml
from confr.models import Conf, ModifiedConf
from confr import CONFIGURED


global_conf = None # global config object which will hold an instance of Conf


def get(k, default=None):
    return global_conf.get(k, default)


def set(k, v):
    return global_conf.set(k, v)


def configured(orig):
    if inspect.isfunction(orig):
        def confr_wrapped_function(*args, **kwargs):
            overrides = _get_call_overrides(orig, args, kwargs)
            return orig(*args, **kwargs, **overrides)

        return confr_wrapped_function
    else:
        class ConfrWrappedClass(orig):
            def __init__(self, *args, **kwargs):
                overrides = _get_call_overrides(orig, args, kwargs)
                super().__init__(*args, **kwargs, **overrides)

        return ConfrWrappedClass


def modified_conf(**kwargs):
    return ModifiedConf(global_conf, **kwargs)


def conf_from_dict(conf_dict, overrides=None, verbose=True):
    global global_conf
    report_conf_init(global_conf, verbose)
    global_conf = Conf([conf_dict], overrides=overrides, verbose=verbose)


def conf_from_files(conf_files, overrides=None, verbose=True):
    global global_conf
    report_conf_init(global_conf, verbose)
    fps = [conf_files] if type(conf_files) == str else conf_files
    conf_dicts = [read_yaml(fp, verbose=verbose) for fp in fps]
    global_conf = Conf(conf_dicts, overrides=overrides, verbose=verbose)


def conf_from_dir(
    conf_dir=settings.CONF_DIR,
    base_conf=settings.CONF_DIR,
    conf_patches=[],
    overrides=None,
    verbose=True,
    ):
    """Loads {conf_dir}/{base_conf}.yaml and all {conf_dir}/{conf_patch}.yaml files."""

    conf_files = [
        os.path.join(conf_dir, base + ".yaml")
        for base in ([base_conf] if base_conf else []) + list(conf_patches)
    ]

    global global_conf
    report_conf_init(global_conf, verbose)
    fps = [conf_files] if type(conf_files) == str else conf_files
    conf_dicts = [read_yaml(fp, verbose=verbose) for fp in fps]
    global_conf = Conf(conf_dicts, overrides=overrides, verbose=verbose)


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


def _get_call_overrides(cls_or_fn, args, kwargs):
    try:
        bound_args = inspect.signature(cls_or_fn).bind(*args, **kwargs)
    except Exception as e:
        raise Exception(f"Unable to substitute values for {cls_or_fn.__name__}. {e}")
    bound_args.apply_defaults()
    default_args = dict(bound_args.arguments)

    assert global_conf is not None, "Need to initialize config before executing configurable functions."
    try:
        return {
            k: global_conf[k]
            for k, v in default_args.items()
            if type(v) == str and v == CONFIGURED
        }
    except:
        print(f"Trying to assign configurations to {cls_or_fn.__name__}")
        raise
