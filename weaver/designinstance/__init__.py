
import elephant.local_

class DesignInstance(elephant.local_.File):
    def __init__(self, manager, e, d):
        super().__init__(e, d)

    async def update_temp(self, user):
        pass        
        
    async def to_array(self):
        d = dict(self.d)
        d["_collection"] = "weaver designinstances"
        return d

class Engine(elephant.local_.Engine):
    def __init__(self, manager, coll, e_queries):
        super().__init__(coll, e_queries)
        self.manager = manager
        self.h = manager.h

    def pipe0(self):
        # design
        yield {'$addFields': {'design_id': '$design.id'}}
        yield {'$lookup': {
                'from': 'weaver.designs.files',
                'let': {'design_id': '$design_id'},
                'pipeline': [
                    {'$match': {'$expr': {'$eq': ['$_id', '$$design_id']}}},
                    ],
                'as': '_design',
                }}
        #yield {'$project': {
        #        '_design': {'$arrayElemAt': ['$_design', 0]},
        #        }}

    def _factory(self, d):
        return DesignInstance(self.manager, self, d)


