import yaml


def validate_yaml(raw):
    try:
        topology = yaml.load(raw)
        return {
            'is_valid': True,
            'topology': topology
        }
    except yaml.YAMLError as e:
        return {
            'is_valid': False,
            'error_message': str(e)
        }


validators = {'YAML': validate_yaml}


def validate(language, raw):
    return validators[language](raw)
