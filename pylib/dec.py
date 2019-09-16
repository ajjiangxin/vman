#!/usr/bin/python
# encoding: utf-8


def handle(cls):
    cls.h[cls.cmd](cls)

# decorate on class to register as handler any of its methods whose name starts with 'do_'
def handlers(cls):
    cls.handle = handle
    cls.h = {}
    for n in dir(cls):
        if n.startswith('do_'):
            m = getattr(cls, n)
            cls.h.update({n.replace('do_', ''): m})
    return cls
