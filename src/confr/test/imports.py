import confr


class MyClass:
    def __init__(self, num):
        self.num = num


def my_fn():
    return 123


@confr.bind
def get_encoder(num=confr.value):
    return MyClass(num)


def get_dict():
    return {1: 1, 2: "@something()"}
