# %%
import os
from tempfile import NamedTemporaryFile, TemporaryDirectory

import confr
from confr.utils import read_yaml


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
    confr.init(conf={"key1": "val1"})
    assert confr.get("key1") == fn1() == "val1", (fn1(), type(fn1()))

    confr.set("key1", "val2")
    assert confr.get("key1") == fn1() == "val2"


def test_bind_fn():
    confr.init(conf={"key1": "val1"})
    assert fn1() == "val1"
    assert fn1(key1="val2") == "val2"


def test_bind_class():
    confr.init(conf={"key1": "val1", "key2": "val2"})

    o = MyClass(key1="val1")
    assert o.key1 == "val1"
    assert o.my_method1() == ("val1", None, "val2")
    assert o.my_method2() == ("val1", None, confr.value)

    assert o.my_method1(key1="a") == ("val1", "a", "val2")
    assert o.my_method2(key1="a") == ("val1", "a", confr.value)
    assert o.my_method1(key1="a", key2="b") == ("val1", "a", "b")
    assert o.my_method2(key1="a", key2="b") == ("val1", "a", "b")


def test_bind_fn_subkeys():
    confr.init(conf={"key1": "val1", "nested": {"key1": "nested1"}})

    assert fn1() == "val1"
    assert fn1(key1="val2") == "val2"

    assert fn1_subkeys() == "nested1"
    assert fn1_subkeys(key1="val2") == "val2"


def test_value_custom_key():
    confr.init(conf={"key1": "val1", "key2": "val2"})
    assert fn_custom_key() == "val2"
    assert fn_custom_key(key1="val3") == "val3"


def test_value_custom_key_deep():
    confr.init(conf={"key1": "val1", "key2": "val2", "k1": {"k2": {"k3": "v3"}}})
    assert fn_custom_key_deep() == "v3"
    assert fn_custom_key_deep(key1="val3") == "val3"


def test_value_default():
    confr.init(conf={"other_key": "other_val"}) # ensure we init from dict, rather than dir
    assert fn_default() == "default"

    confr.init(conf={"key1": "val1"})
    assert fn_default() == "val1"


def test_value_custom_key_and_default():
    confr.init(conf={"key1": "val1", "key2": "val2"})
    assert fn_custom_key_and_default() == "val2"
    assert fn_custom_key_and_default(key1="val3") == "val3"

    confr.init(conf={"other_key": "other_val"}) # ensure we init from dict, rather than dir
    assert fn_custom_key_and_default() == "default"

    confr.init(conf={"key2": "val2"})
    assert fn_custom_key_and_default() == "val2"


def test_python_reference():
    confr.init(conf={"preprocessing_fn": "@confr.test_imports.my_fn"})
    assert fn_python_reference() == 123


def test_singleton():
    conf = {
        "encoder": "@confr.test_imports.get_encoder()",
        "encoder/num": 4,
        "num": 3,
    }
    confr.init(conf=conf)

    my_model1 = get_model1()
    my_model2 = get_model1()
    assert my_model1 == my_model2
    assert my_model1.num == my_model2.num == 4


def test_interpolation():
    conf = {
        "k1": "v1",
        "k2": {"k21": "v21", "k22": "${k1}"},
    }
    confr.init(conf=conf)

    assert confr.get("k1") == "v1"
    assert confr.get("k2") == {"k21": "v21", "k22": "v1"}
    assert confr.get("k2.k21") == "v21"
    assert confr.get("k2.k22") == "v1"


def test_interpolation_singleton():
    conf = {
        "encoder": "@confr.test_imports.get_encoder()",
        "encoder/num": 4,
        "num": 3,
        "k1": {"k2": "${encoder}"},
        "my": {
            "encoder": "@confr.test_imports.get_encoder()",
            "encoder/num": 5,
        },
    }
    confr.init(conf=conf)

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
    confr.init(conf={"key1": "val1"})
    assert fn1() == "val1"
    with confr.modified_conf(key1="val2"):
        assert fn1() == "val2"
    assert fn1() == "val1"


def test_conf_from_files():
    with NamedTemporaryFile() as f:
        f.write("key1: val1".encode("utf-8"))
        f.flush()

        confr.init(conf_files=[f.name])
        assert fn1() == "val1"


def test_conf_from_dir():
    with TemporaryDirectory() as conf_dir:
        conf1 = os.path.join(conf_dir, "conf1.yaml")
        conf2 = os.path.join(conf_dir, "conf2.yaml")
        with open(conf1, "w") as f:
            f.write("key1: val1")
        with open(conf2, "w") as f:
            f.write("key1: val2")

        confr.init(
            conf_dir=conf_dir,
            base_conf="conf1",
        )
        assert fn1() == "val1"

        confr.init(
            conf_dir=conf_dir,
            base_conf="conf1",
            overrides={"key1": "overwritten"},
        )
        assert fn1() == "overwritten"

        confr.init(
            conf_dir=conf_dir,
            base_conf="conf1",
            conf_patches=["conf2"],
        )
        assert fn1() == "val2"

        confr.init(
            conf_dir=conf_dir,
            base_conf="conf1",
            conf_patches=["conf2"],
            overrides={"key1": "overwritten"},

        )
        assert fn1() == "overwritten"


def test_write_conf_file():
    # TODO test writing singleton and python reference
    # TODO test writing interpolation, interpolation to singleton
    with TemporaryDirectory() as tmp_dir:
        confr.init(conf={"key1": "val1"})
        confr.set("key2", "val2")

        conf_fn = os.path.join(tmp_dir, "conf.yaml")

        confr.write_conf_file(conf_fn)
        assert read_yaml(conf_fn) == {"key1": "val1", "key2": "val2"}

        confr.write_conf_file(conf_fn, except_keys=["key1"])
        assert read_yaml(conf_fn) == {"key2": "val2"}


# %%
