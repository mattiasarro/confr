import sys
import importlib
import yaml
from yaml import CSafeDumper


def import_python_object(module_path_and_var_name):
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
        yaml.dump(obj, f, allow_unicode=True, sort_keys=False, Dumper=CSafeDumper)
        if do_print:
            print("---")
            yaml.dump(obj, sys.stdout, allow_unicode=True, sort_keys=False, Dumper=CSafeDumper)
            print("---")


def report_conf_init(c, verbose):
    if c is None and verbose:
        print("Declaring config.")
    else:
        if verbose:
            print("Redeclaring config.")


def strip_keys(conf_dict, except_keys=[], key_prefix=None):
    ret = {}
    for k, v in conf_dict.items():
        k_with_prefix = f"{key_prefix}.{k}" if key_prefix else k
        print(k_with_prefix, except_keys)
        if k_with_prefix not in except_keys:
            if type(v) == dict:
                v = strip_keys(v, except_keys=except_keys, key_prefix=k_with_prefix)
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
