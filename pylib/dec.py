#!/usr/bin/python
# encoding: utf-8

class Handler:

    @staticmethod
    def handle(cls):
        cls.h[cls.cmd](cls)

    # decorate on class to register as handler any of its methods whose name starts with 'do_'
    @staticmethod
    def registerDoHandlers(cls):
        cls.handle = Handler.handle
        cls.h = {}
        for n in dir(cls):
            m = getattr(cls, n)
            if n.startswith('do_'):
                cls.h.update({n.replace('do_', ''): m})
            if hasattr(m, "route"):
                cls.h.update({m.route: m})
        return cls

    @staticmethod
    def route(key=""):
        def decorator(func):
            def wrapper(*args, **kwargs):
                print('exec route for key: %s' % key)
                return func(*args, **kwargs)
            wrapper.route = key
            return wrapper

        return decorator
