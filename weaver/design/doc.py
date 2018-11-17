import bson
import logging

import elephant.local_
import weaver.util

logger = logging.getLogger(__name__)

class Design(elephant.local_.doc.Doc):
    """
    fields

    'unit'           - default unit
    'conversions'   - conversions between units of different fundamental measurement
    'onhand'        - desired onhand quantity. used for automaticly adding to shopping list
    'onhand_thresh' - threshold for purchase quantity when buying to meet onhand quantity
    """

    def __init__(self, e, d, _d, is_subobject=False):
        super().__init__(e, d, _d, is_subobject)
        self.d["_collection"] = "weaver designs"

    async def update_temp(self, user):
        await super().update_temp(user)
        
        #self.d["temp"]["unit"] =

    async def check(self):
        await super().check()

        if self.d.get("unit") is not None:
            if not isinstance(self.d.get("unit"), weaver.quantity.unit.BaseUnit):
                raise TypeError(f'expected BaseUnit not {self.d.get("unit")!r}')

        if 'cost' in self.d:
            assert isinstance(self.d["cost"], (int, float))

    def visit_manager_produce(self, user, manager, m, q):
        return manager.purchase(user, m, q)

    def print_info(self, indent='', m=None):
        print(indent + f'{self["description"]}')
        if m is not None:
            print(indent + f'quantity: {m["quantity"]}')
            print(indent + f'consumed: {m["consumed"]}')

    async def quantity_onhand(self):
        return self.d.get("onhand", weaver.quantity.Quantity(0, self.d.get("unit", None)))

    async def quantity_onhand_threshold(self):
        return self.d.get("onhand_threshold", weaver.quantity.Quantity(0, self.d.get("unit", None)))

    async def list_recipes_negative(self, user):
        query = {
                "materials.Material.0.DocRef.0": self.d["_id"]}
        async for r in self.e.h.weaver.e_recipes.find(user, query):
            q = r.quantity(self)
            if q.num < 0: yield r

    async def list_upstream(self, user, filt):
 
        async for r in self.e.h.weaver.e_recipes.find(user, {"materials.design.id": self.d["_id"]}):
            q = r.quantity(self)
            if q.num > 0: continue
            yield r

    async def conversion(self, u0, u1):
        """
        conversion factor from u0 to u1
        x (u1) = y (u10 * c (u1 / u0)
        """
        print("conversion")
        print(f"{u0!r}")
        print(f"{u1!r}")

        if weaver.quantity.unit.unit_eq(u0, u1):
            return weaver.quantity.Quantity(1)

        r0 = u0.reduce()
        r1 = u1.reduce()
        print(f"{u0!r}")
        print(f"{u1!r}")
        c0 = [r0, r1]
        c1 = [r1, r0]

        if r0 == r1:
            return weaver.quantity.Quantity(1)

        print("looking for")
        print(f"    {c0}")
        for c, y in self.d.get("conversions", []):
            r = [c[0].reduce(), c[1].reduce()]
            print(f"try {r!r}")
            if r == c0:
                return weaver.quantity.Quantity(y, weaver.quantity.unit.ComposedUnit([u1], [u0]))

        print("looking for")
        print(f"    {c1}")
        for c, y in self.d.get("conversions", []):
            r = [c[0].reduce(), c[1].reduce()]
            print(f"try {r!r} {r == c1}")
            if r == c1:
                return weaver.quantity.Quantity(1/y, weaver.quantity.unit.ComposedUnit([u1], [u0]))

        raise Exception("no conversion")

    async def create_demand(self, user, quantity, d=dict()):
        """
        d - dict with additional data for the new designinstance
        """

        if not isinstance(quantity, weaver.quantity.Quantity):
            raise TypeError()

        d.update({
                'mode':     weaver.designinstance.doc.DesignInstanceMode.DEMAND.value,
                'design':   self.freeze(),
                'quantity': quantity,
                })

        di = await self.e.manager.e_designinstances.put(user, None, d)

        return di
 
    async def cost(self, user, q):
        logger.info("cost")

        # yield the cost of all possible options for producing this design
        
        if not weaver.quantity.unit.unit_eq(self.d.get("unit"), q.unit):

            try:
                c = await self.conversion(q.unit, self.d.get("unit"))
            except:
                raise Exception(f'failed to convert {q.unit} to {self.d.get("unit")} for design {self.d.get("description")}')
                raise

            q = q * c

            if not weaver.quantity.unit_eq(self.d.get("unit"), q.unit):
                raise Exception(f'units must be equal {self.d.get("unit")} {q.unit}')
            #logger.error(f'units must be equal {self.d.get("unit")} {q.unit}')
            #return

        if not weaver.quantity.unit.unit_eq(self.d.get("unit"), q.unit): raise Exception()

        async for r in self.list_recipes_negative(user):
            logger.info(f'has recipe')
            q1 = r.quantity(self)
            q2 = -q / q1
            logger.info(f'get cost for {q2} of recipe')
            async for _ in r.cost(user, q2): 
                yield _

        if 'cost' in self.d:
            logger.info(f'has cost field {self.d["cost"]}')
            assert isinstance(self.d["cost"], (int, float))
            yield self.d["cost"] * q.num

    async def materials_leaf(self, user, q):
        logger.info("materials leaf")

        # yield the cost of all possible options for producing this design
        
        if not weaver.quantity.unit.unit_eq(self.d.get("unit"), q.unit):
            try:
                c = await self.conversion(q.unit, self.d.get("unit"))
            except:
                raise Exception(f'failed to convert {q.unit} to {self.d.get("unit")} for design {self.d.get("description")}')

            q = q * c

            if not weaver.quantity.unit_eq(self.d.get("unit"), q.unit):
                raise Exception(f'units must be equal {self.d.get("unit")} {q.unit}')

        if not weaver.quantity.unit.unit_eq(self.d.get("unit"), q.unit): raise Exception()

        async for r in self.list_recipes_negative(user):
            logger.info(f'has recipe')
            q1 = r.quantity(self)
            q2 = -q / q1
            logger.info(f'get cost for {q2} of recipe')
            async for _ in r.materials_leaf(user, q2): 
                yield _

        if 'cost' in self.d:
            logger.info(f'has cost field {self.d["cost"]}')
            assert isinstance(self.d["cost"], (int, float))
            yield weaver.material.Material(self.freeze(), q)



