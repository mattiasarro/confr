import sys
import importlib
import re
import yaml
from yaml import SafeDumper

from confr import settings


def import_python_object(module_path_and_var_name):
    assert module_path_and_var_name != "", "Specified empty module."
    parts = module_path_and_var_name.split(".")
    module_name = ".".join(parts[:-1])
    func_name = parts[-1]
    module = importlib.import_module(module_name)
    func = getattr(module, func_name)
    return func


def read_yaml(fn, verbose=True):
    if verbose:
        print(f"Reading {fn}.")
    with open(fn, 'r') as f:
        return yaml.safe_load(f)


def write_yaml(fn, obj, verbose=True, do_print=False):
    if verbose:
        print(f"Writing {fn}.")
    with open(fn, 'w') as f:
        yaml.dump(obj, f, allow_unicode=True, sort_keys=False, Dumper=SafeDumper)
        if do_print:
            print("---")
            yaml.dump(obj, sys.stdout, allow_unicode=True, sort_keys=False, Dumper=SafeDumper)
            print("---")


def strip_keys(conf_dict, except_keys=[], key_prefix=None):
    ret = {}
    for k, v in conf_dict.items():
        k_with_prefix = f"{key_prefix}.{k}" if key_prefix else k
        if k_with_prefix not in except_keys:
            if type(v) == dict:
                v = strip_keys(v, except_keys=except_keys, key_prefix=k_with_prefix)
            ret[k] = v

    return ret


def with_keys(d, limit_keys, prefix=None):
    ret = {}
    for k, v in d.items():
        k_with_prefix = f"{prefix}.{k}" if prefix else k
        if k_with_prefix in limit_keys:
            ret[k] = v
        if type(v) == dict:
            v = with_keys(v, limit_keys, prefix=k_with_prefix)
            if v:
                ret[k] = v
    return ret


def flattened_items(conf_dict, prefix=None):
    for k, v in conf_dict.items():
        k = k if prefix is None else f"{prefix}.{k}"
        if type(v) == dict:
            for k2, v2 in flattened_items(v, prefix=k):
                yield k2, v2
        else:
            yield k, v


def interpolate_key(k, conf):
    if k:
        regex = r"\$\{(.*?)\}"
        for match in re.finditer(regex, k, re.DOTALL):
            outer = match.group(0) # e.g. ${key.subkey}
            inner = match.group(1) # e.g. key.subkey
            interpolated = conf.get(inner)
            assert type(interpolated) == str
            k = k.replace(outer, interpolated)
    return k


def recursive_merge(src, dst):
    for k, v in src.items():
        if type(v) == dict:
            if k in dst:
                if type(src[k]) == dict and type(dst[k]) == dict:
                    recursive_merge(src[k], dst[k])
                else:
                    dst[k] = v # overwrite, shouldn't happen usually
            else:
                dst[k] = v # set in dst for first time
        else:
            dst[k] = v # primitive, OK to blindly overwrite


def escape(s):
    return s.replace(".", settings.DOT_REPLACEMENT)


def unescape(s):
    return s.replace(settings.DOT_REPLACEMENT, ".")
