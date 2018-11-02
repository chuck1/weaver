import itertools

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
        if y.reduce() == ([], []): return True
        return False
    if y is None:
        if x.reduce() == ([], []): return True
        return False
    return x.reduce() ==  y.reduce()

def simplify(u):
    if isinstance(u, ComposedUnit):
        N, D = u.reduce()
        if (not N) and (not D):
            return None
        if (len(N) == 1) and (not D):
            return N[0]
    return u

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

    def __str__(self):
        N = " ".join(str(n) for n in self.numer)
        if not self.denom: return N
        D = " ".join(str(d) for d in self.denom)
        return f'{N} / {D}'

    def reduce(self):
        N = list(self.numer)
        D = list(self.denom)
        
        while True:
            n = _find_match(N, D)
            if not n: break
            N.remove(n)
            D.remove(n)
        return (list(sorted(n for n in N)), list(sorted(d for d in D)))

    async def get_unit(self, h, user):
        
        for u in itertools.chain(self.numer, self.denom):
            if u is None: continue
            await u.get_unit(h, user)

    async def __encode__(self, h, user, mode):
        u = simplify(self)

        if u is self: raise Exception()
 
        return u

class Unit(BaseUnit):

    @classmethod
    async def decode(cls, h, args):
        args = await h.decode(args)
        return cls(*args)

    def __init__(self, ref):

        # fix
        #if isinstance(ref, bson.objectid.ObjectId):
        #    ref = elephant.ref.DocRef(ref)

        if not isinstance(ref, elephant.ref.DocRef):
            raise TypeError(f'expected DocRef but got {ref!r} {type(ref)}')

        self.ref = ref
    
    def reduce(self):
        return ([self], [])

    def __lt__(self, other):
        return self.ref < other.ref

    def __eq__(self, other):
        if not isinstance(other, Unit): return False
        return self.ref == other.ref

    def __repr__(self):
        return f"Unit({self.ref!r})"

    def __str__(self):
        if hasattr(self, "doc"):
            return self.doc.d["name"]
        return repr(self)

    async def get_unit(self, h, user):
        self.doc = await h.weaver.e_units.find_one_by_ref(user, self.ref)
        return self.doc 

    async def __encode__(self, h, user, mode):
        args = [self.ref]

        if mode == elephant.EncodeMode.CLIENT:
            doc = await self.get_unit(h, user)
            if doc is None:
                raise RuntimeError('unit document not found')
            args.append(doc)

        return {"Unit": await elephant.util.encode(h, user, mode, args)}




