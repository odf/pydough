from __future__ import generators

if not hasattr(__builtins__, 'True'):
    True = 1
    False = not True

if not hasattr(__builtins__, 'enumerate'):
    def enumerate(seq):
        i = 0
        for x in seq:
            yield i, x
            i = i + 1

if not hasattr(__builtins__, 'sum'):
    def sum(seq):
        s = 0
        for x in seq:
            s = s + x
        return s
