# Copyright 2017 Oursky Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from skygear.models import Record
from skygear.transmitter.encoding import deserialize_record, serialize_record

from .asset import sign_asset_url
from .exc import SkygearChatException


class Database(object):
    def __init__(self, container, database_id):
        self.container = container
        self.database_id = database_id

    def save(self, arg, atomic=False):
        if not isinstance(arg, list):
            arg = [arg]
        records = [serialize_record(item)
                   if isinstance(item, Record) else item
                   for item in arg]
        return self.container.send_action('record:save', {
            'database_id': self.database_id,
            'records': records,
            'atomic': atomic
        })

    @staticmethod
    def _encode_id(record_id):
        return record_id.type + "/" + record_id.key

    def delete(self, arg):
        if not isinstance(arg, list):
            arg = [arg]
        ids = [Database._encode_id(item.id)
               if isinstance(item, Record)
               else item
               for item in arg]
        return self.container.send_action('record:delete', {
            'database_id': self.database_id,
            'ids': ids
        })

    def query(self, query):
        include = {v: {"$type": "keypath", "$val": v}
                   for v in list(set(query.include))}

        payload = {'database_id': self.database_id,
                   'record_type': query.record_type,
                   'predicate': query.predicate.to_dict(),
                   'count': query.count,
                   'sort': query.sort,
                   'include': include}

        if query.offset is not None:
            payload['offset'] = query.offset
        if query.limit is not None:
            payload['limit'] = query.limit
        result = self.container.send_action('record:query', payload)
        if 'error' in result:
            raise SkygearChatException(result['error']['message'])
        result = result['result']
        output = []
        for r in result:
            record = deserialize_record(r)
            if '_transient' in r:
                t = r['_transient']
                record['_transient'] = {k: deserialize_record(t[k])
                                        for k in t.keys()}
            if 'attachment' in r:
                record['attachment'] = r['attachment'].copy()
                record['attachment']['$url'] =\
                    sign_asset_url(r['attachment']['$name'])
            output.append(record)
        return output
