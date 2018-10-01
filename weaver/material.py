
import elephant.util

import weaver.quantity

async def decode(h, args):
    return Material(args["design"], args["quantity"])

class Material:
    def __init__(self, design, quantity):

        if not isinstance(design, dict):
            raise Exception(f'first argument must be dict')

        if not isinstance(quantity, (int, float, weaver.quantity.Quantity)):
            raise Exception(f'invalid type for \'quantity\' argument: {type(quantity)}')

        self._design = design
        self.design = design
        self._quantity = quantity
  

        if isinstance(quantity, weaver.quantity.Quantity):
            self.quantity = quantity
        elif isinstance(quantity, (int, float)):
            self.quantity = weaver.quantity.Quantity(quantity)

    async def __encode__(self):
        args = {
                "design": self._design,
                "quantity": self._quantity,
                }
        return {'Material': await elephant.util.encode(args)}

