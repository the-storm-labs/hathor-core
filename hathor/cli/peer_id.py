# Copyright 2021 Hathor Labs
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

""" Generates a random Peer and print it to stdout.
It may be used to testing purposes.
"""

import json


def main() -> None:
    from hathor.p2p.peer import Peer

    peer = Peer()
    data = peer.to_json(include_private_key=True)
    txt = json.dumps(data, indent=4)
    print(txt)
