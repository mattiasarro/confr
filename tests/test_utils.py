from copy import deepcopy
from confr.utils import recursive_merge
from confr.test.imports import MyClass


def test_recursive_merge():
    d1 = {
        "k1": "d1_1",
        "k2": "d1_2",
        "k3": {
            "k4": {
                "k5": "d1_5",
                "k6": "d1_6",
            },
            "k7": "d1_7",
        },
    }
    d2 = {
        "k3": {
            "k4": "d2_v4",
            "k41": "d2_v41",
        }
    }

    d1_src = deepcopy(d1)
    d2_dst = deepcopy(d2)
    recursive_merge(d1_src, d2_dst)
    assert d2_dst == {
        "k1": "d1_1",
        "k2": "d1_2",
        "k3": {
            "k41": "d2_v41",
            "k4": {
                "k5": "d1_5",
                "k6": "d1_6",
            },
            "k7": "d1_7",
        },

    }, d2_dst

    d1_dst = deepcopy(d1)
    d2_src = deepcopy(d2)
    recursive_merge(d2_src, d1_dst)
    assert d1_dst == {
        "k1": "d1_1",
        "k2": "d1_2",
        "k3": {
            "k41": "d2_v41",
            "k4": "d2_v4",
            "k7": "d1_7",
        },

    }, d1_dst


def test_recursive_merge_inputs_unchanged():
    active_conf = {}
    c_original = {
        "parent_k1": "parent_v1",
        "k1": {
            "k2": {
                "encoder": "@confr.test.imports.get_encoder()",
                "encoder/num": 4,
            },
        },
        "num": 3,
        "another_model": "@confr.test.imports.get_encoder()",
    }
    c_singletons = {"k1": {"k2": {"encoder": MyClass(num=10)}}}
    c_singletons2 = {"k1": {"k2": {"encoder": MyClass(num=20)}}}

    active_conf.update(deepcopy(c_original))
    recursive_merge(c_singletons, active_conf)
    recursive_merge(c_singletons2, active_conf)

    assert c_original["k1"]["k2"]["encoder"] == "@confr.test.imports.get_encoder()", \
        c_original["k1"]["k2"]["encoder"]
    assert c_singletons["k1"]["k2"]["encoder"].num == 10, \
        c_singletons["k1"]["k2"]["encoder"].num
    assert c_singletons2["k1"]["k2"]["encoder"].num == 20, \
        c_singletons2["k1"]["k2"]["encoder"].num
    assert active_conf["k1"]["k2"]["encoder"].num == 20, \
        active_conf["k1"]["k2"]["encoder"].num
