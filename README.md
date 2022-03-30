# confr

Configuration system geared towards Python machine learning projects.

## Installation

Either run:

```
pip install git+https://github.com/mattiasarro/confr.git
```

Or add `git+https://github.com/mattiasarro/confr.git` to `requirements.txt` and execute ` pip install -r requirements.txt`, as usual.

## Usage

The idea behind confr is to keep configuration about a ML project (trainer script + inference code) in one or more configuration files. The configuration files (currently just `yaml`) will contain key-value pairs, which will be mapped 1-to-1 to keyword arguments in Python code.

For example, assume we have a config file in `/path/to/project/config/_base.yaml` with the following content:
```yaml
my_config_key1: value 1
my_config_key2: [1, 2, 3]
```

And in some Python program you can do the following:

```python
import confr
confr.conf_from_files(["/path/to/project/config/_base.yaml"])

@confr.configured
def my_function(a, my_config_key1=confr.CONFIGURED):
    return a, my_config_key1

@confr.configured
class MyClass:
    def __init__(self, a, my_config_key1=confr.CONFIGURED):
        self.a = a
        self.my_config_key1 = my_config_key1

    def my_method1(self):
        return self.a, self.my_config_key1

    @confr.configured
    def my_method2(self, my_config_key2=confr.CONFIGURED):
        return self.a, self.my_config_key1, my_config_key2

my_function("foo") # returns ("foo", "value 1")
my_function("foo", "override") # returns ("foo", "override")
my_function("foo", my_config_key1="override") # returns ("foo", "override")

obj = MyClass("bar")
obj.my_method1() # returns ("bar", "value 1")
obj.my_method2() # returns ("bar", "value 1", [1, 2, 3])
obj.my_method2("override") # returns ("bar", "value 1", "override")
obj.my_method2(my_config_key2="override") # returns ("bar", "value 1", "override")
```

We have three ways to initialise a configuration:

1. `confr.conf_from_files` - explicitly pass absolute paths (used e.g. in the inference server).
2. `confr.conf_from_dict` - explicitly pass config key-value pairs as dict (useful e.g. in unit/integration tests).
3. `confr.conf_from_dict` - by default, loads the base conf file `config/_base.yaml`, which is where the config file is located anyway. You can also pass a list of "conf patches", e.g. `test`, `model1`, `model2`; each conf patch's file is also loaded (e.g. from `config/test.yaml`), which can override some of the base conf's values.

Below is a typical example of how to initialise a configuration. The below code first loads `config/_base.yaml`, then `config/model1.yaml`, and then overwrites the `learning_rate` config key to be `0.01` in the current active configuration.

```python
import confr

confr.conf_from_dir(
    conf_patches=["model1"],
    overrides={"learning_rate": 0.01},
)
```

Once `confr.conf_from_*()` is called, confr ensures that for all functions and classes decorated with `@confr.configured`, which have keyword arguments with default values `confr.CONFIGURED`, will at runtime have those default values replaced with values from the global config object initialised with `confr.conf_from_*`.

We have three cases:

1. Classes decorated with `@confr.configured`. The `__init__` method can have keyword arguments with `confr.CONFIGURED` default values (e.g. `MyClass.__init__` above).
1. Class instance methods decorated with `confr.configured`. The class instance method can have keyword arguments with `confr.CONFIGURED` default values (e.g. `MyClass.my_method1` above).
1. Regular functions decorated with `confr.configured`. The function can have keyword arguments with `confr.CONFIGURED` default values (e.g. `my_function` above).

Please bear in mind the following:

* If you forget to decorate the class/function with `confr.configured` but set the keyword argument's default value as `confr.CONFIGURED`, the actual runtime value will be `"__CONFR_CONFIGURED__"`, which is not what you want. That's because `confr.CONFIGURED` is actually a constant that has the value `"__CONFR_CONFIGURED__"`, and unless you decorate your class/function with `confr.configured`, confr has no way to replace those values with ones in your config file(s).
* Even if you specify a keyword argument whose default value is `confr.CONFIGURED`, you can always override it by calling the function / class initializer with the keyword value assigned. Be careful when doing this, however. We often make arguments `confr.CONFIGURED` if we expect the value of the argument to always come from a config file (rather than being hardcoded from the calling function). Passing the value explicitly breaks this expectation, and can lead to confusing results. For example, say you implement `function1`, which calls `function2(img_h=96)`, which works fine for your current set of hyperparameters (because your `_base.yaml` also states `img_h=96`). But if someone else reuses the code and sets `img_h=192` in `_base.yaml`, then `function1` will probably cause the program to fail, because `function2` is called with `img_h=96` while everywhere else `img_h=192`. There are legitimate cases when you would need to modify the global configuration of some keywords, though - see the section `"confr.modified_conf"` below for more details.

## Python references and singletons

A value in `_base.yaml` can be a of the form `"@module1.module2.object_class_or_function"` (strings starting with a `@`). Such values (which we call **Python references**) will effectively be imported by confr and passed as regular python objects. For example, if `_base.yaml` contains `aug_fn: "@my_module.augmentors.aug_standard"`, we could do the following:

```python
confr.configured
def my_preprocessing(x, aug_fn=confr.CONFIGURED):
    # aug_fn is a Python callable
    x_augmented = aug_fn(x)
```

A value in `_base.yaml` can also be a of the form `"@module1.module2.class_or_function()"` (strings starting with a `@` **and ending with** `()`). These are **initializable Python references**, i.e. Python references which are called before they're swapped in as the default value. Generally it would be a class that gets initialized, though it can also be a function that returns a new object (such as a Keras model).

Initializable Python references have two types.

1. **singletons** - If `_base.yaml` defines a top-level config key (such as `my_model` in the `_base.yaml example` below), the value returned by calling the initializable Python reference is memoized (cached). Now this cached value is reused in all the places where we've defined `my_model=confr.CONFIGURED`. See `Python example 1` below.
2. **non-singletons** - For all other occurences of initializable Python references in config files, such as in lists or non-root config keys (e.g. in `all_models` and `models_by_name` in `_base.yaml example` below), the values get re-initialized every time they re-occur. See `Python example 2` below. **Make sure that you don't needlessly create many non-singleton Python references that take a long time to initialize or take a lot of memory, such as TensorFlow models.**

**_base.yaml example - do not do this!**

```yaml
my_model: "@my_module.models.model1()"
all_models:
    - "@my_module.models.model1()"
    - "@my_module.models.model1()"
models_by_name:
    model1: "@my_module.models.model1()"
    model2: "@my_module.models.model1()"
```

**Python example 1**

```python
@confr.configured
def get_my_model1(my_model=confr.CONFIGURED):
    return my_model

@confr.configured
def get_my_model2(my_model=confr.CONFIGURED):
    return my_model

my_model1 = get_my_model1() # my_model gets initialized here and memoized (cached in memory)
my_model2 = get_my_model1() # my_model is not re-initialized
assert my_model1 == my_model2 # my_model1 and my_model2 are the same object
```

**Python example 2**

```python
@confr.configured
def get_all_models(all_models=confr.CONFIGURED):
    return all_models

@confr.configured
def get_models_by_name(models_by_name=confr.CONFIGURED):
    return models_by_name

all_models = get_all_models() # model1 gets inititalized twice
assert all_models[0] != all_models[1] # while the objects are identical in behaviour, they're different objects

models_by_name = get_models_by_name() # model1 gets inititalized twice
assert all_models["model1"] != all_models["model2"] # while the objects are identical in behaviour, they're different objects
```

### Avoiding argument name conflicts in singletons

If you would like to configure input arguments specifically for singletons, you can do the following:

```yaml
my_model1: "@my_module.models.model1()"
my_model1/location: "/path/to/weights.h5"
my_model2: "@my_module.models.model2()"
my_model2/location: "/path/to/some/other/weights.h5"
```

Now `my_model1` singleton will be initialized with `location="/path/to/weights.h5"` and `my_model2` singleton will be initialized with `location="/path/to/some/other/weights.h5"`. This way they can both define an input argument called `location` and still receive a unique value at initialization time. We call `my_model1/location` as a **scoped argument**, i.e. the value of `location` is present in only the `my_model1` singleton scope.

Note that you can still use the regular, non-scoped arguments along with scoped ones. For example, both `my_model1` and `my_model2` might define `img_h=confr.CONFIGURED`, and this value will be the same when initializing both singletons.

## References to singletons

If a config value in `_base.yaml` starrs with a `$`, it is considered a reference to a singleton. For example, we might do  the following:

**_base.yaml**

```yaml
my_embedding_model: "@my_module.models.embedding_model()"
my_embedding_model/location: "/path/to/embedding_model/weights.h5"
classifier_model: "@my_module.models.classifier_model()"
classifier_model/location: "/path/to/embedding_model/weights.h5"
classifier_model/embedding_model: "$my_embedding_model"
```

Here we have said that, when we initialize the `classifier_model` singleton, the value of its keyword argument `embedding_model` will be the value of the `my_embedding_model` singleton.

This is useful if you have more than one embedding model singletons in one config file. If you have just one embedding model in your config file, you could instead write the above as:

```yaml
embedding_model: "@my_module.models.embedding_model()"
embedding_model/location: "/path/to/embedding_model/weights.h5"
classifier_model: "@my_module.models.classifier_model()"
classifier_model/location: "/path/to/embedding_model/weights.h5"
```

Notice that we've changed the name of our embedding model singleton from `my_embedding_model` to `embedding_model`, which coincides with the `my_module.models.classifier_model` argument `embedding_model`. Therefore we can omit the line `classifier_model/embedding_model: "$embedding_model"`, because this is the default behaviour anyway.


## confr.modified_conf and overrides

When working in a notebook, you may not want to modify the yaml file to change the configuration. You could instead initialize the configuration by selectively providing overrides to the keys you care about like this:

```python
confr.conf_from_dir(overrides={"override_key1": "v1", "override_key2": "v2"})
```

Here, all configurations will be taken from `_base.yaml`, and the keys `override_key1` and `override_key2` would respectively have values `"v1"` and `"v2"`.

You may also want to provide overrides to config values temporarily, for the duration of calling a function (and any downstream functions called by this function). For example, you might want to iterate over a list of `p_thresh` values and accuracy metrics for each `p_thresh`.

Our first attempt at solving this would look like this:
```python
for p_thresh in p_thresholds:
    precision = calculate_precision(x, y, p_thresh=p_thresh)
```

This would work if `calculate_precision` is the only place that uses the `p_thresh` that's passed in. But if `calculate_precision` calls another function that defines `sub_function(p_thresh=confr.CONFIGURED)`, then the value of `p_thresh` will be the same as in `_base.yaml` and not the one we passed to `calculate_precision`. What we need here is to temporarily set the value of `p_thresh` config key in the whole confr, like this:

```python
for p_thresh in p_thresholds:
    with confr.modified_conf(p_thresh=p_thresh):
        precision = calculate_precision(x, y)
```

## Accessing active configuration

Sometimes we need to explicitly fetch the value of a key in our config system. You can use `confr.get` and `confr.set` accessors to modify the current active conf:


```python
import confr

confr.conf_from_dict({"key1": "val1"})

confr.get("key1") # returns "val1"
confr.set("key1", "overwritten")
confr.get("key1") # returns "overwritten"

# can also write novel keys
confr.set("key2", "val2")
confr.get("key2") # returns "val2"

```

You can also save the current active configuration as a yaml file. We do this at the end of training, for example, since the conf file will need to be loaded when we re-initialize the model for inference.

```python
confr.write_conf_file("my_active__base.yaml)
```
