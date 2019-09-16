#!/usr/bin/python3
# encoding: utf-8


def str_to_dict(string, key_by_value_of=''):
    d_key = ''
    d = {}
    for sub in string.split(','):
        item = {}
        sub = sub.strip()
        pos_sep = 0
        for i in range(len(sub)):
            if sub[i] == ':' or sub[i] == '=':
                pos_sep = i
                break
        k = sub[:pos_sep].strip()
        v = sub[(pos_sep + 1):].strip()
        if key_by_value_of and k == key_by_value_of:
            d_key = v
        else:
            d[k] = v
    return d_key, d
