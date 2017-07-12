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

from skygear.transmitter.encoding import _RecordDecoder


class User(object):
    def __init__(self, name, id_, roles):
        self.name = name
        self._id = id_
        self.roles = roles

    @property
    def id(self):
        return self._id

    @staticmethod
    def deserialize(record):
        decoder = _RecordDecoder()
        name = record['name']
        id_ = decoder.decode_id(record['_id'])
        roles = [decoder.decode_ace(a) for a in record['_access']]
        return User(name, id_, roles)
