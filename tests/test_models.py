from copy import deepcopy
from confr.models import _in, _get, _set, _is_interpolation, _interpolated_key, _deep_merge_dicts


def test_in_dict():
    d = {"k": "v", "k2": {"k3": "v3"}}
    assert _in(d, "k")
    assert not _in(d, "k0")
    assert _in(d, "k2.k3")
    assert not _in(d, "k2.k4")


def test_get_dict():
    d = {"k": "v", "k2": {"k3": "v3"}}
    assert _get(d, "k") == "v"
    assert _get(d, "k0") is None
    assert _get(d, "k2.k3") == "v3"
    assert _get(d, "k2.k4") is None


def test_set_dict():
    d = {}
    _set(d, "k", "v")
    assert d == {"k": "v"}
    _set(d, "k2", {})
    assert d == {"k": "v", "k2": {}}
    _set(d, "k2.k3", "v3")
    assert d == {"k": "v", "k2": {"k3": "v3"}}


def test_set_dict_override():
    conf = {
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

    # only nested dict

    d = deepcopy(conf)
    _set(d, "k2", {"k4": "v4"}, merge_mode="override")
    assert d == {
        "k1": "v1",
        "k2": {"k4": "v4"},
    }, d

    d = deepcopy(conf)
    _set(d, "k2", {"k4": {"k7": "v7"}}, merge_mode="override")
    assert d == {
        "k1": "v1",
        "k2": {"k4": {"k7": "v7"}},
    }, d

    d = deepcopy(conf)
    _set(d, "k2", {"k4": {"k7": {"k9": "v9"}}}, merge_mode="override")
    assert d == {
        "k1": "v1",
        "k2": {"k4": {"k7": {"k9": "v9"}}},
    }, d

    # only dot notation, primitives at values (same behaviour as with deep_merge)

    d = deepcopy(conf)
    _set(d, "k2.k4", "v4", merge_mode="override")
    assert d == {
        "k1": "v1",
        "k2": {
            "k3": "v3",
            "k4": "v4",
        },
    }, d

    d = deepcopy(conf)
    _set(d, "k2.k4.k7", "v7", merge_mode="override")
    assert d == {
        "k1": "v1",
        "k2": {
            "k3": "v3",
            "k4": {
                "k5": "v5",
                "k6": "v6",
                "k7": "v7",
            },
        },
    }, d

    d = deepcopy(conf)
    _set(d, "k2.k4.k7.k9", "v9", merge_mode="override")
    assert d == {
        "k1": "v1",
        "k2": {
            "k3": "v3",
            "k4": {
                "k5": "v5",
                "k6": "v6",
                "k7": {
                    "k8": "v8",
                    "k9": "v9",
                },
            },
        },
    }, d

    # dot notation, dicts as values

    d = deepcopy(conf)
    _set(d, "k2.k4", {"k10": "v10"}, merge_mode="override")
    assert d == {
        "k1": "v1",
        "k2": {
            "k3": "v3",
            "k4": {"k10": "v10"},
        },
    }, d


def test_set_dict_deep_merge():
    conf = {
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

    # only nested dict

    d = deepcopy(conf)
    _set(d, "k2", {"k4": "v4"}, merge_mode="deep_merge")
    assert d == {
        "k1": "v1",
        "k2": {
            "k3": "v3",
            "k4": "v4",
        },
    }, d

    d = deepcopy(conf)
    _set(d, "k2", {"k4": {"k7": "v7"}}, merge_mode="deep_merge")
    assert d == {
        "k1": "v1",
        "k2": {
            "k3": "v3",
            "k4": {
                "k5": "v5",
                "k6": "v6",
                "k7": "v7",
            },
        },
    }, d

    d = deepcopy(conf)
    _set(d, "k2", {"k4": {"k7": {"k9": "v9"}}}, merge_mode="deep_merge")
    assert d == {
        "k1": "v1",
        "k2": {
            "k3": "v3",
            "k4": {
                "k5": "v5",
                "k6": "v6",
                "k7": {
                    "k8": "v8",
                    "k9": "v9",
                },
            },
        },
    }, d

    # only dot notation, primitives at values (same behaviour as with override)

    d = deepcopy(conf)
    _set(d, "k2.k4", "v4", merge_mode="deep_merge")
    assert d == {
        "k1": "v1",
        "k2": {
            "k3": "v3",
            "k4": "v4",
        },
    }, d

    d = deepcopy(conf)
    _set(d, "k2.k4.k7", "v7", merge_mode="deep_merge")
    assert d == {
        "k1": "v1",
        "k2": {
            "k3": "v3",
            "k4": {
                "k5": "v5",
                "k6": "v6",
                "k7": "v7",
            },
        },
    }, d

    d = deepcopy(conf)
    _set(d, "k2.k4.k7.k9", "v9", merge_mode="deep_merge")
    assert d == {
        "k1": "v1",
        "k2": {
            "k3": "v3",
            "k4": {
                "k5": "v5",
                "k6": "v6",
                "k7": {
                    "k8": "v8",
                    "k9": "v9",
                },
            },
        },
    }, d

    # dot notation, dicts as values

    d = deepcopy(conf)
    _set(d, "k2.k4", {"k10": "v10"}, merge_mode="deep_merge")
    assert d == {
        "k1": "v1",
        "k2": {
            "k3": "v3",
            "k4": {
                "k5": "v5",
                "k6": "v6",
                "k7": {
                    "k8": "v8",
                },
                "k10": "v10",
            },
        },
    }, d


def test_is_interpolation():
    conf = {
        "encoder": "@confr.test.imports.get_encoder()",
        "encoder/num": 4,
        "num": 3,
        "k1": {"k2": "${encoder}"},
        "k3": "${encoder}",
    }

    assert not _is_interpolation(conf, "encoder")
    assert not _is_interpolation(conf, "encoder/num")
    assert not _is_interpolation(conf, "num")
    assert _is_interpolation(conf, "k1.k2")
    assert _is_interpolation(conf, "k3")
    assert not _is_interpolation(conf, "k1.unknown")
    assert not _is_interpolation(conf, "unknown")


def test_interpolated_key():
    conf = {
        "k1": "v1",
        "k2": {
            "k3": "v3",
            "k4": {
                "k5": "${..k3}", # => "v3"
                "k6": "${...k10.k11}", # => "v11"
                "k7": {
                    "k8": "v8",
                },
            },
            "k9": "${.k3}", # => "v3"
        },
        "k10": {
            "k11": "v11",
        },
    }
    assert _interpolated_key("k2.k9", "${.k3}") == "k2.k3"
    assert _interpolated_key("k2.k4.k5", "${..k3}") == "k2.k3"
    assert _interpolated_key("k2.k4.k6", "${...k10.k11}") == "k10.k11"


def test_deep_merge_dicts():
    d1 = {
        "k1": "v1",
    }
    d2 = {
        "k2": "v2",
        "k4": {
            "k5": "v5",
        },
        "k6": {
            "k7": "v7",
        },
        "k8": {
            "k9": "v9",
        },
        "k10": {
            "k11": {
                "k12": "v12",
            },
        },
    }
    d3 = {
        "k3": "v3",
        "k6": {
            "k7": "v7_overridden",
        },
        "k8.k9": "v9_overridden",
        "k10.k11": "v11",
    }
    ret = _deep_merge_dicts([d1, d2, d3])
    assert ret == {
        "k1": "v1",
        "k2": "v2",
        "k4": {
            "k5": "v5",
        },
        "k6": {
            "k7": "v7_overridden",
        },
        "k8": {
            "k9": "v9_overridden",
        },
        "k3": "v3",
        "k10": {
            "k11": "v11",
        },
    }, ret
