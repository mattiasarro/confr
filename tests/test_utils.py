from copy import deepcopy
from confr.utils import recursive_merge


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
