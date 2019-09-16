#!/usr/bin/python3
# encoding: utf-8

def iterate_print(iter_count, prefix, key, value):
    def print_key():
        if key:
            print("%s%s:" % (iter_count * prefix, key))

    if value:
        if isinstance(value, dict):
            print_key()
            for _key, _value in value.items():
                iterate_print(iter_count + 1, prefix, _key, _value)
        elif isinstance(value, list):
            print_key()
            for _value in value:
                iterate_print(iter_count + 1, prefix, None, _value)
        else:
            print("%s%s: %s" % (iter_count * prefix, key, value) if key else "%s%s" % (iter_count * prefix, value))
