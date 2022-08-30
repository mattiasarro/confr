import aiocontextvars

from confr.utils import import_python_object


class Conf:
    def __init__(
        self,
        conf_dicts,
        overrides=None,
        strict=False,
        verbose=True,
        ):

        self.c_singletons = {}
        self.c_original = {}
        self.overrides_dicts = aiocontextvars.ContextVar("overrides_dicts", default=[])

        for conf_dict in conf_dicts:
            self._init_conf_dict(conf_dict, strict)

        if overrides:
            if verbose:
                print(f"Overwriting {len(overrides)} configs with `overrides`")
            self.add_overrides(overrides, verbose)

        if "seed" in self.c_original:
            self._set_seed(verbose)

    def _init_conf_dict(self, conf_dict, strict):
        for k, v in conf_dict.items():
            if self.c_original.get(k) is not None:
                if self.c_original[k] != v:
                    msg = f"override {k} = {v} (formerly {self.c_original[k]})"
                    if strict:
                        raise Exception("can't " + msg)
                    else:
                        print("    " + msg)
            self.c_original[k] = v

    def get(self, k, default=None):
        # TODO handle dot notation for nested keys
        try:
            return self[k]
        except AssertionError:
            return default

    def set(self, k, v):
        self.c_original[k] = v

    def __getitem__(self, k):
        for overrides_dict in self.overrides_dicts.get()[::-1]:
            if k in overrides_dict:
                return self._get_val(k, overrides_dict[k])

        assert k in self.c_original, f"no config '{k}' found in {list(self.c_original.keys())}"
        return self._get_val(k, self.c_original[k])

    def __setitem__(self, k, v):
        self.c_original[k] = v

    def _get_val(self, k, orig_val):
        if type(orig_val) == str:
            if k is not None and orig_val[0] == "@":
                # _get_val is called for a root element of conf.yaml, so memoize the result
                if self.c_singletons.get(k) is None:
                    self.c_singletons[k] = self._get_python_object(k, orig_val)
                return self.c_singletons[k]
            elif k is None and orig_val[0] in ["@", "$"]:
                # _get_val is called for a non-root element of conf.yaml, therefore we can't memoize it
                return self._get_python_object(None, orig_val)
            else:
                return orig_val
        elif type(orig_val) == list:
            return [self._get_val(None, v) for v in orig_val]
        elif type(orig_val) == dict:
            return {k: self._get_val(None, v) for v in orig_val for k, v in orig_val.items()}
        else:
            return orig_val

    def _get_python_object(self, k, orig_val):
        if orig_val.startswith("@") and orig_val.endswith("()"):
            assert k != "__SINGLETON_ATTRIBUTE__", \
            (
                'Tried to pass a config like `singleton_name/attribute_name: "@MyClass()"`, '
                'which is not supported. Instead define a singleton `my_obj: "@MyClass()"` and '
                'refer to it as `singleton_name/attribute_name = "$my_obj"`'
            )
            return self._init_python_object(k, orig_val[1:-2])
        elif orig_val.startswith("@"):
            return import_python_object(orig_val[1:])
        elif orig_val[0] == "$": # reference to another config val
            return self[orig_val[1:]]
        else:
            return orig_val

    def _init_python_object(self, k, module_path_and_var_name):
        overrides = {}
        if k is not None:
            prefix = k + "/"
            for conf_k, conf_v in self.to_dict().items():
                if conf_k.startswith(prefix):
                    override_key = conf_k[len(prefix):]
                    if type(conf_v) == str and conf_v[0] in ["@", "$"]:
                        override_val = self._get_python_object("__SINGLETON_ATTRIBUTE__", conf_v)
                    else:
                        override_val = conf_v
                    overrides[override_key] = override_val

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

    def to_dict(self):
        """This implementation does not eagerly initialize singleton configs."""
        active_conf = {}
        active_conf.update(self.c_original)
        active_conf.update(self.c_singletons)
        for overrides_dict in self.overrides_dicts.get():
            active_conf.update(overrides_dict)
        return active_conf

    def _set_seed(self, verbose=True):
        seed = self["seed"]
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
