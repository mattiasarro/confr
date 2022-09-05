import confr

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
confr.init(conf=conf)

print(confr.to_dict())
