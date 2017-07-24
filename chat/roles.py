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


class RolesHelper(object):
    def __init__(self, container):
        self.container = container

    def assign(self, users, roles):
        return self.container.send_action('role:assign', {
            'roles': roles,
            'users': users
        })

    def revoke(self, users, roles):
        return self.container.send_action('role:revoke', {
            'roles': roles,
            'users': users
        })

    def set_roles(self, users, roles, flag):
        result = None
        if flag:
            result = self.assign(users, roles)
        else:
            result = self.revoke(users, roles)
        return result
