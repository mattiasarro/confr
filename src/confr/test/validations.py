import confr


@confr.bind
def validate_batch_size(
    batch_size=confr.value,
    samples_per_batch=confr.value,
):
    assert batch_size == (
        samples_per_batch["labelled"] +
        sum(samples_per_batch["gen"].values())
    )
