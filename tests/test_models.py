from confr.models import _in, _get, _set


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
