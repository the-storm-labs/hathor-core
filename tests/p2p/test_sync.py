from twisted.python import log
from twisted.internet.task import Clock

from tests.utils import FakeConnection
from tests import unittest

import sys
import random
import base58


class HathorSyncMethodsTestCase(unittest.TestCase):
    def setUp(self):
        super().setUp()

        log.startLogging(sys.stdout)
        self.clock = Clock()
        self.network = 'testnet'
        self.manager1 = self.create_peer(self.network, unlock_wallet=True)

        self.genesis = self.manager1.tx_storage.get_all_genesis()
        self.genesis_blocks = [tx for tx in self.genesis if tx.is_block]

    def _add_new_tx(self, address, value):
        from hathor.transaction import Transaction
        from hathor.wallet.base_wallet import WalletOutputInfo

        outputs = []
        outputs.append(WalletOutputInfo(address=base58.b58decode(address), value=int(value)))

        tx = self.manager1.wallet.prepare_transaction_compute_inputs(Transaction, outputs)
        tx.weight = 10
        tx.parents = self.manager1.get_new_tx_parents()
        tx.resolve()
        self.manager1.propagate_tx(tx)

    def _add_new_transactions(self, num_txs):
        txs = []
        for _ in range(num_txs):
            address = '3JEcJKVsHddj1Td2KDjowZ1JqGF1'
            value = random.choice([500, 1000, 5000, 10000, 12000])
            tx = self._add_new_tx(address, value)
            txs.append(tx)
        return txs

    def _add_new_block(self):
        block = self.manager1.generate_mining_block()
        self.assertTrue(block.resolve())
        self.manager1.propagate_tx(block)
        return block

    def _add_new_blocks(self, num_blocks):
        blocks = []
        for _ in range(num_blocks):
            blocks.append(self._add_new_block())
        return blocks

    def test_get_blocks_before(self):
        genesis_block = self.genesis_blocks[0]
        result = self.manager1.tx_storage.get_blocks_before(genesis_block.hash.hex())
        self.assertEqual(0, len(result))

        blocks = self._add_new_blocks(20)
        num_blocks = 5

        for i, block in enumerate(blocks):
            result = self.manager1.tx_storage.get_blocks_before(block.hash.hex(), num_blocks=num_blocks)

            expected_result = [genesis_block] + blocks[:i]
            expected_result = expected_result[-num_blocks:]
            expected_result = expected_result[::-1]
            self.assertEqual(result, expected_result)

    def assertTipsEqual(self, manager1, manager2):
        s1 = set(manager1.tx_storage.get_tip_transactions_hashes())
        s1.update(manager1.tx_storage.get_tip_blocks_hashes())

        s2 = set(manager2.tx_storage.get_tip_transactions_hashes())
        s2.update(manager2.tx_storage.get_tip_blocks_hashes())

        self.assertEqual(s1, s2)

    def test_block_sync_only_genesis(self):
        manager2 = self.create_peer(self.network)
        self.assertEqual(manager2.state, manager2.NodeState.WAITING_FOR_PEERS)

        conn = FakeConnection(self.manager1, manager2)

        conn.run_one_step()  # HELLO
        conn.run_one_step()  # PEER-ID

        for _ in range(100):
            if not conn.tr1.value() and not conn.tr2.value():
                break
            conn.run_one_step()
            self.clock.advance(0.1)

        self.assertEqual(manager2.state, manager2.NodeState.SYNCED)
        self.assertTipsEqual(self.manager1, manager2)

    def test_block_sync_new_blocks(self):
        self._add_new_blocks(15)

        manager2 = self.create_peer(self.network)
        self.assertEqual(manager2.state, manager2.NodeState.WAITING_FOR_PEERS)

        conn = FakeConnection(self.manager1, manager2)

        for _ in range(100):
            if not conn.tr1.value() and not conn.tr2.value():
                break
            conn.run_one_step()
            self.clock.advance(0.1)

        self.assertEqual(manager2.state, manager2.NodeState.SYNCED)
        self.assertTipsEqual(self.manager1, manager2)

    def test_block_sync_many_new_blocks(self):
        self._add_new_blocks(150)

        manager2 = self.create_peer(self.network)
        self.assertEqual(manager2.state, manager2.NodeState.WAITING_FOR_PEERS)

        conn = FakeConnection(self.manager1, manager2)

        for idx in range(1000):
            if not conn.tr1.value() and not conn.tr2.value():
                break
            conn.run_one_step()
            self.clock.advance(0.1)

        self.assertEqual(manager2.state, manager2.NodeState.SYNCED)
        self.assertTipsEqual(self.manager1, manager2)

    def test_block_sync_new_blocks_and_txs(self):
        self._add_new_blocks(15)
        self._add_new_transactions(3)
        self._add_new_blocks(4)
        self._add_new_transactions(5)

        manager2 = self.create_peer(self.network)
        self.assertEqual(manager2.state, manager2.NodeState.WAITING_FOR_PEERS)

        conn = FakeConnection(self.manager1, manager2)

        for _ in range(500):
            if not conn.tr1.value() and not conn.tr2.value():
                break
            conn.run_one_step()
            self.clock.advance(0.1)

        self.assertEqual(manager2.state, manager2.NodeState.SYNCED)
        self.assertTipsEqual(self.manager1, manager2)

    def test_tx_propagation_nat_peers(self):
        """ manager1 <- manager2 <- manager3
        """
        self._add_new_blocks(5)

        manager2 = self.create_peer(self.network)
        conn1 = FakeConnection(self.manager1, manager2)

        for _ in range(50):
            conn1.run_one_step()
            self.clock.advance(0.1)
        self.assertTipsEqual(self.manager1, manager2)

        self._add_new_blocks(1)

        for _ in range(20):
            conn1.run_one_step()
            self.clock.advance(0.1)
        self.assertTipsEqual(self.manager1, manager2)

        manager3 = self.create_peer(self.network)
        conn2 = FakeConnection(manager2, manager3)

        for _ in range(50):
            conn1.run_one_step()
            conn2.run_one_step()
            self.clock.advance(0.1)

        self.assertEqual(self.manager1.state, self.manager1.NodeState.SYNCED)
        self.assertEqual(manager2.state, manager2.NodeState.SYNCED)
        self.assertEqual(manager3.state, manager3.NodeState.SYNCED)
        self.assertTipsEqual(self.manager1, manager2)
        self.assertTipsEqual(self.manager1, manager3)

        self._add_new_transactions(1)

        for _ in range(20):
            conn1.run_one_step()
            conn2.run_one_step()
            self.clock.advance(0.1)

        self.assertTipsEqual(self.manager1, manager2)
        self.assertTipsEqual(self.manager1, manager3)