import enum
import logging
import pprint
import pymongo
import elephant.local_
import weaver.recipeinstance
import weaver.designinstance.doc

logger = logging.getLogger(__name__)

class Engine(weaver.engine.EngineGlobal):
    def __init__(self, manager, coll, e_queries):
        super().__init__(manager, coll, "master", e_queries)
        self._doc_class = weaver.designinstance.doc.DesignInstance

    async def get_test_object(self, user, b0={}):

        design = await self.manager.e_designs.get_test_object(user)

        b1 = {
            "design":   design.freeze(),
            "behavior": weaver.designinstance.doc.behavior.BehaviorInventory(
                weaver.quantity.Quantity(1, design.d.get("unit")),
                None,
                ),
            }

        b1.update(b0)

        b = await self._doc_class.get_test_document(b1)

        o = await self.put(user, None, b)
        return o

    async def counter(self, name):
        counter = self.manager.h.db.counters.find_one_and_update(
            {'name': name},
            {'$inc': {'count': 1}},
            upsert=True,
            return_document=pymongo.ReturnDocument.BEFORE,
            )
        if counter is None: return 0
        return counter["count"]

    async def next_id(self):
        return await self.counter('designinstane_id')

    async def pre_put_new(self, d_0):
        d_0['id_1'] = await self.next_id()
        return d_0

    def pipe0(self, user):
        yield from super().pipe0(user)



