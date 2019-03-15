from typing import Dict, List, TypeVar, Any

K = TypeVar('K')


def combine_dict_lists_by_key(dict_lists: List[List[Dict[K, Any]]], key: K):
    map_by_key: Dict[K, Dict] = {}

    for dict_list in dict_lists:
        for d in dict_list:
            new_d: Dict[K, Any] = map_by_key.get(d.get(key)) if map_by_key.get(d.get(key)) else {}
            for k, v in d.items():
                new_d[k] = v
            map_by_key[d.get(key)] = new_d

    return map_by_key.values()
