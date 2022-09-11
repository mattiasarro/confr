import os

CONF_DIR = os.environ.get("CONFR_CONF_DIR", "config")
BASE_CONF = os.environ.get("CONFR_BASE_CONF", "_base")
CLI_DOT_REPLACEMENT = os.environ.get("CLI_DOT_REPLACEMENT", "___")
PLX_DOT_REPLACEMENT = os.environ.get("PLX_DOT_REPLACEMENT", "___")
IN_POLYAXON = int(os.environ.get("IN_POLYAXON", 0))


PRIMITIVE_TYPES = [int, float, str, list]
STR_TO_TYPE = {
    "int": int,
    "float": float,
    "str": str,
    "list": list,
}
