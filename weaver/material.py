
import elephant.util

import weaver.quantity

async def decode(h, args):
    return Material(args["design"], args["quantity"])

class Material:
    def __init__(self, design, quantity):
        self._design = design
        self.design = design
        self._quantity = quantity
  
        if not isinstance(quantity, (int, float, weaver.quantity.Quantity)):
            raise Exception(f'invalid type for \'quantity\' argument: {type(quantity)}')

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

