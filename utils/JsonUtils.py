import json


def is_json(json_str):
    try:
        json_object = json.loads(json_str)
    except ValueError as e:
        return False
    return True


def format_model(model_str):
    strs = model_str.split('\n')
    print('strs = ', strs)
    res_str = ''
    for s in strs:
        s = s.replace("\"{", "{")
        s = s.replace("}\"", "}")
        s = s.replace("\\", "")
        if is_json(s):
            res_str += json.dumps(json.loads(s), indent=2) + '\n'
        else:
            res_str += s + '\n'
    return res_str


class JsonUtils:
    pass
