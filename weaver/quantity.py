import bson

import elephant.util

def _numer(N, D):
    for u in N:
        if isinstance(u, ComposedUnit):
            yield from _numer(u.numer, u.denom)
        else:
            yield u
    for u in D:
        if isinstance(u, ComposedUnit):
            yield from _denom(u.numer, u.denom)

def _denom(N, D):
    for u in D:
        if isinstance(u, ComposedUnit):
            yield from _numer(u.numer, u.denom)
        else:
            yield u
    for u in N:
        if isinstance(u, ComposedUnit):
            yield from _denom(u.numer, u.denom)

def _find_match(N, D):
    for n in N:
        for d in D:
            if n == d:
                return n

def _reduce(N, D):
    N, D = list(N), list(D)
    while True:
        n = _find_match(N, D)
        if not n: break
        N.remove(n)
        D.remove(n)
    return N, D

def unit_eq(x, y):
    if (x is None) and (y is None): return True
    if x is None:
        if y.reduce() == [[], []]: return True
        return False
    if y is None:
        if x.reduce() == [[], []]: return True
        return False
    return x.reduce() ==  y.reduce()

#def simplify(u):
#    if isinstance(u, ComposedUnit):
        

class BaseUnit: pass

class ComposedUnit(BaseUnit):
    def __init__(self, numer=[], denom=[]):
        numer = [u for u in numer if u is not None]
        denom = [u for u in denom if u is not None]
        for u in numer: assert isinstance(u, BaseUnit)
        for u in denom: assert isinstance(u, BaseUnit)
        assert isinstance(numer, list)
        assert isinstance(denom, list)
        self.numer, self.denom = _reduce(list(_numer(numer, denom)), list(_denom(numer, denom)))

    def __repr__(self):
        return f"ComposedUnit({self.numer}, {self.denom})"

    def reduce(self):
        N = list(self.numer)
        D = list(self.denom)
        print("reduce")
        print("N", N)
        print("D", D)
        while True:
            n = _find_match(N, D)
            if not n: break
            N.remove(n)
            D.remove(n)
        return [list(sorted(n for n in N)), list(sorted(d for d in D))]

class Unit(BaseUnit):
    def __init__(self, _id):
        assert isinstance(_id, bson.objectid.ObjectId)
        self._id = _id
    
    def reduce(self):
        return [[self], []]

    def __lt__(self, other):
        return self._id < other._id

    def __eq__(self, other):
        if not isinstance(other, Unit): return False
        return self._id == other._id

    def __repr__(self):
        return f"Unit({str(self._id)[-8:]})"

    async def __encode__(self):
        return {"Unit": [self._id]}

class Quantity:
    def __init__(self, num_or_dict):
        if isinstance(num_or_dict, dict):
            num_or_dict = dict(num_or_dict)
            assert "num" in num_or_dict
            #assert "unit" in num_or_dict
            assert isinstance(num_or_dict["num"], (int, float))

            self.num = num_or_dict["num"]

            if (num_or_dict.get("unit") is None) or isinstance(num_or_dict["unit"], BaseUnit):
                self.unit = num_or_dict.get("unit")
            else:
                self.unit = Unit(num_or_dict["unit"])

        elif isinstance(num_or_dict, (int, float)):
            
            self.num = num_or_dict
            self.unit = None

        else:
            raise Exception(f"expected dict, int, or float, not {type(num_or_dict)}")

    def __repr__(self):
        return f"Quantity({self.num!r}, {self.unit!r})"

    def __add__(self, other):
        assert isinstance(other, Quantity)
        r0 = self.unit.reduce()
        r1 = other.unit.reduce()
        if not (r0 == r1):
            raise Exception(f"Incompatible units {r0!r} and {r1!r}")
            #raise Exception(f"Incompatible units {self.unit!r} and {other.unit!r}")
        return Quantity({"num": self.num + other.num, "unit": self.unit})

    def __neg__(self):
        return Quantity({"num": -self.num, "unit": self.unit})

    def __truediv__(self, other):
        assert isinstance(other, (int, float, Quantity))
        if isinstance(other, (int, float)):
            return Quantity({"num": self.num / other, "unit": self.unit})
        return Quantity({"num": self.num / other.num, "unit": ComposedUnit([self.unit], [other.unit])})

    def __mul__(self, other):
        assert isinstance(other, Quantity)
        return Quantity({"num": self.num * other.num, "unit": ComposedUnit([self.unit, other.unit])})

    async def __encode__(self):
        args = await elephant.util.encode([{'num': self.num, 'unit': self.unit}])
        return {'Quantity': args}



