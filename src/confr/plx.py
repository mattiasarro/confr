from confr.settings import PLX_DOT_REPLACEMENT


def enc_input(input_name):
    assert PLX_DOT_REPLACEMENT not in input_name, \
        f"'{PLX_DOT_REPLACEMENT}' not allowed in input name. " + \
        f"You can work around this by setting the PLX_DOT_REPLACEMENT env var."
    return input_name.replace(".", PLX_DOT_REPLACEMENT)


def dec_input(input_name):
    return input_name.replace(PLX_DOT_REPLACEMENT, ".")
