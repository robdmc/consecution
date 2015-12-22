"""
Interface is something like
a | b | deal([c, d, e])  #shortcut ( << )
a | b | route([c, d, e], route_func)
a | b | broadcast([c, d, e])  # shortcut ( & )
merge([a, b, c]) | d  # shortcut [a, b, c] >> d
"""

class OperatorMixin:
    def __or__(self, other):
        return X('({} | {})'.format(self, other))

    def __ror__(self, other):
        return X('({} | {})'.format(other, self))



class X(object):
    def __init__(self, name):
        self.name = name

    def __or__(self, other):
        print('called or')
        return X('({} | {})'.format(self, other))

    def __ror__(self, other):
        print('called ror')
        return X('({} | {})'.format(other, self))

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.__str__()

a = X('a')
b = X('b')
c = X('c')
d = X('d')
e = X('e')
f = X('f')
g = X('g')

if True:
    print(a|b)
    print(b|a)

if False:
    print( 'a|1', a|1)
    print( '1|a', 1|a)
    print()
    print( a | b | c | d)

