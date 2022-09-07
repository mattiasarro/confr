import os

CONF_DIR = os.environ.get("CONFR_CONF_DIR", "config")
BASE_CONF = os.environ.get("CONFR_BASE_CONF", "_base")

PRIMITIVE_TYPES = [int, float, str, list]
STR_TO_TYPE = {
    "int": int,
    "float": float,
    "str": str,
    "list": list,
}
