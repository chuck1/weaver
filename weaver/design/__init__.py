import bson
import logging

import elephant.local_
import weaver.util
import weaver.design.doc

logger = logging.getLogger(__name__)


class Engine(weaver.engine.EngineLocal):

    def __init__(self, manager, coll, e_queries):
        super().__init__(manager, coll, e_queries)
        self.manager = manager
        self.h = manager.h
        self._doc_class = weaver.design.doc.Design

    async def create_indices(self):
        self.coll.files.create_index([("description", "text")])


