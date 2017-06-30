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


import collections
import copy


class Predicate(object):
    AND = 'and'
    OR = 'or'
    NOT = 'not'

    def __init__(self, **kwargs):
        self.op = kwargs.pop('op', Predicate.AND)
        # Need to use ordered dict in order to pass unit test in python 3.5.
        # See https://docs.python.org/3.6/whatsnew/3.6.html#whatsnew36-pep468
        od = collections.OrderedDict(sorted(kwargs.items()))
        self.conditions = [(key, kwargs[key]) for key in od.keys()]

    def __and__(self, other):
        new_instance = Predicate()
        if self.op == Predicate.AND:
            new_instance.conditions = copy.copy(self.conditions)
            if other.op == self.op:
                new_instance.conditions += other.conditions
            else:
                new_instance.conditions.append(other)
        else:
            new_instance.conditions = [self, other]
        return new_instance

    def __or__(self, other):
        new_instance = Predicate(op=Predicate.OR)
        if self.op == Predicate.OR:
            new_instance.conditions = copy.copy(self.conditions)
            if other.op == self.op:
                new_instance.conditions += other.conditions
            else:
                new_instance.conditions.append(other)
        else:
            new_instance.conditions = [self, other]
        return new_instance

    def __invert__(self):
        new_instance = Predicate(op=Predicate.NOT)
        new_instance.conditions = [self]
        return new_instance

    @classmethod
    def condition_to_dict(cls, t):
        field, op = t[0].split("__")
        return [op, {"$type": "keypath", "$val": field}, t[1]]

    def to_dict(self, root=None):
        if root is None:
            root = self
        if root is None:
            return []
        if isinstance(root, Predicate):
            num_conditions = len(root.conditions)
            if num_conditions == 0:
                return []
            elif num_conditions == 1:
                result = self.to_dict(root.conditions[0])
                if root.op != Predicate.NOT:
                    return result
                return [root.op, result]
            else:
                return [root.op] + [self.to_dict(d) for d in root.conditions]
        elif type(root) == tuple:
            return Predicate.condition_to_dict(root)
        else:
            return []
