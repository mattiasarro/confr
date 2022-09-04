import os
import aiocontextvars

from confr.utils import import_python_object, read_yaml
# TODO interpolations in overrides

def _in(conf, k):
    for part in k.split("."):
        if part in conf:
            conf = conf[part]
        else:
            return False
    return True


def _get(conf, k):
    for part in k.split("."):
        if part not in conf:
            return
        conf = conf[part]
    return conf


def _set(conf, k, v, strict=False):
    if not _in(conf, k):
        if _get(conf, k) != v:
            msg = f"override {k} = {v} (formerly {_get(conf, k)})"
            if strict:
                raise Exception("can't " + msg)
            else:
                print("    " + msg)

    parts = k.split(".")
    if len(parts) > 1:
        for part in parts[:-1]:
            if part not in conf:
                conf[part] = {}
            conf = conf[part]
        conf[parts[-1]] = v
    else:
        conf[k] = v

    return v


def _is_interpolation(conf, k):
    return _is_interpolation_val(_get(conf, k))


def _is_interpolation_val(val):
    return type(val) == str and val.startswith("${") and val.endswith("}")


def _interpolated_key(orig_val):
    interpolated_key = orig_val[2:-1]
    assert not interpolated_key.startswith("."), \
        ("Relative interpolations are not yet supported.", orig_val, interpolated_key)
    return interpolated_key


def _follow_file_refs(conf_dict, conf_dir):
    for k, v in conf_dict.items():
        if type(v) == dict and "_file" in v:
            conf_dict[k] = read_yaml(os.path.join(conf_dir, v["_file"]))
        if type(v) == dict:
            _follow_file_refs(v, conf_dir)


class Conf:
    def __init__(
        self,
        conf_dicts,
        overrides=None,
        strict=False,
        verbose=True,
        ):

        self.strict = strict
        self.c_singletons = {}
        self.c_original = {}
        self.overrides_dicts = aiocontextvars.ContextVar("overrides_dicts", default=[])

        for conf_dict in conf_dicts:
            self._init_conf_dict(conf_dict)

        if overrides:
            if verbose:
                print(f"Overwriting {len(overrides)} configs with `overrides`")
            self.add_overrides(overrides, verbose)

        if _in(self.c_original, "seed"):
            self._set_seed(verbose)

    def _init_conf_dict(self, conf_dict):
        for k, v in conf_dict.items():
            self.set(k, v)

    def follow_file_refs(self, conf_dir):
        _follow_file_refs(self.c_original, conf_dir)

    def get(self, k, default=None):
        for overrides_dict in self.overrides_dicts.get()[::-1]:
            if k in overrides_dict:
                return self._get_val(k, overrides_dict[k])

        if _in(self.c_singletons, k):
            return self._get_val(k, _get(self.c_singletons, k))
        elif _in(self.c_original, k):
            return self._get_val(k, _get(self.c_original, k))
        else:
            if default is None:
                raise Exception(f"no config '{k}' found in {list(self.c_original.keys())}")
            else:
                return default

    def set(self, k, v):
        _set(self.c_original, k, v, strict=self.strict)

    def __getitem__(self, k):
        return self.get(k)

    def __setitem__(self, k, v):
        self.set(k, v)

    def _get_val(self, k, orig_val):
        if type(orig_val) == str:
            if _is_interpolation_val(orig_val):
                assert k is not None, "Not supported."
                return self.get(_interpolated_key(orig_val))
            elif k is not None and orig_val.startswith("@"):
                if not _in(self.c_singletons, k):
                    # memoize the result
                    return _set(self.c_singletons, k, self._get_python_object(k, orig_val))
                return _get(self.c_singletons, k)
            elif k is None and orig_val.startswith("@"):
                # _get_val is called for a list element, therefore we can't memoize it
                return self._get_python_object(None, orig_val)
            else:
                return orig_val
        elif type(orig_val) == list:
            # TODO handle int indexes
            return [self._get_val(None, v) for v in orig_val]
        elif type(orig_val) == dict:
            return {
                k2: self._get_val(f"{k}.{k2}", v)
                for k2, v in orig_val.items()
            }
        else:
            return orig_val

    def _get_python_object(self, k, orig_val):
        if orig_val.startswith("@") and orig_val.endswith("()"):
            return self._init_python_object(k, orig_val[1:-2])
        elif orig_val.startswith("@"):
            return import_python_object(orig_val[1:])
        else:
            raise Exception("_get_python_object orig_val should start with '@'")

    def _init_python_object(self, k, module_path_and_var_name):
        overrides = {}
        if k is not None:
            conf = self.to_dict(include_singletons=True)
            if "." in k:
                parts = k.split(".")
                conf = _get(conf, ".".join(parts[:-1])) # get parent node of obj in conf
                k = parts[-1] # look for key in that subtree

            prefix = k + "/"
            for conf_k, conf_v in conf.items():
                if conf_k.startswith(prefix):
                    if type(conf_v) == str and conf_v.startswith("@"):
                        if conf_v.endswith("()"):
                            raise Exception((
                                'Tried to pass a config like `singleton_name/attribute_name: "@MyClass()"`, '
                                'which is not supported. Instead define a singleton `my_obj: "@MyClass()"` and '
                                'refer to it as `singleton_name/attribute_name = "${my_obj}"`'
                            ))
                        else:
                            conf_v = self._get_python_object(None, conf_v)

                    override_key = conf_k[len(prefix):]
                    overrides[override_key] = conf_v

        func = import_python_object(module_path_and_var_name)
        return func(**overrides)

    def add_overrides(self, overrides, verbose):
        for arg_name, arg_val in overrides.items():
            if verbose:
                print(f"    {arg_name} = {arg_val}")
            if self.c_original[arg_name] != arg_val:
                if verbose:
                    print(f"        value differs from existing conf ({self.c_original[arg_name]})")
                self.c_original[arg_name] = arg_val

    def to_dict(self, include_singletons=False):
        """This implementation does not eagerly initialize singleton configs."""
        active_conf = {}
        active_conf.update(self.c_original)
        if include_singletons:
            # TODO recursive merge
            active_conf.update(self.c_singletons)
        for overrides_dict in self.overrides_dicts.get():
            # TODO recursive merge
            active_conf.update(overrides_dict)
        return active_conf

    def _set_seed(self, verbose=True):
        # TODO remove

        seed = self.get("seed")
        if seed is not None:
            if verbose:
                print(f"Setting seed to {seed}")
            import tensorflow as tf
            import numpy as np
            import random
            np.random.seed(seed)
            random.seed(seed)
            tf.random.set_seed(seed)


class ModifiedConf:
    def __init__(self, global_conf, overrides=None, **kwargs):
        self.global_conf = global_conf
        self.overrides_dict = {}
        if overrides is not None:
            self.overrides_dict.update(overrides)
        self.overrides_dict.update(kwargs)

    def __enter__(self):
        self.overrides_dicts_before = self.global_conf.overrides_dicts.set(
            self.global_conf.overrides_dicts.get() + [self.overrides_dict]
        )

    def __exit__(self, *args):
        assert self.global_conf.overrides_dicts.get()[-1] == self.overrides_dict, \
            (self.global_conf.overrides_dicts.get()[-1], self.overrides_dict)
        self.global_conf.overrides_dicts.reset(self.overrides_dicts_before)
