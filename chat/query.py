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

from .predicate import Predicate


class Query:
    def __init__(self, record_type,
                 predicate=None, count=False,
                 limit=50, offset=None, include=[]):
        self.record_type = record_type
        if predicate is None:
            predicate = Predicate()
        self.predicate = predicate
        self.count = count
        self.sort = []
        self.limit = limit
        self.offset = offset
        self.include = include

    def add_order(self, key, order):
        self.sort.append([{'$type': 'keypath', '$val': key}, order])
        return self
