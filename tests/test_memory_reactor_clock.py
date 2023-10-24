#  Copyright 2023 Hathor Labs
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

from twisted.internet.testing import MemoryReactorClock


class TestMemoryReactorClock(MemoryReactorClock):
    def run(self):
        """
        We have to override MemoryReactor.run() because the original Twisted implementation weirdly calls stop() inside
        run(), and we need the reactor running during our tests.
        """
        self.running = True