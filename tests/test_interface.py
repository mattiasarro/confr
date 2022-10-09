# %%
import os
from copy import deepcopy
from tempfile import NamedTemporaryFile, TemporaryDirectory

import confr
from confr import settings
from confr.utils import read_yaml, write_yaml


# mock functions #


@confr.bind
def fn1(key1=confr.value):
    return key1


@confr.bind(subkeys="nested")
def fn1_subkeys(key1=confr.value):
    return key1


@confr.bind
def fn_custom_key(key1=confr.value("key2")):
    return key1


@confr.bind
def fn_custom_key_deep(key1=confr.value("k1.k2.k3")):
    return key1


@confr.bind
def fn_default(key1=confr.value(default="default")):
    return key1


@confr.bind
def fn_custom_key_and_default(key1=confr.value("key2", default="default")):
    return key1


@confr.bind
def fn_python_reference(preprocessing_fn=confr.value):
    return preprocessing_fn()


@confr.bind
def get_model1(encoder=confr.value):
    return encoder


@confr.bind
def get_model2(model=confr.value("encoder")):
    return model


@confr.bind(subkeys="k1.k2")
def get_model3(encoder=confr.value):
    return encoder


@confr.bind
def get_model4(model=confr.value("k1.k2.encoder")):
    return model


@confr.bind
def get_sth(sth=confr.value):
    return sth


@confr.bind
class MyClass:
    def __init__(self, key1=confr.value):
        self.key1 = key1

    @confr.bind
    def my_method1(self, key1=None, key2=confr.value):
        return self.key1, key1, key2

    # notice this method is not annotated with @confr.bind
    def my_method2(self, key1=None, key2=confr.value):
        return self.key1, key1, key2


# tests #


def test_conf_get_set():
    confr.init(conf={"key1": "val1"}, cli_overrides=False)
    assert confr.get("key1") == fn1() == "val1", (fn1(), type(fn1()))

    confr.set("key1", "val2")
    assert confr.get("key1") == fn1() == "val2"


def test_bind_fn():
    confr.init(conf={"key1": "val1"}, cli_overrides=False)
    assert fn1() == "val1"
    assert fn1(key1="val2") == "val2"


def test_bind_class():
    confr.init(conf={"key1": "val1", "key2": "val2"}, cli_overrides=False)

    o = MyClass(key1="val1")
    assert o.key1 == "val1"
    assert o.my_method1() == ("val1", None, "val2")
    assert o.my_method2() == ("val1", None, confr.value)

    assert o.my_method1(key1="a") == ("val1", "a", "val2")
    assert o.my_method2(key1="a") == ("val1", "a", confr.value)
    assert o.my_method1(key1="a", key2="b") == ("val1", "a", "b")
    assert o.my_method2(key1="a", key2="b") == ("val1", "a", "b")


def test_bind_fn_subkeys():
    confr.init(conf={"key1": "val1", "nested": {"key1": "nested1"}}, cli_overrides=False)

    assert fn1() == "val1"
    assert fn1(key1="val2") == "val2"

    assert fn1_subkeys() == "nested1"
    assert fn1_subkeys(key1="val2") == "val2"


def test_value_custom_key():
    confr.init(conf={"key1": "val1", "key2": "val2"}, cli_overrides=False)
    assert fn_custom_key() == "val2"
    assert fn_custom_key(key1="val3") == "val3"


def test_value_custom_key_deep():
    confr.init(conf={"key1": "val1", "key2": "val2", "k1": {"k2": {"k3": "v3"}}}, cli_overrides=False)
    assert fn_custom_key_deep() == "v3"
    assert fn_custom_key_deep(key1="val3") == "val3"


def test_value_default():
    confr.init(conf={"other_key": "other_val"}, cli_overrides=False) # ensure we init from dict, rather than dir
    assert fn_default() == "default"

    confr.init(conf={"key1": "val1"}, cli_overrides=False)
    assert fn_default() == "val1"


def test_value_custom_key_and_default():
    confr.init(conf={"key1": "val1", "key2": "val2"}, cli_overrides=False)
    assert fn_custom_key_and_default() == "val2"
    assert fn_custom_key_and_default(key1="val3") == "val3"

    confr.init(conf={"other_key": "other_val"}, cli_overrides=False) # ensure we init from dict, rather than dir
    assert fn_custom_key_and_default() == "default"

    confr.init(conf={"key2": "val2"}, cli_overrides=False)
    assert fn_custom_key_and_default() == "val2"


def test_python_reference():
    confr.init(conf={"preprocessing_fn": "@confr.test.imports.my_fn"}, cli_overrides=False)
    assert fn_python_reference() == 123


def test_singleton_without_overrides():
    conf = {
        "my_obj": "@confr.test.imports.MySimpleClass()",
    }
    confr.init(conf=conf, cli_overrides=False)

    assert confr.get("my_obj").name == "MySimpleClass"


def test_singleton_with_overrides():
    conf = {
        "encoder": {
            "_callable": "@confr.test.imports.get_encoder()",
            "num": 4,
        },
        "num": 3,
    }
    confr.init(conf=conf, cli_overrides=False)

    my_model1 = get_model1()
    my_model2 = get_model2()
    assert my_model1 == my_model2
    assert my_model1.num == my_model2.num == 4


def test_singleton_nested():
    # This is/was a known failure mode which caused to_dict() to return singletons
    # instead of original string representations.

    conf = {
        "parent_k1": "parent_v1",
        "k1": {
            "k2": {
                "encoder": {
                    "_callable": "@confr.test.imports.get_encoder()",
                    "num": 4,
                },
            },
        },
        "num": 3,
        "another_model": "@confr.test.imports.get_encoder()",
    }
    confr.init(conf=conf, cli_overrides=False)

    confr.get("k1.k2.encoder")
    confr.get("another_model")

    my_model3 = get_model3()
    my_model4 = get_model4()
    assert my_model3 == my_model4
    assert my_model3.num == my_model4.num == 4

    d = confr.to_dict()
    assert d["k1"]["k2"]["encoder"] == {
        "_callable": "@confr.test.imports.get_encoder()",
        "num": 4,
    }
    assert d["another_model"] == "@confr.test.imports.get_encoder()"


def test_interpolation():
    conf = {
        "k1": "v1",
        "k2": {"k21": "v21", "k22": "${k1}", "k23": "${.k21}", "k24": "${..k1}"},
    }
    confr.init(conf=conf, cli_overrides=False)

    assert confr.get("k1") == "v1"
    assert confr.get("k2") == {"k21": "v21", "k22": "v1", "k23": "v21", "k24": "v1"}
    assert confr.get("k2.k21") == "v21"
    assert confr.get("k2.k22") == "v1"


def test_interpolation_singleton():
    conf = {
        "encoder": {
            "_callable": "@confr.test.imports.get_encoder()",
            "num": 4,
        },
        "num": 3,
        "k1": {"k2": "${encoder}"},
        "my": {
            "encoder": {
                "_callable": "@confr.test.imports.get_encoder()",
                "num": 5,
            },
        },
    }
    confr.init(conf=conf, cli_overrides=False)

    my_model1 = get_model1()
    my_model2 = get_model2()
    encoder = confr.get("encoder")
    k1_k2 = confr.get("k1.k2")
    my_encoder = confr.get("my.encoder")

    assert my_encoder.num == 5
    assert my_model1.num == my_model2.num == encoder.num == k1_k2.num == 4
    assert my_model1 == my_model2 == encoder == k1_k2
    assert my_encoder != my_model1 and my_encoder != my_model2 and my_encoder != k1_k2


def test_modified_conf():
    conf = {
        "key1": "val1",
        "encoder": {
            "_callable": "@confr.test.imports.get_encoder()",
            "num": 3,
        },
    }

    confr.init(conf=conf, cli_overrides=False)
    assert fn1() == "val1"
    assert confr.get("encoder").num == 3

    with confr.modified_conf(key1="val2", sth="${encoder}", overrides={"encoder/num": 4}):
        assert fn1() == "val2"
        # Here, `sth` points to `encoder`, which had been initialised earlier and memoized.
        # Therefore, encoder does not get re-initialised with num=4.
        # TODO add a warning or exception when such overrides are attempted.
        assert confr.get("sth").num == 3

    assert fn1() == "val1"


def test_conf_context():
    conf1 = {
        "key1": "val1",
        "encoder": {
            "_callable": "@confr.test.imports.get_encoder()",
            "num": 3,
        },
    }
    conf2 = {
        "key1": "val2",
        "encoder": {
            "_callable": "@confr.test.imports.get_encoder()",
            "num": 4,
        },
    }

    confr.init(conf=conf1, cli_overrides=False)
    assert fn1() == "val1"
    assert confr.get("encoder").num == 3

    with confr.init(conf=conf2, cli_overrides=False, ctx=True):
        assert fn1() == "val2"
        assert confr.get("encoder").num == 4

    assert fn1() == "val1"
    assert confr.get("encoder").num == 3


def test_init_deep_merge():
    conf1 = {
        "k1": "v1",
        "k2": {
            "k3": "v3",
            "k4": {
                "k5": "v5",
                "k6": "v6",
                "k7": {
                    "k8": "v8",
                },
            },
        },
    }
    conf2 = {
        "k2": {
            "k3": "v3_changed",
            "k4": {
                "k6": "v6_changed",
                "k7": "v7",
            },
        },
    }
    conf3 = {"k2.k4.k6": "v6_changed2", "unknown": {"key": "val"}}
    confr.init(conf=[conf1, conf2, conf3], cli_overrides=False)

    d = confr.to_dict()
    assert d == {
        "k1": "v1",
        "k2": {
            "k3": "v3_changed",
            "k4": {
                "k5": "v5",
                "k6": "v6_changed2",
                "k7": "v7",
            },
        },
        "unknown": {"key": "val"},
    }, d


def test_init_conf_patches():
    conf_base = {
        "k1": "v1",
        "k2": {
            "k3": "v3",
            "k4": {
                "k5": "v5",
                "k6": "v6",
                "k7": {
                    "k8": "v8",
                },
            },
            "k9": "v9",
        },
    }
    cp1 = {
        "k2": {
            "k3": "v3_changed",
            "k4": {
                "k6": "v6_changed",
                "k7": "v7",
            },
        },
    }
    cp2 = {"k2.k4.k6": "v6_changed2", "unknown": {"key": "val"}}

    with TemporaryDirectory() as conf_dir:
        write_yaml(os.path.join(conf_dir, f"{settings.BASE_CONF}.yaml"), conf_base)
        write_yaml(os.path.join(conf_dir, "cp1.yaml"), cp1)
        write_yaml(os.path.join(conf_dir, "cp2.yaml"), cp2)

        confr.init(conf_dir=conf_dir, conf_patches=("cp1", "cp2"), cli_overrides=False)

        d = confr.to_dict()
        assert d == {
            "k1": "v1",
            "k2": {
                "k3": "v3_changed",
                "k4": {
                    "k5": "v5",
                    "k6": "v6_changed2",
                    "k7": "v7",
                },
                "k9": "v9",
            },
            "unknown": {"key": "val"},
        }, d


def test_init_override():
    conf1 = {
        "k1": "v1",
        "k2": {
            "k3": "v3",
            "k4": {
                "k5": "v5",
                "k6": "v6",
                "k7": {
                    "k8": "v8",
                },
            },
        },
    }
    conf2 = {
        "k2": {
            "k3": "v3_changed",
            "k4": {
                "k6": "v6_changed",
                "k7": "v7",
            },
        },
    }
    conf3 = {"k2.k4.k6": "v6_changed2", "unknown": {"key": "val"}}
    confr.init(conf=[conf1, conf2, conf3], merge_mode="override", cli_overrides=False)

    d = confr.to_dict()
    assert d == {
        "k1": "v1",
        "k2": {
            "k3": "v3_changed",
            "k4": {
                "k6": "v6_changed2",
                "k7": "v7",
            },
        },
        "unknown": {"key": "val"},
    }, d


def test_conf_from_files():
    with NamedTemporaryFile() as f:
        f.write("key1: val1".encode("utf-8"))
        f.flush()

        confr.init(conf_files=[f.name], cli_overrides=False)
        assert fn1() == "val1"


def test_conf_from_dir():
    with TemporaryDirectory() as conf_dir:
        conf1_fp = os.path.join(conf_dir, "conf1.yaml")
        conf2_fp = os.path.join(conf_dir, "conf2.yaml")
        write_yaml(conf1_fp, {"key1": "val1"})
        write_yaml(conf2_fp, {"key1": "val2"})

        confr.init(
            conf_dir=conf_dir,
            base_conf="conf1",
            cli_overrides=False,
        )
        assert fn1() == "val1"

        confr.init(
            conf_dir=conf_dir,
            base_conf="conf1",
            overrides={"key1": "overwritten"},
            cli_overrides=False,
        )
        assert fn1() == "overwritten"

        confr.init(
            conf_dir=conf_dir,
            base_conf="conf1",
            conf_patches=["conf2"],
            cli_overrides=False,
        )
        assert fn1() == "val2"

        confr.init(
            conf_dir=conf_dir,
            base_conf="conf1",
            conf_patches=["conf2"],
            overrides={"key1": "overwritten"},
            cli_overrides=False,
        )
        assert fn1() == "overwritten"


def test_conf_from_dir_composed():
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

        confr.init(conf_dir=conf_dir, cli_overrides=False)
        conf = confr.to_dict()
        assert conf == {
            "conf_key": 123,
            "neural_net": {"num_outputs": 10, "layer_sizes": [20]},
        }, conf

        confr.init(
            conf_dir=conf_dir,
            overrides={"neural_net": {"_file": "deep.yaml", "this key": "is overridden"}}, # nested dict
            cli_overrides=False,
        )
        conf = confr.to_dict()
        assert conf == {
            "conf_key": 123,
            "neural_net": {"num_outputs": 10, "layer_sizes": [20, 15, 10, 15, 20]},
        }, conf

        confr.init(
            conf_dir=conf_dir,
            overrides={"neural_net._file": "deep.yaml"}, # dot notation
            cli_overrides=False,
        )
        conf = confr.to_dict()
        assert conf == {
            "conf_key": 123,
            "neural_net": {"num_outputs": 10, "layer_sizes": [20, 15, 10, 15, 20]},
        }, conf

        confr.init(
            conf_dir=conf_dir,
            overrides={"neural_net._file": "refs.yaml"},
            cli_overrides=False,
        )
        conf = confr.to_dict()
        assert conf == {
            "conf_key": 123,
            "neural_net": {"k1": {"k2": "v2", "k3": {"k4": 4}}},
        }, conf


def test_write_conf():
    with TemporaryDirectory() as tmp_dir:
        confr.init(conf={"key1": "val1"}, cli_overrides=False)
        confr.set("key2", "val2")

        conf_fn = os.path.join(tmp_dir, "conf.yaml")

        confr.write_conf(conf_fn)
        assert read_yaml(conf_fn) == {"key1": "val1", "key2": "val2"}

        confr.write_conf(conf_fn, except_keys=["key1"])
        assert read_yaml(conf_fn) == {"key2": "val2"}

        confr.set("key3", {"key4": "val4", "key5": "val5"})

        confr.write_conf(conf_fn, except_keys=["key3.key4"])
        assert read_yaml(conf_fn) == {"key1": "val1", "key2": "val2", "key3": {"key5": "val5"}}

        confr.write_conf(conf_fn, except_keys=["key3.key4", "key3.key5"])
        assert read_yaml(conf_fn) == {"key1": "val1", "key2": "val2", "key3": {}}


def test_write_conf_with_interpolations():
    with TemporaryDirectory() as tmp_dir:
        conf = {
            "encoder_fn": "@confr.test.imports.get_encoder",
            "encoder": "@confr.test.imports.get_encoder()",
            "encoder/num": 4,
            "num": 3,
            "k1": {"k2": "${encoder}"},
            "my": {
                "encoder": "@confr.test.imports.get_encoder()",
                "encoder/num": 5,
            },
        }
        conf_orig = deepcopy(conf)
        confr.init(conf=conf, cli_overrides=False)

        # ensure singletons are initialised
        get_model1()
        get_model2()
        confr.get("encoder_fn")
        confr.get("encoder")
        confr.get("k1.k2")
        confr.get("my.encoder")

        conf_fn = os.path.join(tmp_dir, "conf.yaml")
        confr.write_conf(conf_fn)
        assert read_yaml(conf_fn) == conf_orig


# %%
