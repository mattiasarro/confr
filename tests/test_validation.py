import os
from tempfile import TemporaryDirectory

import confr
from confr.test import validations
from confr.utils import write_yaml


def test_validate_batch_size():
    conf = {
        "batch_size": 32,
        "samples_per_batch": {
            "labelled": 16,
            "gen": {
                "generator1": 8,
                "generator2": 8,
            },
        },
    }
    confr.init(conf=conf, validate=validations, cli_overrides=False)
    confr.init(conf=conf, validate=[validations.validate_batch_size], cli_overrides=False)
    confr.init(conf=conf, validate=validations.validate_batch_size, cli_overrides=False)


def test_types_loading_dict():
    conf = {
        "batch_size": 32,
        "samples_per_batch": {
            "labelled": 16,
            "gen": {
                "generator1": 8,
                "generator2": 8,
            },
        },
    }
    t1 = {
        "batch_size": int
    }
    t2 = {
        "samples_per_batch": {
            "labelled": int,
            "gen": {
                "generator1": int,
            },
        },
    }
    t3 = {
        "samples_per_batch": {
            "gen": {
                "generator2": int,
            },
        },
    }
    confr.init(conf=conf, types=[t1, t2, t3], cli_overrides=False)
    types = confr.types()
    assert types == {
        "batch_size": int,
        "samples_per_batch": {
            "labelled": int,
            "gen": {
                "generator1": int,
                "generator2": int,
            },
        },
    }, types


def test_types_loading_files():
    with TemporaryDirectory() as conf_dir:
        conf = {
            "batch_size": 32,
            "samples_per_batch": {
                "labelled": 16,
                "gen": {
                    "generator1": 8,
                    "generator2": 8,
                },
            },
        }
        t1 = {
            "batch_size": int
        }
        t2 = {
            "samples_per_batch": {
                "labelled": int,
                "gen": {
                    "generator1": int,
                },
            },
        }
        t3 = {
            "samples_per_batch": {
                "gen": {
                    "generator2": "int",
                },
            },
        }

        conf_fp = os.path.join(conf_dir, "conf.yaml")
        t3_fp = os.path.join(conf_dir, "conf_types.yaml")
        write_yaml(conf_fp, conf)
        write_yaml(t3_fp, t3)

        confr.init(conf_files=conf_fp, types=[t1, t2], cli_overrides=False)
        types = confr.types()
        assert types == {
            "batch_size": int,
            "samples_per_batch": {
                "labelled": int,
                "gen": {
                    "generator1": int,
                    "generator2": "int", # this is a string due to loading from yaml
                },
            },
        }, types


def test_types_loading_file_refs():
    with TemporaryDirectory() as conf_dir:
        base_fp = os.path.join(conf_dir, f"{confr.settings.BASE_CONF}.yaml")
        shallow_fp = os.path.join(conf_dir, "shallow.yaml")
        deep_fp = os.path.join(conf_dir, "deep.yaml")
        refs_fp = os.path.join(conf_dir, "refs.yaml")
        v1_fp = os.path.join(conf_dir, "v1.yaml")
        v4_fp = os.path.join(conf_dir, "v4.yaml")

        write_yaml(
            base_fp,
            {
                "conf_key": 123,
                "neural_net": {
                    "_file": "shallow.yaml",
                    "this key": "is overridden",
                },
            },
        )
        write_yaml(
            shallow_fp,
            {"num_outputs": 10, "layer_sizes": [20]},
        )
        write_yaml(
            deep_fp,
            {"num_outputs": 10, "layer_sizes": [20, 15, 10, 15, 20]},
        )
        write_yaml(
            refs_fp,
            {"k1": {"_file": "v1.yaml"}},
        )
        write_yaml(
            v1_fp,
            {"k2": "v2", "k3": {"k4": {"_file": "v4.yaml"}}},
        )
        write_yaml(
            v4_fp,
            4,
        )

        base_types_fp = os.path.join(conf_dir, f"{confr.settings.BASE_CONF}_types.yaml")
        shallow_types_fp = os.path.join(conf_dir, "shallow_types.yaml")
        v4_types_fp = os.path.join(conf_dir, "v4_types.yaml")
        write_yaml(base_types_fp, {"conf_key": "int", "neural_net": {"this key": "str"}})
        write_yaml(shallow_types_fp, {"num_outputs": "int", "layer_sizes": "list"})
        write_yaml(v4_types_fp, "int")

        confr.init(conf_dir=conf_dir, cli_overrides=False)
        conf = confr.to_dict()
        types = confr.types()
        assert conf == {
            "conf_key": 123,
            "neural_net": {"num_outputs": 10, "layer_sizes": [20]},
        }, conf
        # "this key": "str" is kept in types, since we do deep merge of these
        assert types == {
            "conf_key": "int",
            "neural_net": {"num_outputs": "int", "layer_sizes": "list", "this key": "str"},
        }, types

        confr.init(
            conf_dir=conf_dir,
            overrides={"neural_net": {"_file": "deep.yaml", "this key": "is overridden"}}, # nested dict
            cli_overrides=False,
        )
        conf = confr.to_dict()
        types = confr.types()
        assert conf == {
            "conf_key": 123,
            "neural_net": {"num_outputs": 10, "layer_sizes": [20, 15, 10, 15, 20]},
        }, conf
        assert types == {
            "conf_key": "int",
            "neural_net": {"this key": "str"}, # deep_types.yaml does not exist
        }, types

        confr.init(
            conf_dir=conf_dir,
            overrides={"neural_net._file": "deep.yaml"}, # dot notation
            cli_overrides=False,
        )
        conf = confr.to_dict()
        types = confr.types()
        assert conf == {
            "conf_key": 123,
            "neural_net": {"num_outputs": 10, "layer_sizes": [20, 15, 10, 15, 20]},
        }, conf
        assert types == {
            "conf_key": "int",
            "neural_net": {"this key": "str"}, # deep_types.yaml does not exist
        }, types

        confr.init(
            conf_dir=conf_dir,
            overrides={"neural_net._file": "refs.yaml"},
            cli_overrides=False,
        )
        conf = confr.to_dict()
        types = confr.types()
        assert conf == {
            "conf_key": 123,
            "neural_net": {"k1": {"k2": "v2", "k3": {"k4": 4}}},
        }, conf
        assert types == {
            "conf_key": "int",
            "neural_net": {"this key": "str", "k1": {"k3": {"k4": "int"}}},
        }, types
