from confr.settings import PLX_DOT_REPLACEMENT, IN_POLYAXON


def enc_input(input_name):
    assert PLX_DOT_REPLACEMENT not in input_name, \
        f"'{PLX_DOT_REPLACEMENT}' not allowed in input name. " + \
        f"You can work around this by setting the PLX_DOT_REPLACEMENT env var."
    return input_name.replace(".", PLX_DOT_REPLACEMENT)


def dec_input(input_name):
    return input_name.replace(PLX_DOT_REPLACEMENT, ".")


def inputs():
    if IN_POLYAXON:
        print(f"Overriding arguments from Polyaxon since IN_POLYAXON={IN_POLYAXON}.")
        from polyaxon.client import RunClient

        try:
            run_client = RunClient()
            run_client.refresh_data()
        except:
            print("Could not initialise RunClient. Polyaxon configured?")
            return {}
        return run_client.get_inputs()

    else:
        return {}
