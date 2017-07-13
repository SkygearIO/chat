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


class Database(object):
    def __init__(self, container, database_id):
        self.container = container
        self.database_id = database_id

    def save(self, records):
        if not isinstance(records, list):
            records = [records]

        return self.container.send_action('record:save', {
            'database_id': self.database_id,
            'records': records
        })

    def delete(self, records):
        if not isinstance(records, list):
            records = [records]

        return self.container.send_action('record:delete', {
            'database_id': self.database_id,
            'records': records
        })

    def query(self, query):
        payload = {'database_id': self.database_id,
                   'record_type': query.record_type,
                   'predicate': query.predicate.to_dict(),
                   'count': query.count,
                   'sort': query.sort,
                   'include': query.include}

        if query.offset is not None:
            payload['offset'] = query.offset
        if query.limit is not None:
            payload['limit'] = query.limit

        return self.container.send_action('record:query', payload)
