import os
import json
import aiocontextvars
import argparse
from copy import deepcopy

from confr.utils import import_python_object, read_yaml, flattened_items, recursive_merge, escape, unescape
from confr import settings, plx


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


def _set(conf, k, v, strict=False, merge_mode="deep_merge", verbose=True):
    assert merge_mode in ["deep_merge", "override"]

    former_val = None
    if _in(conf, k):
        if _get(conf, k) != v:
            former_val = _get(conf, k)
            if strict:
                raise Exception(f"Can't override {k} (formerly {former_val}).")

    parts = k.split(".")
    if len(parts) > 1:
        for part in parts[:-1]:
            if part not in conf:
                conf[part] = {}
            conf = conf[part]
        k = parts[-1]

    if k.endswith("="):
        merge_mode = "override"
        k = k[:-1]

    if merge_mode == "deep_merge" and type(v) == dict and k in conf:
        _deep_merge(conf, k, v)
    else:
        conf[k] = v

    if verbose and former_val:
        if type (v) == dict:
            print(f"Override {k} = " + json.dumps(v, indent=4))
        else:
            print(f"Override {k} = {v}")

    return v


def _deep_merge(conf, k, v):
    assert type(v) == dict, \
        f"Expected _deep_merge v to be dict, got {type(v)}."

    if k not in conf or conf[k] is None:
        conf[k] = {}

    for k2, v2 in v.items():
        if type(v2) == dict and not k2.endswith("="):
            _deep_merge(conf[k], k2, v2)
        else:
            conf[k][k2.replace("=", "")] = v2


def _deep_merge_dicts(dicts, verbose=False):
    ret = {}
    for d in dicts:
        for k, v in d.items():
            _set(ret, k, v, merge_mode="deep_merge", verbose=verbose)
    return ret


def _is_interpolation(conf, k):
    return _is_interpolation_val(_get(conf, k))


def _is_interpolation_val(val):
    return type(val) == str and val.startswith("${") and val.endswith("}")


def _interpolated_key(k, orig_val):
    interpolated_key = orig_val[2:-1]
    if interpolated_key.startswith("."):
        for i, c in enumerate(interpolated_key):
            if c != ".":
                prefix = ".".join(k.split(".")[:-i]) # rm i trailing subkeys
                suffix = interpolated_key[i:] # cut of leading dots
                if prefix:
                    return f"{prefix}.{suffix}"
                else:
                    return suffix
    else:
        return interpolated_key


def _follow_file_refs(conf_dict, conf_dir, prefix=None, verbose=True):
    loaded_files = {}
    for k, v in conf_dict.items():
        k_with_prefix = k if prefix is None else f"{prefix}.{k}"

        if type(v) == dict and "_file" in v:
            fn = v["_file"]
            if "." not in fn:
                fn += ".yaml"
            conf_fp = os.path.join(conf_dir, fn)
            conf_dict[k] = read_yaml(conf_fp, verbose=verbose)
            loaded_files[k_with_prefix] = conf_fp

        if type(conf_dict[k]) == dict:
            loaded_files.update(
                _follow_file_refs(conf_dict[k], conf_dir, prefix=k_with_prefix)
            )

    return loaded_files


def _load_types_dicts(loaded_conf_fps, verbose=True):
    ret = {}
    for k, conf_fp in loaded_conf_fps.items():
        types_fp = conf_fp.replace(".yaml", "_types.yaml")
        if os.path.exists(types_fp):
            ret[k] = read_yaml(types_fp, verbose=verbose)
    return ret


def _leaves_to_primitives(d):
    for k, v in d.items():
        if v in settings.PRIMITIVE_TYPES:
            continue
        elif type(v) == dict:
            _leaves_to_primitives(v)
        elif type(v) in settings.PRIMITIVE_TYPES:
            d[k] = settings.STR_TO_TYPE[v]
        else:
            raise Exception(
                f"Expected value of {k} to be a primitive (in {settings.PRIMITIVE_TYPES}), "
                f"but {v} is of type {type(v)}."
            )


def _get_cli_arg(arg_name, **kwargs):
    arg_name_sane = arg_name.replace("-", "_").replace(".", settings.DOT_REPLACEMENT)
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument(arg_name, dest=arg_name_sane, **kwargs)
    return getattr(parser.parse_known_args()[0], arg_name_sane)


class Conf:
    def __init__(
        self,
        conf=None,
        types=None,
        conf_files=None,
        conf_dir=settings.CONF_DIR,
        base_conf=settings.BASE_CONF,
        overrides=None,
        merge_mode="deep_merge",
        conf_patches=(),
        verbose=True,
        strict=False,
        env_overrides=True,
        env_overrides_prefix="CONFR_",
        cli_overrides=True,
        cli_overrides_prefix="--",
        validate_types=True,
        set_missing_types=True,
    ):

        self._plx_inputs = None
        self.merge_mode = merge_mode
        self.conf_patches = tuple(conf_patches) + self.conf_patches_overrides()
        self.verbose = verbose
        self.strict = strict
        self.c_singletons = {}
        self.c_original = {}
        self.overrides_dicts = aiocontextvars.ContextVar("overrides_dicts", default=[])

        conf_dicts, types_dicts, fps = [], [], []

        if conf:
            """Loads conf directly from conf dict."""
            if type(conf) == dict:
                conf_dicts.append(conf)
            elif type(conf) == list:
                conf_dicts.extend(conf)
            else:
                raise Exception(f"Unknown conf type of {type(conf)}.")
            assert conf_files is None, "Can't specify conf_files when using init(conf={...})."
            assert conf_patches == (), "Can't specify conf_patches when using init(conf={...})."
        elif conf_files:
            """Loads conf from conf files."""
            fps = [conf_files] if type(conf_files) == str else conf_files
        else:
            """Loads {conf_dir}/{base_conf}.yaml and all {conf_dir}/{conf_patch}.yaml files."""
            fps = [
                os.path.join(conf_dir, base + ".yaml")
                for base in ((base_conf,) if base_conf else tuple()) + self.conf_patches
            ]

        if types:
            if type(types) == list:
                types_dicts.extend(types)
            else:
                assert type(types) == dict
                types_dicts.append(types)

        for conf_fp in fps:
            conf_dicts.append(read_yaml(conf_fp, verbose=verbose))
            types_fp = conf_fp.replace(".yaml", "_types.yaml")
            if os.path.exists(types_fp) and ".yaml" in conf_fp:
                types_dicts.append(read_yaml(types_fp, verbose=verbose))

        for conf_dict in conf_dicts:
            self._init_conf_dict(conf_dict)

        if overrides:
            if verbose:
                print(f"Overwriting {len(overrides)} configs with `overrides`")
            # Merging with actual conf (rather than using self.add_overrides)
            # since these overrides are permanent (and self.add_overrides) is more limited.
            self._init_conf_dict(overrides)

        if env_overrides:
            self.override_from_env(env_overrides_prefix)
        if cli_overrides:
            self.override_from_cli(cli_overrides_prefix, file_refs_only=True)
        loaded_conf_fps = self.follow_file_refs(conf_dir)

        merged_types_dicts = _load_types_dicts(loaded_conf_fps, verbose=self.verbose)
        self.types = _deep_merge_dicts(types_dicts + [merged_types_dicts])
        _leaves_to_primitives(self.types)

        if validate_types:
            self.validate_types()
        if set_missing_types:
            self.set_missing_types()
        if cli_overrides:
            self.override_from_cli(cli_overrides_prefix)
        self.maybe_override_plx()

    def _init_conf_dict(self, conf_dict):
        for k, v in conf_dict.items():
            self.set(k, v)

    def override_from_env(self, env_overrides_prefix):
        for k, v in os.environ.items():
            if (
                k.startswith(env_overrides_prefix) and
                k not in ["CONFR_BASE_CONF", "CONFR_CONF_DIR"]
            ):
                k = unescape(k[len(env_overrides_prefix):])
                self.set(k, v)

    def override_from_cli(self, prefix, file_refs_only=False):
        parser = argparse.ArgumentParser(allow_abbrev=False, description='Override confr values.')

        for k, v in flattened_items(self.to_dict()):
            if file_refs_only:
                if k.endswith("_file"):
                    parser.add_argument(f"{prefix}{k}", dest=escape(k))
            else:
                parser.add_argument(f"{prefix}{k}", dest=escape(k), type=_get(self.types, k))

        args = vars(parser.parse_known_args()[0])
        args = {unescape(k_escaped): v for k_escaped, v in args.items() if v is not None}
        if args:
            print(f"Overriding {len(args)} arguments from CLI.")
            for k, v in args.items():
                self.set(k, v)

    def follow_file_refs(self, conf_dir):
        return _follow_file_refs(self.c_original, conf_dir, verbose=self.verbose)

    def get(self, k, default=None):
        use_singletons = True
        if k.startswith("&"):
            k = k[1:]
            use_singletons = False

        for overrides_dict in self.overrides_dicts.get()[::-1]:
            if k in overrides_dict:
                return self._get_val(k, overrides_dict[k])

        if use_singletons and _in(self.c_singletons, k):
            return _get(self.c_singletons, k)
        elif _in(self.c_original, k):
            return self._get_val(k, _get(self.c_original, k))
        else:
            if default is None:
                raise Exception(f"no config '{k}' found in {list(self.c_original.keys())}")
            else:
                return default

    def set(self, k, v, merge_mode=None):
        merge_mode = merge_mode if merge_mode else self.merge_mode
        _set(self.c_original, k, v, verbose=self.verbose, strict=self.strict, merge_mode=merge_mode)

    def __getitem__(self, k):
        return self.get(k)

    def __setitem__(self, k, v):
        self.set(k, v)

    def _get_val(self, k, orig_val):
        if k:
            assert k[0] != "."
            assert "/" not in k, f"Slashes no longer allowed in keys ({k})."

        if type(orig_val) == str:
            if _is_interpolation_val(orig_val):
                assert k is not None, "Not supported."
                return self.get(_interpolated_key(k, orig_val))
            elif orig_val.startswith("@"):
                if k is None:
                    # _get_val is called for a list element, therefore we can't memoize it
                    return self._get_python_ref(None, orig_val)
                else:
                    if _in(self.c_singletons, k):
                        return _get(self.c_singletons, k)
                    else:
                        # memoize the result
                        return _set(self.c_singletons, k, self._get_python_ref(orig_val))
            else:
                return orig_val
        elif type(orig_val) == list:
            # TODO handle int indexes
            return [self._get_val(None, v) for v in orig_val]
        elif type(orig_val) == dict and "_callable" in orig_val:
            return _set(self.c_singletons, k, self._get_python_ref_with_overrides(k, orig_val))
        elif type(orig_val) == dict and "." in k: # TODO this causes test_interpolation to fail
            return {
                k2: self._get_val(f"{k}.{k2}", v)
                for k2, v in orig_val.items()
            }
        else:
            return orig_val

    def _get_python_ref(self, orig_val):
        if orig_val.endswith("()"):
            return import_python_object(orig_val[1:-2])() # import and call without overrides
        else:
            return import_python_object(orig_val[1:]) # just import

    def _get_python_ref_with_overrides(self, k, orig_val):
        overrides = {}
        for k2, v in orig_val.items():
            if k2 != "_callable":
                overrides[k2] = self._get_val(f"{k}.{k2}", v)

        return import_python_object(orig_val["_callable"][1:-2])(**overrides)

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
        active_conf.update(deepcopy(self.c_original))
        if include_singletons:
            recursive_merge(self.c_singletons, active_conf)
        for overrides_dict in self.overrides_dicts.get():
            recursive_merge(overrides_dict, active_conf)
        return active_conf

    def validate_types(self):
        for k, expected_type in flattened_items(self.types):
            if _in(self.c_original, k):
                v = _get(self.c_original, k)
                assert expected_type == type(v), \
                    f"Expected {k} type to be {expected_type}, got {type(v)} for value {v}."

    def set_missing_types(self):
        for k, v in flattened_items(self.c_original):
            if not _in(self.types, k):
                assert type(v) in settings.PRIMITIVE_TYPES, \
                    f"{type(v)} not in settings.PRIMITIVE_TYPES ({settings.PRIMITIVE_TYPES})"
                _set(self.types, k, type(v))

    def maybe_override_plx(self):
        for k, v in self.plx_inputs.items():
            k = k.replace(settings.PLX_DOT_REPLACEMENT, ".")
            v = None if v == "" else v
            if _in(self.c_original, k):
                self.set(k, v)

    def conf_patches_overrides(self):
        # Can add overrides from other systems than plx here as well.
        plx_conf_patches = self.plx_inputs.get("conf_patches") or tuple()
        cli_conf_patches = _get_cli_arg("-c", action="append") or tuple()
        return tuple(plx_conf_patches) + tuple(cli_conf_patches)

    @property
    def plx_inputs(self):
        if self._plx_inputs is None:
            self._plx_inputs = plx.inputs()
        return self._plx_inputs


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
