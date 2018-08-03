import bson
import elephant.local_
import weaver.util

class Design(elephant.local_.File):
    def __init__(self, manager, e, d):
        self.manager = manager
        super(Design, self).__init__(e, d)

    def visit_manager_produce(self, user, manager, m, q):
        return manager.purchase(user, m, q)

    def print_info(self, indent='', m=None):
        print(indent + f'{self["description"]}')
        if m is not None:
            print(indent + f'quantity: {m["quantity"]}')
            print(indent + f'consumed: {m["consumed"]}')

    def freeze(self):
        if isinstance(self.d['_elephant']['ref'], bson.objectid.ObjectId):
            return {
                'id': self.d['_id'],
                'ref': self.d['_elephant']['ref'],
                }
        else:
            return {
                'id': self.d['_id'],
                'ref': self.d['_elephant']['refs'][self.d['_elephant']['ref']],
                }

    def list_upstream(self, user, filt):

        for m in self.d.get("materials", []):
            if m is None: continue

            u_id = m["part"]["id"]
                
            u = self.manager.e_designs.get_content(m["part"]["ref"], {"_id": u_id})

            yield

    async def produce(self, user, quantity):
        d0 = {
                'design': self.freeze(),
                'quantity': quantity,
                }

        d1 = await self.manager.e_designinstances.put(
                "master",
                None,
                d0,
                user)

        return d1

    async def to_array(self):
        d = dict(self.d)
        d["_collection"] = "weaver designs"
        return d


class Assembly(Design):
    def __init__(self, manager, e, d):
        super(Assembly, self).__init__(manager, e, d)

    def print_info(self, indent='', m0=None):
        print(indent + f'{self["description"]}')
        if m0 is not None:
            print(indent + f'quantity: {m0["quantity"]}')
            print(indent + f'consumed: {m0["consumed"]}')

        for m in self.d['materials']:
            part = self.manager.e_designs.get_content(m['part']['ref'], {'_id': m['part']['_id']})
            part.print_info(indent + '  ', m)

    def produce(self, user, manager, q):

        purchased = []

        for m in self.d['materials']:

            part = manager.e_designs.get_content(m['part']['ref'], user, {'_id': m['part']['_id']})
        
            # check inventory

            i = manager.get_inventory(m['part'])

            d = m['quantity'] * q - i

            if d > 0:
                # insufficient inventory
                
                purchased1 = part.visit_manager_produce(user, manager, m['part'], d)

                purchased += purchased1

                #manager.purchase(m, d)

                pass
            else:
                # sufficient inventory
                pass

            manager.consume(m)

        manager.receive(user, self.freeze(), q)

        return purchased

class Engine(elephant.local_.Engine):
    def __init__(self, manager, coll, e_queries):
        super().__init__(coll, e_queries)
        self.manager = manager
        self.h = manager.h

    def _factory(self, d):
        if 'materials' in d:
            raise Exception()
            #return weaver.design.Assembly(self.manager, self, d)
        return weaver.design.Design(self.manager, self, d)


