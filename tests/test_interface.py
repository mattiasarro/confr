# %%
import os
from tempfile import NamedTemporaryFile, TemporaryDirectory

import confr
from confr.utils import read_yaml


@confr.bind
def myfn(key1=confr.value):
    return key1


@confr.bind
def fn_custom_key(key1=confr.value("key2")):
    return key1


@confr.bind
def fn_default(key1=confr.value(default="default")):
    return key1


@confr.bind
def fn_custom_key_and_default(key1=confr.value("key2", default="default")):
    return key1


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


def test_conf_get_set():
    confr.init(conf={"key1": "val1"})
    assert confr.get("key1") == myfn() == "val1", (myfn(), type(myfn()))

    confr.set("key1", "val2")
    assert confr.get("key1") == myfn() == "val2"


def test_bind_fn():
    confr.init(conf={"key1": "val1"})
    assert myfn() == "val1"
    assert myfn(key1="val2") == "val2"


def test_custom_key():
    confr.init(conf={"key1": "val1", "key2": "val2"})
    assert fn_custom_key() == "val2"
    assert fn_custom_key(key1="val3") == "val3"


def test_default():
    confr.init(conf={"other_key": "other_val"}) # ensure we init from dict, rather than dir
    assert fn_default() == "default"

    confr.init(conf={"key1": "val1"})
    assert fn_default() == "val1"


def test_custom_key_and_default():
    confr.init(conf={"key1": "val1", "key2": "val2"})
    assert fn_custom_key_and_default() == "val2"
    assert fn_custom_key_and_default(key1="val3") == "val3"

    confr.init(conf={"other_key": "other_val"}) # ensure we init from dict, rather than dir
    assert fn_custom_key_and_default() == "default"

    confr.init(conf={"key2": "val2"})
    assert fn_custom_key_and_default() == "val2"


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


def test_modified_conf():
    confr.init(conf={"key1": "val1"})
    assert myfn() == "val1"
    with confr.modified_conf(key1="val2"):
        assert myfn() == "val2"
    assert myfn() == "val1"


def test_conf_from_files():
    with NamedTemporaryFile() as f:
        f.write("key1: val1".encode("utf-8"))
        f.flush()

        confr.init(conf_files=[f.name])
        assert myfn() == "val1"


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
        assert myfn() == "val1"

        confr.init(
            conf_dir=conf_dir,
            base_conf="conf1",
            overrides={"key1": "overwritten"},
        )
        assert myfn() == "overwritten"

        confr.init(
            conf_dir=conf_dir,
            base_conf="conf1",
            conf_patches=["conf2"],
        )
        assert myfn() == "val2"

        confr.init(
            conf_dir=conf_dir,
            base_conf="conf1",
            conf_patches=["conf2"],
            overrides={"key1": "overwritten"},

        )
        assert myfn() == "overwritten"


def test_write_conf_file():
    with TemporaryDirectory() as tmp_dir:
        confr.init(conf={"key1": "val1"})
        confr.set("key2", "val2")

        conf_fn = os.path.join(tmp_dir, "conf.yaml")

        confr.write_conf_file(conf_fn)
        assert read_yaml(conf_fn) == {"key1": "val1", "key2": "val2"}

        confr.write_conf_file(conf_fn, except_keys=["key1"])
        assert read_yaml(conf_fn) == {"key2": "val2"}


# test_conf_get_set()
# test_bind_fn()
# test_bind_class()
# test_modified_conf()
# test_conf_from_files()
# test_conf_from_dir()
# test_write_conf_file()

# %%
