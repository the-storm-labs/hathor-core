from hathor.pubsub import HathorEvents, PubSubManager
from tests.unittest import TestCase


class PubSubTestCase(TestCase):
    def test_duplicate_subscribe(self):
        def noop():
            pass
        pubsub = PubSubManager(self.clock)
        pubsub.subscribe(HathorEvents.NETWORK_NEW_TX_ACCEPTED, noop)
        pubsub.subscribe(HathorEvents.NETWORK_NEW_TX_ACCEPTED, noop)
        self.assertEqual(1, len(pubsub._subscribers[HathorEvents.NETWORK_NEW_TX_ACCEPTED]))
