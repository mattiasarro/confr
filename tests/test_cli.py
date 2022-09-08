import subprocess
import ast


def _cli(args={}, prefix="--"):
    cmd = ["python", "-m", "confr.test.cli"]
    for k, v in args.items():
        cmd.extend([f"{prefix}{k}", str(v)])
    out = subprocess.check_output(cmd).decode("utf-8")
    print(out)
    return ast.literal_eval(out.split("\n")[-2])


def test_root_key():
    ret = _cli({"k1": "my_val"})
    assert ret["k1"] == "my_val"


def test_nested_key():
    ret = _cli({"k2.k3": "my_val"})
    assert ret["k2"]["k3"] == "my_val"

    ret = _cli({"k2.k4.k5": "my_val"})
    assert ret["k2"]["k4"]["k5"] == "my_val"


def test_type_conversion():
    ret = _cli()
    assert ret["k2"]["k4"]["k7"]["k8"] == 8

    ret = _cli({"k2.k4.k7.k8": 9})
    assert ret["k2"]["k4"]["k7"]["k8"] == 9
