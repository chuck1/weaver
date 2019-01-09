import bson

import elephant.util

import weaver.quantity.unit

class Quantity:

    @classmethod
    async def decode(cls, h, args):

        args = await h.decode(args)

        # fix
        #if isinstance(args, dict):
        #    args = [args["design"], args["quantity"]]

        return cls(*args)

    async def __encode__(self, h, user, mode):
        args = [self.num, self.unit]
        args = await elephant.util.encode(h, user, mode, args)
        return {'Quantity': args}


    def __init__(self, num, unit=None):
       
        # MIGRATE
        if isinstance(num, dict):
            a = dict(num)
            num = a.get("num")

            unit = a.get("unit")

        if isinstance(unit, bson.objectid.ObjectId):
            unit = weaver.quantity.unit.Unit(unit)

        # validate
 
        if not isinstance(num, (int, float)):
            raise Exception(f"expected int or float, not {type(num)} {num}")

        if not ((unit is None) or isinstance(unit, weaver.quantity.unit.BaseUnit)):
            raise Exception(f"expected None or BaseUnit, not {type(unit)} {unit}")

        self.num = num
        self.unit = unit

    def __repr__(self):
        return f"Quantity({self.num!r}, {self.unit!r})"

    def __str__(self):
        return f'{self.num} {self.unit!s}'

    def __add__(self, other):
        assert isinstance(other, Quantity)
        if not weaver.quantity.unit.unit_eq(self.unit, other.unit):
            raise Exception(f"Incompatible units {self.unit!r} and {other.unit!r}")
            #raise Exception(f"Incompatible units {self.unit!r} and {other.unit!r}")
        return Quantity(self.num + other.num, self.unit)

    def __sub__(self, other):
        assert isinstance(other, Quantity)
        if not weaver.quantity.unit.unit_eq(self.unit, other.unit):
            raise Exception(f"Incompatible units {r0!r} and {r1!r}")
            #raise Exception(f"Incompatible units {self.unit!r} and {other.unit!r}")
        return Quantity(self.num - other.num, self.unit)

    def __neg__(self):
        return Quantity(-self.num, self.unit)

    def __truediv__(self, other):
        assert isinstance(other, (int, float, Quantity))
        if isinstance(other, (int, float)):
            return Quantity(self.num / other, self.unit)
        return Quantity(self.num / other.num, weaver.quantity.unit.ComposedUnit([self.unit], [other.unit]))

    def __mul__(self, other):
        assert isinstance(other, Quantity)
        return Quantity(
                self.num * other.num, 
                weaver.quantity.unit.ComposedUnit([self.unit, other.unit]))

    def __eq__(self, other):
        assert isinstance(other, Quantity)
        if not weaver.quantity.unit.unit_eq(self.unit, other.unit):
            raise Exception(f"Incompatible units {self.unit!r} and {other.unit!r}")
        return self.num == other.num

    def __lt__(self, other):
        assert isinstance(other, Quantity)
        if not weaver.quantity.unit.unit_eq(self.unit, other.unit):
            raise Exception(f"Incompatible units {r0!r} and {r1!r}")
        return self.num < other.num

    def __le__(self, other):
        assert isinstance(other, Quantity)
        if not weaver.quantity.unit.unit_eq(self.unit, other.unit):
            raise Exception(f"Incompatible units {r0!r} and {r1!r}")
        return self.num <= other.num



