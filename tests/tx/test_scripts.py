import os
import json
import base64
import struct

from hathor.transaction.scripts import (
    HathorScript, op_pushdata, ScriptExtras,
    op_pushdata1, op_dup, op_equalverify, op_checksig, op_hash160,
    op_greaterthan_timestamp
)
from hathor.transaction.exceptions import OutOfData, MissingStackItems, EqualVerifyFailed, TimeLocked
from hathor.crypto.util import get_private_key_from_bytes, get_public_key_from_bytes, \
                               get_public_key_bytes_compressed, get_hash160

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes

from tests import unittest


class BasicTransaction(unittest.TestCase):
    def test_pushdata(self):
        stack = []
        random_bytes = b'a' * 50
        s = HathorScript()
        s.pushData(random_bytes)

        op_pushdata(0, s.data, stack)

        self.assertEqual(random_bytes, stack.pop())

        with self.assertRaises(OutOfData):
            op_pushdata(0, s.data[:-1], stack)

    def test_pushdata1(self):
        stack = []
        random_bytes = b'a' * 100
        s = HathorScript()
        s.pushData(random_bytes)

        op_pushdata1(0, s.data, stack)

        self.assertEqual(random_bytes, stack.pop())

        with self.assertRaises(OutOfData):
            op_pushdata1(0, s.data[:-1], stack)

    def test_dup(self):
        with self.assertRaises(MissingStackItems):
            op_dup([], log=[], extras=None)

        stack = [1]
        op_dup(stack, log=[], extras=None)
        self.assertEqual(stack[-1], stack[-2])

    def test_equalverify(self):
        elem = b'a'
        with self.assertRaises(MissingStackItems):
            op_equalverify([elem], log=[], extras=None)

        op_equalverify([elem, elem], log=[], extras=None)

        with self.assertRaises(EqualVerifyFailed):
            op_equalverify([elem, b'aaaa'], log=[], extras=None)

    def test_checksig(self):
        filepath = os.path.join(os.getcwd(), 'hathor/wallet/genesis_keys.json')
        dict_data = None
        with open(filepath, 'r') as json_file:
            dict_data = json.loads(json_file.read())
        b64_private_key = dict_data['private_key']
        b64_public_key = dict_data['public_key']
        private_key_bytes = base64.b64decode(b64_private_key)
        public_key_bytes = base64.b64decode(b64_public_key)
        genesis_private_key = get_private_key_from_bytes(private_key_bytes)
        genesis_public_key = get_public_key_from_bytes(public_key_bytes)

        with self.assertRaises(MissingStackItems):
            op_checksig([1], log=[], extras=None)

        from hathor.transaction.genesis import genesis_transactions
        block = [x for x in genesis_transactions(None) if x.is_block][0]

        from hathor.transaction import Transaction, TxInput, TxOutput
        txin = TxInput(tx_id=block.hash, index=0, data=b'')
        txout = TxOutput(value=block.outputs[0].value, script=b'')
        tx = Transaction(inputs=[txin], outputs=[txout])

        import hashlib
        data_to_sign = tx.get_sighash_all()
        hashed_data = hashlib.sha256(data_to_sign).digest()
        signature = genesis_private_key.sign(hashed_data, ec.ECDSA(hashes.SHA256()))
        pubkey_bytes = get_public_key_bytes_compressed(genesis_public_key)

        extras = ScriptExtras(tx=tx, txin=None, spent_tx=None)

        stack = [b'aaaaaaaaa', pubkey_bytes]
        op_checksig(stack, log=[], extras=extras)
        self.assertEqual(0, stack.pop())

        stack = [signature, pubkey_bytes]
        op_checksig(stack, log=[], extras=extras)
        self.assertEqual(1, stack.pop())

    def test_hash160(self):
        with self.assertRaises(MissingStackItems):
            op_checksig([], log=[], extras=None)

        elem = b'aaaaaaaa'
        hash160 = get_hash160(elem)
        stack = [elem]
        op_hash160(stack, log=[], extras=None)
        self.assertEqual(hash160, stack.pop())

    def test_greaterthan_timestamp(self):
        with self.assertRaises(MissingStackItems):
            op_greaterthan_timestamp([], log=[], extras=None)

        timestamp = 1234567

        from hathor.transaction import Transaction
        tx = Transaction()

        stack = [struct.pack('!I', timestamp)]
        extras = ScriptExtras(tx=tx, txin=None, spent_tx=None)

        with self.assertRaises(TimeLocked):
            tx.timestamp = timestamp - 1
            op_greaterthan_timestamp(list(stack), log=[], extras=extras)

        with self.assertRaises(TimeLocked):
            tx.timestamp = timestamp
            op_greaterthan_timestamp(list(stack), log=[], extras=extras)

        tx.timestamp = timestamp + 1
        op_greaterthan_timestamp(stack, log=[], extras=extras)
        self.assertEqual(len(stack), 0)


if __name__ == '__main__':
    unittest.main()
