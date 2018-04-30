import bson
import datetime

import elephant.file

class _AArray(elephant.file.File):
    def __init__(self, manager, engine, _id, d):
        super(_AArray, self).__init__(d)
        self.manager = manager
        self.engine = engine
        self._id = _id

    def __getitem__(self, k):
        return self.d[k]

    def __setitem__(self, k, v):
        self.d[k] = v

        self.engine.put(self._id, self.d)

    def get(self, k, default):
        if k in self.d:
            return self.d[k]
        else:
            return default

    def to_array(self):
        
        def _f1(v):
            if isinstance(v, datetime.datetime):
                v = str(v)

            if isinstance(v, bson.objectid.ObjectId):
                v = str(v)

            if isinstance(v, list):
                v = [_f1(i) for i in v]
            
            if isinstance(v, dict):
                v = dict(_f(k1, v1) for k1, v1 in v.items())
                
            return v

        def _f(k, v):
            return k, _f1(v)

        d0 = dict(_f(k, v) for k, v in self.d.items())

        if '_elephant' in d0:
            del d0['_elephant']

        return d0



