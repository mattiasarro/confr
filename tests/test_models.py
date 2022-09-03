from confr.models import _in, _get, _set, _is_interpolation


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


def test_is_interpolation():
    conf = {
        "encoder": "@confr.test_imports.get_encoder()",
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
