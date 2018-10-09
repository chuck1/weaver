
import elephant.util

import weaver.quantity
import weaver.design

async def decode(h, args):
    return Material(*args)

class Material:
    def __init__(self, design_ref, quantity):

        # fix
        if isinstance(quantity, (int, float)):
            quantity = weaver.quantity.Quantity(quantity)

        # validate
        assert isinstance(design_ref, dict)
        
        if not isinstance(quantity, weaver.quantity.Quantity):
            raise Exception(f'invalid type for \'quantity\' argument: {type(quantity)}')

        #

        self.design_ref = design_ref
        self.quantity = quantity
  
    async def get_design(self, h, user):
        o = await h.weaver.e_designs.find_one_by_id(user, self.design_ref["ref"], self.design_ref["id"])
        assert o is not None
        return o

    async def __encode__(self, h, user, mode):
        if mode == elephant.EncodeMode.DATABASE:
            args = [self.design_ref, self.quantity]

        elif mode == elephant.EncodeMode.CLIENT:
            design = await self.get_design(h, user)
            args = [self.design_ref, self.quantity, design]

        return {'Material': await elephant.util.encode(h, user, mode, args)}



