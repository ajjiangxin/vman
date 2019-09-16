#!/usr/bin/python
# encoding: utf-8


def handle(cls):
    cls.executors[cls.cmd](cls)

# decorate on class to register as handler any of its methods whose name starts with 'do_'
def handlers(cls):
    cls.handle = handle
    cls.executors = {}
    for mn in dir(cls):
        if 'do_' in mn:
            m = getattr(cls, mn)
            cls.executors.update({mn.replace('do_', ''): m})
    return cls