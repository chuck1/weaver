import bson
import logging

import elephant.local_
import weaver.util
import otter

logger = logging.getLogger(__name__)

class Conversion:

    @classmethod
    async def decode(cls, h, args):
        args = await h.decode(args)
        return cls(*args)

    def __init__(self, unit_0, unit_1, f):

        self.unit_0 = unit_0
        self.unit_1 = unit_1
        self.f = f
 
        if not isinstance(unit_0, weaver.quantity.unit.BaseUnit):
            raise Exception()

        if not isinstance(unit_1, weaver.quantity.unit.BaseUnit):
            raise Exception()

        if not isinstance(f, (int, float)):
            raise Exception(f'expected float not {type(f)} {f!r}')

    def __repr__(self):
        return f'{self.__class__.__name__}({self.unit_0}, {self.unit_1})'
   
    async def __encode__(self, h, user, mode):
        args = [self.unit_0, self.unit_1, self.f]

        return {"Conversion": await elephant.util.encode(h, user, mode, args)}



class Design(elephant.local_.doc.Doc):
    """
    fields

    'unit'           - default unit
    'conversions'   - a list of Conversion objects
                      conversions between units of different fundamental measurement
    'target'        - desired onhand quantity. used for automaticly adding to shopping list
    'onhand_threshold' - a quantity defined as follows:
                         when buying only to meet target, only buy if inventory minus demand is LESS than threshold
                         a threshold of zero would mean that you would only buy just to meet target if inventory was zero
    "inventory_quantity" - when creating an inventory instance, force the quantity to be equal to this quantity
                           this is used for tracking, so that individual pieces that should be handled individually
                           get their own record and therefore their own id_1
    """

    def __init__(self, e, d, _d, is_subobject=False):
        super().__init__(e, d, _d, is_subobject)
        self.d["_collection"] = "weaver designs"

    async def update_temp(self, user):
        await super().update_temp(user)
        
        self.d["_temp"]["designinstances"] = await self.temp_designinstances(user)

    async def temp_designinstances(self, user):

        c = self.e.h.weaver.e_designinstances.find(user, {"design": self.freeze()})

        return [_.subobject() async for _ in c]

    async def check(self):
        await super().check()

        if self.d.get("unit") is not None:
            if not isinstance(self.d.get("unit"), weaver.quantity.unit.BaseUnit):
                raise TypeError(f'expected BaseUnit not {self.d.get("unit")!r}')

        if 'cost' in self.d:
            assert isinstance(self.d["cost"], (int, float))

        for tag in self.d.get("tags", []):
            if not isinstance(tag, otter.subobjects.tag.Tag):
                raise otter.CheckError(f"expected subobjects.tag.Tag got {tag!r} {type(tag)}")

        #logger.warning(
        #    f'weaver design {self.d.get("description", "untitled")} {self.d["_temp"]["commits"][0].user} {self.d}')

        if "target" in self.d:
            logger.warning("has target")
            await self.conversion(self.d["target"].unit, self.d.get("unit"))

        for c in self.d.get("conversions", []):
            if not isinstance(c, Conversion):
                raise Exception()

        # target and unit compatibility

    def visit_manager_produce(self, user, manager, m, q):
        return manager.purchase(user, m, q)

    def print_info(self, indent='', m=None):
        print(indent + f'{self["description"]}')
        if m is not None:
            print(indent + f'quantity: {m["quantity"]}')
            print(indent + f'consumed: {m["consumed"]}')

    async def quantity_target(self):
        return self.d.get("target", weaver.quantity.Quantity(0, self.d.get("unit", None)))

    async def quantity_onhand_threshold(self):
        #return self.d.get("onhand_threshold", weaver.quantity.Quantity(0, self.d.get("unit", None)))
        return self.d.get("onhand_threshold")

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
        logger.info("conversion")
        logger.info(f"u0 = {u0!r}")
        logger.info(f"u1 = {u1!r}")

        if weaver.quantity.unit.unit_eq(u0, u1):
            return weaver.quantity.Quantity(1)

        for c in self.d.get("conversions", []):
            logger.info(f"try {c!r}")
            if not weaver.quantity.unit.unit_eq(c.unit_0, u0): continue
            if not weaver.quantity.unit.unit_eq(c.unit_1, u1): continue
            return weaver.quantity.Quantity(c.f, weaver.quantity.unit.ComposedUnit([u1], [u0]))

        for c in self.d.get("conversions", []):
            logger.info(f"try {c!r}")
            if not weaver.quantity.unit.unit_eq(c.unit_0, u1): continue
            if not weaver.quantity.unit.unit_eq(c.unit_1, u0): continue
            return weaver.quantity.Quantity(1/c.f, weaver.quantity.unit.ComposedUnit([u1], [u0]))

        raise Exception(f'no conversion for {self.d.get("description")!r} from {u0!s} to {u1!s}')

    async def create_demand(self, user, quantity, d=dict()):
        """
        d - dict with additional data for the new designinstance
        """

        if not isinstance(quantity, weaver.quantity.Quantity):
            raise TypeError()

        d.update({
                'design':   self.freeze(),
                'behavior': weaver.designinstance.doc.behavior.BehaviorDemand(
                    quantity,
                    ),
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



