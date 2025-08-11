import copy

class Q:
    def __init__(self, selector):
        self._selector = selector
        self._matchers = set()
        self._functions = list()
        self._over = None

    def __str__(self):
        s = self._selector

        if self._matchers:
            s += '{' + ','.join([str(m) for m in self._matchers]) + '}'

        if self._over:
            s += f'[{self._over}]'

        for f in self._functions:
            s = f.name(s, *f.args) 

        return s
    
    def __add__(self, rhs):
        fn = lambda s, rhs: f'({s} + {rhs})'
        self._functions.append(_Function(fn, rhs))
        return self

    def __truediv__(self, rhs):
        fn = lambda s, rhs: f'({s} / {rhs})'
        self._functions.append(_Function(fn, rhs))
        return self
    
    def __mul__(self, rhs):
        fn = lambda s, rhs: f'({s} * {rhs})'
        self._functions.append(_Function(fn, rhs))
        return self

    def __sub__(self, rhs):
        fn = lambda s, rhs: f'({s} - {rhs})'
        self._functions.append(_Function(fn, rhs))
        return self
    
    def __gt__(self, rhs):
        fn = lambda s, rhs: f'({s} > {rhs})'
        self._functions.append(_Function(fn, rhs))
        return self
    
    def lor(self, rhs, on=None, ignoring=None):
        fn = on_or_ignoring('or', on, ignoring)
        self._functions.append(_Function(fn, rhs))
        return self
    
    def land(self, rhs, on=None, ignoring=None):
        fn = on_or_ignoring('and', on, ignoring)
        self._functions.append(_Function(fn, rhs))
        return self
    
    def unless(self, rhs, on=None, ignoring=None):
        fn = on_or_ignoring('unless', on, ignoring)
        self._functions.append(_Function(fn, rhs))
        return self

    def matches(self, **kwargs):
        for k, v in kwargs.items():
            m = _Matcher(k, "=", v)
            self._matchers.add(m)
        return self
    
    def does_not_match(self, **kwargs):
        for k, v in kwargs.items():
            m = _Matcher(k, "!=", v)
            self._matchers.add(m)
        return self
    
    def like(self, **kwargs):
        for k, v in kwargs.items():
            m = _Matcher(k, "=~", v)
            self._matchers.add(m)
        return self
    
    def not_like(self, **kwargs):
        for k, v in kwargs.items():
            m = _Matcher(k, "!~", v)
            self._matchers.add(m)
        return self
    
    def over(self, over):
        self._over = f'{over}'
        return self
    
    def copy(self):
        return copy.deepcopy(self)
    
    @classmethod
    def vector(cls, v):
        return cls(f'vector({v})')


def on_or_ignoring(binop, on, ignoring):
    if on != None:
        fn = lambda s, rhs: f'{s} {binop} on({",".join(on)}) {rhs}'

    elif ignoring != None:
        fn = lambda s, rhs: f'{s} {binop} ignoring({",".join(ignoring)}) {rhs}'

    else:
        fn = lambda s, rhs: f'{s} {binop} {rhs}'

    return fn


class _Function:
    def __init__(self, name, *args):
        self.name = name
        self.args = args

def rate(v):
    fn = lambda s: f'rate({s})'
    v._functions.append(_Function(fn))
    return v

def increase(v):
    fn = lambda s: f'increase({s})'
    v._functions.append(_Function(fn))
    return v

def _sum_by(s, args):
    if args:
        return f'sum({s}) by ({", ".join(args)})'
    else:
        return f'sum({s})'

def sum_by(v, *args):
    v._functions.append(_Function(_sum_by, args))
    return v

def absent(v):
    fn = lambda s: f'absent({s})'
    v._functions.append(_Function(fn))
    return v

def avg_over_time(v):
    fn = lambda s: f'avg_over_time({s})'
    v._functions.append(_Function(fn))
    return v

def max_over_time(v):
    fn = lambda s: f'max_over_time({s})'
    v._functions.append(_Function(fn))
    return v

def absent_over_time(v):
    fn = lambda s: f'absent_over_time({s})'
    v._functions.append(_Function(fn))
    return v


def sum_over_time(v):
    fn = lambda s: f'sum_over_time({s})'
    v._functions.append(_Function(fn))
    return v

class _Matcher:
    def __init__(self, name, op, value):
        self.name = name
        self.value = value
        self.op = op

    def __str__(self) -> str:
        return f'{self.name}{self.op}`{self.value}`'