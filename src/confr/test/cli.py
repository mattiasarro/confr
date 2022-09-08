import confr

conf = {
    "k1": "v1",
    "k2": {
        "k3": "v3",
        "k4": {
            "k5": "v5",
            "k6": "v6",
            "k7": {
                "k8": 8,
            },
        },
    },
    "k9": {"_file": "ref1.yaml"},
}
types = {"k2.k4.k7.k8": int}
confr.init(conf=conf, types=types, conf_dir="tests/config")

print(confr.to_dict())
