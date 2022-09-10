# %% g1

import gin
import torch

@gin.configurable
def dnn(
    num_inputs,
    num_outputs,
    layer_sizes=[20, 10, 20],
    activation_fn=gin.CONFIGURED,
):
    return torch.nn.Sequential(...)

gin.parse_config_file('config.gin')
model = dnn(64)

# %% g2

dnn.layer_sizes = (1024, 512, 128)
path.to.mymodule.dnn.num_outputs = 10
dnn.activation_fn = @tf.nn.tanh

# %% h

import hydra
from omegaconf import DictConfig, OmegaConf

@hydra.main(
    version_base=None,
    config_path="conf",
    config_name="config",
)
def my_app(cfg : DictConfig) -> None:
    print(OmegaConf.to_yaml(cfg))

if __name__ == "__main__":
    my_app()

# %% o1

server:
  host: localhost
  port: 80
client:
  url: http://${server.host}:${server.port}/
  description: Client of ${.url}

# %% o2

conf = OmegaConf.load('conf.yaml')
assert conf.server == "localhost"
assert conf["client"]["description"] == \
    "Client of http://localhost:80/"

# %% c1

import confr
import torch

@confr.bind
def dnn(
    num_inputs, # not substituted by confr
    num_outputs=confr.value,
    layer_sizes=confr.value(default=[20, 10, 20]),
):
    return torch.nn.Sequential(...)

# same as confr.init(), reads conf/base.yaml
confr.init(conf_dir="conf", base_conf="base")
model = dnn(64)

# %% c2

num_outputs: 5
layer_sizes: [20, 15, 10, 15, 20]

# %% c3

num_chars: 10
neural_net:
    num_outputs: ${num_chars}
    layer_sizes: [20, 15, 10, 15, 20]

# %% c4

@confr.bind(subkeys="neural_net")
def dnn(
    num_outputs=confr.value,
    layer_sizes=confr.value(default=[20, 10, 20]),
):

# %% c5

@confr.bind
def dnn(
    num_outputs=confr.value("num_chars"),
    layer_sizes=confr.value("neural_net.layer_sizes"),
):

# %% c6

# config file
preprocessing_fn: @my.module.resize_and_crop

# Python code
@confr.bind
def predict(
    model,
    img,
    preprocessing_fn=confr.value,
):
    img = preprocessing_fn(img)
    return model(img)

# %% c7

@confr.bind
def get_model1(encoder=confr.value):
    return encoder

@confr.bind
def get_model2(model=confr.value("encoder")):
    return model

my_model1 = get_my_model1()
my_model2 = get_my_model2()
assert my_model1 == my_model2

# %% c8

my_model1: "@my.module.model1()"
my_model1/location: "/path/to/weights.h5"
my_model2: "@my.module.model2()"
my_model2/location: "/path/to/weights2.h5"

# %% c9

confr.init(
    base_conf="base",
    overrides={"override_key1": "v1"},
)

# %% c10

def precision(
    pred,
    lab,
    p_thresh=confr.value,
):
    ...

for p_thresh in p_thresholds:
    p = precision(pred, lab, p_thresh=p_thresh)

# %% c11

for p_thresh in p_thresholds:
    with confr.modified_conf(
        p_thresh=p_thresh
    ):
        p = precision(pred, lab)

# %% c12

# conf/base.yaml
conf_key: 123
neural_net:
    _file: shallow

# conf/neural_net/shallow.yaml
num_outputs: 10
layer_sizes: [20]

# conf/neural_net/deep.yaml
num_outputs: 10
layer_sizes: [20, 15, 10, 15, 20]

# %% c13

# conf/base.yaml
conf_key: 123
neural_net:
    num_outputs: 10
    layer_sizes: [20]

# %% c14

import confr

confr.init(conf={"key1": "val1"})

confr.get("key1") # returns "val1"
confr.set("key1", "overwritten")
confr.get("key1") # returns "overwritten"

# can also write novel keys
confr.set("key2", "val2")
confr.get("key2") # returns "val2"

# %% c15

confr.write_conf("my_active_conf.yaml)

# %% c16

# conf.yaml
num_chars: 10
neural_net:
    num_outputs: ${num_chars}
    layer_sizes: [20, 15, 10, 15, 20]

# conf_types.yaml
num_chars: int
neural_net:
    layer_sizes: list

# %% c17

batch_size: 32
samples_per_batch:
    labelled: 16
    gen:
        generator1: 8
        generator2: 8

# %% c18

# my/module/main.py
from my.module import conf_validation
confr.init(validate=conf_validation)

# my/module/conf_validation.py
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
