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


class Schema(object):
    def __init__(self, record_type, fields):
        self.record_type = record_type
        self.fields = fields

    def to_dict(self):
        return {self.record_type:
                {'fields': [field.to_dict() for field in self.fields]}}


class SchemaHelper(object):
    def __init__(self, container):
        self.container = container

    def create(self, schemas, plugin_request=False):
        record_types = {}
        for schema in schemas:
            record_types.update(schema.to_dict())
        payload = {'record_types': record_types}
        return self.container.send_action('schema:create',
                                          payload,
                                          plugin_request=plugin_request)
