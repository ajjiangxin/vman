#!/usr/bin/env python3
# encoding: utf-8

from inspect import getmodule, getfullargspec


func_cache = {}


def keyword_arguments_to_str(**kwargs):
    l = []
    for k in kwargs:
        l.append('%s:%s' % (k, kwargs[k]))
    return '.'.join(l)

def get_func_cache_key(f, *args, **kwargs):
    return '.'.join([
            getmodule(f).__name__,
            f.__name__,
            '.'.join(getfullargspec(f).args),
            '.'.join(*args) if args else '',
            keyword_arguments_to_str(**kwargs) if kwargs else ''
        ])

def cached(f):
    def wrapper(*args, **kwargs):
        k = get_func_cache_key(f, *args, **kwargs)
        if k in func_cache:
            return func_cache[k]
        else:
            rv = f(*args, **kwargs)
            func_cache[k] = rv
            return rv
    return wrapper
