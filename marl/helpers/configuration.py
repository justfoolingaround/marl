import pathlib
import yaml

def merge_dicts(dict1, dict2):
    for k, v in dict1.items():
        if isinstance(v, dict):
            merge_dicts(v, dict2.setdefault(k, {}))
        else:
            if k not in dict2:
                dict2[k] = v
    return dict2

with open(pathlib.Path(__file__).parent / "default_configuration.yaml") as default_configuration_file:
    default_configuration = yaml.load(default_configuration_file, yaml.SafeLoader)

def get_configuration(*, path: pathlib.Path=pathlib.Path('./bot_configuration.yaml')):
    if not path.exists():
        return default_configuration

    with open(path) as config:
        return merge_dicts(default_configuration, yaml.load(config, yaml.SafeLoader))
