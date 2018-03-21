# Copyright 2015 Oursky Ltd.
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
import json
from urllib.parse import urlparse, urlunparse

from skygear.options import options
from websocket import create_connection

encoder = json.dumps
_hub = None


def get_hub():
    global _hub
    if not _hub:
        _hub = Hub()
    return _hub


def publish(channel, data):
    get_hub().publish(channel, data)


def _get_default_pubsub_url():
    if options.pubsub_url:
        return options.pubsub_url

    parsed_endpoint = urlparse(options.skygear_endpoint)

    scheme = 'wss' if parsed_endpoint.scheme == 'https' else 'ws'
    netloc = parsed_endpoint.netloc
    path = '/pubsub'
    urlparts = (scheme, netloc, path, '', '', '')
    return urlunparse(urlparts)


class Hub:

    def __init__(self, end_point=None, api_key=None):
        self.transport = 'websocket'
        self.end_point = end_point or _get_default_pubsub_url()
        self.api_key = api_key or options.apikey

    def publish(self, channels, data):
        wsopts = {}
        if self.api_key:
            wsopts['header'] = [
                    'X-Skygear-API-Key: {0}'.format(self.api_key)
                    ]
        conn = create_connection(self.end_point, **wsopts)
        if isinstance(channels, str):
            channels = [channels]
        for channel in channels:
            _data = encoder({
                'action': 'pub',
                'channel': channel,
                'data': data,
            })
            conn.send(_data)
        conn.close()
