"""DO NOT MODIFY: Tests generated from `VMTests/vmSystemOperations` with make_VMTests.py"""
import unittest
from binascii import unhexlify

import rlp
import sha3
from rlp.sedes import (
    CountableList,
    BigEndianInt,
    Binary,
)

from manticore.core.smtlib import ConstraintSet, Z3Solver  # Ignore unused import in non-symbolic tests!
from manticore.core.smtlib.visitors import to_constant
from manticore.platforms import evm
from manticore.utils import config
from manticore.core.state import Concretize



class Log(rlp.Serializable):
    fields = [
        ('address', Binary.fixed_length(20, allow_empty=True)),
        ('topics', CountableList(BigEndianInt(32))),
        ('data', Binary())
    ]


class EVMTest_vmSystemOperations(unittest.TestCase):
    # https://nose.readthedocs.io/en/latest/doc_tests/test_multiprocess/multiprocess.html#controlling-distribution
    _multiprocess_can_split_ = True
    # https://docs.python.org/3.7/library/unittest.html#unittest.TestCase.maxDiff
    maxDiff = None

    SAVED_DEFAULT_FORK = evm.DEFAULT_FORK

    @classmethod
    def setUpClass(cls):
        consts = config.get_group('evm')
        consts.oog = 'pedantic'
        evm.DEFAULT_FORK = 'frontier'

    @classmethod
    def tearDownClass(cls):
        evm.DEFAULT_FORK = cls.SAVED_DEFAULT_FORK

    def _test_run(self, world):
        result = None
        returndata = b''
        try:
            while True:
                try:
                    world.current_vm.execute()
                except Concretize as e:
                    value = self._solve(world.constraints, e.expression)
                    class fake_state:pass
                    fake_state = fake_state()
                    fake_state.platform = world
                    e.setstate(fake_state, value)
        except evm.EndTx as e:
            result = e.result
            if result in ('RETURN', 'REVERT'):
                returndata = self._solve(world.constraints, e.data)
        except evm.StartTx as e:
            self.fail('This tests should not initiate an internal tx (no CALLs allowed)')
        return result, returndata

    def _solve(self, constraints, val):
        results = Z3Solver.instance().get_all_values(constraints, val, maxcnt=3)
        # We constrain all values to single values!
        self.assertEqual(len(results), 1)
        return results[0]


    def test_return0(self):
        """
        Testcase taken from https://github.com/ethereum/tests
        File: return0.json
        sha256sum: 0317578f90e3f451ed9d51947d1303493022caa568aa4927eb113e1c9a0183e6
        Code:     PUSH1 0x37
                  PUSH1 0x0
                  MSTORE8
                  PUSH1 0x0
                  MLOAD
                  PUSH1 0x0
                  SSTORE
                  PUSH1 0x1
                  PUSH1 0x0
                  RETURN
        """    
    
        def solve(val):
            return self._solve(constraints, val)

        constraints = ConstraintSet()

        blocknumber = constraints.new_bitvec(256, name='blocknumber')
        constraints.add(blocknumber == 0)

        timestamp = constraints.new_bitvec(256, name='timestamp')
        constraints.add(timestamp == 1)

        difficulty = constraints.new_bitvec(256, name='difficulty')
        constraints.add(difficulty == 256)

        coinbase = constraints.new_bitvec(256, name='coinbase')
        constraints.add(coinbase == 244687034288125203496486448490407391986876152250)

        gaslimit = constraints.new_bitvec(256, name='gaslimit')
        constraints.add(gaslimit == 10000000)

        world = evm.EVMWorld(constraints, blocknumber=blocknumber, timestamp=timestamp, difficulty=difficulty,
                             coinbase=coinbase, gaslimit=gaslimit)
    
        acc_addr = 0xcd1722f3947def4cf144679da39c4c32bdc35681
        acc_code = unhexlify('603760005360005160005560016000f3')
            
        acc_balance = constraints.new_bitvec(256, name='balance_0xcd1722f3947def4cf144679da39c4c32bdc35681')
        constraints.add(acc_balance == 23)

        acc_nonce = constraints.new_bitvec(256, name='nonce_0xcd1722f3947def4cf144679da39c4c32bdc35681')
        constraints.add(acc_nonce == 0)

        world.create_account(address=acc_addr, balance=acc_balance, code=acc_code, nonce=acc_nonce)

        address = 0xcd1722f3947def4cf144679da39c4c32bdc35681
        caller = 0xf572e5295c57f15886f9b263e2f6d2d6c7b5ec6
        price = constraints.new_bitvec(256, name='price')
        constraints.add(price == 100000000000000)

        value = constraints.new_bitvec(256, name='value')
        constraints.add(value == 23)

        gas = constraints.new_bitvec(256, name='gas')
        constraints.add(gas == 100000)

        data = constraints.new_array(index_max=1)
        constraints.add(data == b'\xaa')

        # open a fake tx, no funds send
        world._open_transaction('CALL', address, price, data, caller, value, gas=gas)

        # This variable might seem redundant in some tests - don't forget it is auto generated
        # and there are cases in which we need it ;)
        result, returndata = self._test_run(world)

        # World sanity checks - those should not change, right?
        self.assertEqual(solve(world.block_number()), 0)
        self.assertEqual(solve(world.block_gaslimit()), 10000000)
        self.assertEqual(solve(world.block_timestamp()), 1)
        self.assertEqual(solve(world.block_difficulty()), 256)
        self.assertEqual(solve(world.block_coinbase()), 0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba)

        # Add post checks for account 0xcd1722f3947def4cf144679da39c4c32bdc35681
        # check nonce, balance, code
        self.assertEqual(solve(world.get_nonce(0xcd1722f3947def4cf144679da39c4c32bdc35681)), 0)
        self.assertEqual(solve(world.get_balance(0xcd1722f3947def4cf144679da39c4c32bdc35681)), 23)
        self.assertEqual(world.get_code(0xcd1722f3947def4cf144679da39c4c32bdc35681), unhexlify('603760005360005160005560016000f3'))
        # check storage
        self.assertEqual(solve(world.get_storage_data(0xcd1722f3947def4cf144679da39c4c32bdc35681, 0x00)), 0x3700000000000000000000000000000000000000000000000000000000000000)
        # check outs
        self.assertEqual(returndata, unhexlify('37'))
        # check logs
        logs = [Log(unhexlify('{:040x}'.format(l.address)), l.topics, solve(l.memlog)) for l in world.logs]
        data = rlp.encode(logs)
        self.assertEqual(sha3.keccak_256(data).hexdigest(), '1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347')

        # test used gas
        self.assertEqual(solve(world.current_vm.gas), 79973)

    def test_TestNameRegistrator(self):
        """
        Testcase taken from https://github.com/ethereum/tests
        File: TestNameRegistrator.json
        sha256sum: dd000f5977416de19410170b8a7acb5060011594fd97c81f307f015cd5bdd51e
        Code:     PUSH1 0x0
                  CALLDATALOAD
                  SLOAD
                  ISZERO
                  PUSH1 0x9
                  JUMPI
                  STOP
                  JUMPDEST
                  PUSH1 0x20
                  CALLDATALOAD
                  PUSH1 0x0
                  CALLDATALOAD
                  SSTORE
        """    
    
        def solve(val):
            return self._solve(constraints, val)

        constraints = ConstraintSet()

        blocknumber = constraints.new_bitvec(256, name='blocknumber')
        constraints.add(blocknumber == 0)

        timestamp = constraints.new_bitvec(256, name='timestamp')
        constraints.add(timestamp == 1)

        difficulty = constraints.new_bitvec(256, name='difficulty')
        constraints.add(difficulty == 256)

        coinbase = constraints.new_bitvec(256, name='coinbase')
        constraints.add(coinbase == 244687034288125203496486448490407391986876152250)

        gaslimit = constraints.new_bitvec(256, name='gaslimit')
        constraints.add(gaslimit == 1000000)

        world = evm.EVMWorld(constraints, blocknumber=blocknumber, timestamp=timestamp, difficulty=difficulty,
                             coinbase=coinbase, gaslimit=gaslimit)
    
        acc_addr = 0xf572e5295c57f15886f9b263e2f6d2d6c7b5ec6
        acc_code = unhexlify('6000355415600957005b60203560003555')
            
        acc_balance = constraints.new_bitvec(256, name='balance_0xf572e5295c57f15886f9b263e2f6d2d6c7b5ec6')
        constraints.add(acc_balance == 100000000000000000000000)

        acc_nonce = constraints.new_bitvec(256, name='nonce_0xf572e5295c57f15886f9b263e2f6d2d6c7b5ec6')
        constraints.add(acc_nonce == 0)

        world.create_account(address=acc_addr, balance=acc_balance, code=acc_code, nonce=acc_nonce)

        address = 0xf572e5295c57f15886f9b263e2f6d2d6c7b5ec6
        caller = 0xcd1722f3947def4cf144679da39c4c32bdc35681
        price = constraints.new_bitvec(256, name='price')
        constraints.add(price == 100000000000000)

        value = constraints.new_bitvec(256, name='value')
        constraints.add(value == 1000000000000000000)

        gas = constraints.new_bitvec(256, name='gas')
        constraints.add(gas == 100000)

        data = constraints.new_array(index_max=64)
        constraints.add(data == b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xfa\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xfa')

        # open a fake tx, no funds send
        world._open_transaction('CALL', address, price, data, caller, value, gas=gas)

        # This variable might seem redundant in some tests - don't forget it is auto generated
        # and there are cases in which we need it ;)
        result, returndata = self._test_run(world)

        # World sanity checks - those should not change, right?
        self.assertEqual(solve(world.block_number()), 0)
        self.assertEqual(solve(world.block_gaslimit()), 1000000)
        self.assertEqual(solve(world.block_timestamp()), 1)
        self.assertEqual(solve(world.block_difficulty()), 256)
        self.assertEqual(solve(world.block_coinbase()), 0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba)

        # Add post checks for account 0xf572e5295c57f15886f9b263e2f6d2d6c7b5ec6
        # check nonce, balance, code
        self.assertEqual(solve(world.get_nonce(0xf572e5295c57f15886f9b263e2f6d2d6c7b5ec6)), 0)
        self.assertEqual(solve(world.get_balance(0xf572e5295c57f15886f9b263e2f6d2d6c7b5ec6)), 100000000000000000000000)
        self.assertEqual(world.get_code(0xf572e5295c57f15886f9b263e2f6d2d6c7b5ec6), unhexlify('6000355415600957005b60203560003555'))
        # check storage
        self.assertEqual(solve(world.get_storage_data(0xf572e5295c57f15886f9b263e2f6d2d6c7b5ec6, 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffa)), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffa)
        # check outs
        self.assertEqual(returndata, unhexlify(''))
        # check logs
        logs = [Log(unhexlify('{:040x}'.format(l.address)), l.topics, solve(l.memlog)) for l in world.logs]
        data = rlp.encode(logs)
        self.assertEqual(sha3.keccak_256(data).hexdigest(), '1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347')

        # test used gas
        self.assertEqual(solve(world.current_vm.gas), 79915)

    def test_suicide0(self):
        """
        Testcase taken from https://github.com/ethereum/tests
        File: suicide0.json
        sha256sum: b6a8903cf90bc139d273b9408ec6aad5832bc94a2f87ee21cc018a4f1aea2fd8
        Code:     CALLER
                  SELFDESTRUCT
        """    
    
        def solve(val):
            return self._solve(constraints, val)

        constraints = ConstraintSet()

        blocknumber = constraints.new_bitvec(256, name='blocknumber')
        constraints.add(blocknumber == 0)

        timestamp = constraints.new_bitvec(256, name='timestamp')
        constraints.add(timestamp == 1)

        difficulty = constraints.new_bitvec(256, name='difficulty')
        constraints.add(difficulty == 256)

        coinbase = constraints.new_bitvec(256, name='coinbase')
        constraints.add(coinbase == 244687034288125203496486448490407391986876152250)

        gaslimit = constraints.new_bitvec(256, name='gaslimit')
        constraints.add(gaslimit == 10000000)

        world = evm.EVMWorld(constraints, blocknumber=blocknumber, timestamp=timestamp, difficulty=difficulty,
                             coinbase=coinbase, gaslimit=gaslimit)
    
        acc_addr = 0xf572e5295c57f15886f9b263e2f6d2d6c7b5ec6
        acc_code = unhexlify('33ff')
            
        acc_balance = constraints.new_bitvec(256, name='balance_0xf572e5295c57f15886f9b263e2f6d2d6c7b5ec6')
        constraints.add(acc_balance == 100000000000000000000000)

        acc_nonce = constraints.new_bitvec(256, name='nonce_0xf572e5295c57f15886f9b263e2f6d2d6c7b5ec6')
        constraints.add(acc_nonce == 0)

        world.create_account(address=acc_addr, balance=acc_balance, code=acc_code, nonce=acc_nonce)

        acc_addr = 0xcd1722f3947def4cf144679da39c4c32bdc35681
        acc_code = unhexlify('6000355415600957005b60203560003555')
            
        acc_balance = constraints.new_bitvec(256, name='balance_0xcd1722f3947def4cf144679da39c4c32bdc35681')
        constraints.add(acc_balance == 23)

        acc_nonce = constraints.new_bitvec(256, name='nonce_0xcd1722f3947def4cf144679da39c4c32bdc35681')
        constraints.add(acc_nonce == 0)

        world.create_account(address=acc_addr, balance=acc_balance, code=acc_code, nonce=acc_nonce)

        address = 0xf572e5295c57f15886f9b263e2f6d2d6c7b5ec6
        caller = 0xcd1722f3947def4cf144679da39c4c32bdc35681
        price = constraints.new_bitvec(256, name='price')
        constraints.add(price == 100000000000000)

        value = constraints.new_bitvec(256, name='value')
        constraints.add(value == 100000)

        gas = constraints.new_bitvec(256, name='gas')
        constraints.add(gas == 1000)

        data = ''
        # open a fake tx, no funds send
        world._open_transaction('CALL', address, price, data, caller, value, gas=gas)

        # This variable might seem redundant in some tests - don't forget it is auto generated
        # and there are cases in which we need it ;)
        result, returndata = self._test_run(world)

        # World sanity checks - those should not change, right?
        self.assertEqual(solve(world.block_number()), 0)
        self.assertEqual(solve(world.block_gaslimit()), 10000000)
        self.assertEqual(solve(world.block_timestamp()), 1)
        self.assertEqual(solve(world.block_difficulty()), 256)
        self.assertEqual(solve(world.block_coinbase()), 0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba)

        # Add post checks for account 0xcd1722f3947def4cf144679da39c4c32bdc35681
        # check nonce, balance, code
        self.assertEqual(solve(world.get_nonce(0xcd1722f3947def4cf144679da39c4c32bdc35681)), 0)
        self.assertEqual(solve(world.get_balance(0xcd1722f3947def4cf144679da39c4c32bdc35681)), 100000000000000000000023)
        self.assertEqual(world.get_code(0xcd1722f3947def4cf144679da39c4c32bdc35681), unhexlify('6000355415600957005b60203560003555'))
        # check outs
        self.assertEqual(returndata, unhexlify(''))
        # check logs
        logs = [Log(unhexlify('{:040x}'.format(l.address)), l.topics, solve(l.memlog)) for l in world.logs]
        data = rlp.encode(logs)
        self.assertEqual(sha3.keccak_256(data).hexdigest(), '1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347')

        # test used gas
        self.assertEqual(solve(world.current_vm.gas), 998)

    def test_return1(self):
        """
        Testcase taken from https://github.com/ethereum/tests
        File: return1.json
        sha256sum: 8bb16dfbc95077f7abc51d07cdba90b310b680750f22ad7bd5aaa1b4bda98d08
        Code:     PUSH1 0x37
                  PUSH1 0x0
                  MSTORE8
                  PUSH1 0x0
                  MLOAD
                  PUSH1 0x0
                  SSTORE
                  PUSH1 0x2
                  PUSH1 0x0
                  RETURN
        """    
    
        def solve(val):
            return self._solve(constraints, val)

        constraints = ConstraintSet()

        blocknumber = constraints.new_bitvec(256, name='blocknumber')
        constraints.add(blocknumber == 0)

        timestamp = constraints.new_bitvec(256, name='timestamp')
        constraints.add(timestamp == 1)

        difficulty = constraints.new_bitvec(256, name='difficulty')
        constraints.add(difficulty == 256)

        coinbase = constraints.new_bitvec(256, name='coinbase')
        constraints.add(coinbase == 244687034288125203496486448490407391986876152250)

        gaslimit = constraints.new_bitvec(256, name='gaslimit')
        constraints.add(gaslimit == 10000000)

        world = evm.EVMWorld(constraints, blocknumber=blocknumber, timestamp=timestamp, difficulty=difficulty,
                             coinbase=coinbase, gaslimit=gaslimit)
    
        acc_addr = 0xcd1722f3947def4cf144679da39c4c32bdc35681
        acc_code = unhexlify('603760005360005160005560026000f3')
            
        acc_balance = constraints.new_bitvec(256, name='balance_0xcd1722f3947def4cf144679da39c4c32bdc35681')
        constraints.add(acc_balance == 23)

        acc_nonce = constraints.new_bitvec(256, name='nonce_0xcd1722f3947def4cf144679da39c4c32bdc35681')
        constraints.add(acc_nonce == 0)

        world.create_account(address=acc_addr, balance=acc_balance, code=acc_code, nonce=acc_nonce)

        address = 0xcd1722f3947def4cf144679da39c4c32bdc35681
        caller = 0xf572e5295c57f15886f9b263e2f6d2d6c7b5ec6
        price = constraints.new_bitvec(256, name='price')
        constraints.add(price == 100000000000000)

        value = constraints.new_bitvec(256, name='value')
        constraints.add(value == 23)

        gas = constraints.new_bitvec(256, name='gas')
        constraints.add(gas == 100000)

        data = constraints.new_array(index_max=1)
        constraints.add(data == b'\xaa')

        # open a fake tx, no funds send
        world._open_transaction('CALL', address, price, data, caller, value, gas=gas)

        # This variable might seem redundant in some tests - don't forget it is auto generated
        # and there are cases in which we need it ;)
        result, returndata = self._test_run(world)

        # World sanity checks - those should not change, right?
        self.assertEqual(solve(world.block_number()), 0)
        self.assertEqual(solve(world.block_gaslimit()), 10000000)
        self.assertEqual(solve(world.block_timestamp()), 1)
        self.assertEqual(solve(world.block_difficulty()), 256)
        self.assertEqual(solve(world.block_coinbase()), 0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba)

        # Add post checks for account 0xcd1722f3947def4cf144679da39c4c32bdc35681
        # check nonce, balance, code
        self.assertEqual(solve(world.get_nonce(0xcd1722f3947def4cf144679da39c4c32bdc35681)), 0)
        self.assertEqual(solve(world.get_balance(0xcd1722f3947def4cf144679da39c4c32bdc35681)), 23)
        self.assertEqual(world.get_code(0xcd1722f3947def4cf144679da39c4c32bdc35681), unhexlify('603760005360005160005560026000f3'))
        # check storage
        self.assertEqual(solve(world.get_storage_data(0xcd1722f3947def4cf144679da39c4c32bdc35681, 0x00)), 0x3700000000000000000000000000000000000000000000000000000000000000)
        # check outs
        self.assertEqual(returndata, unhexlify('3700'))
        # check logs
        logs = [Log(unhexlify('{:040x}'.format(l.address)), l.topics, solve(l.memlog)) for l in world.logs]
        data = rlp.encode(logs)
        self.assertEqual(sha3.keccak_256(data).hexdigest(), '1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347')

        # test used gas
        self.assertEqual(solve(world.current_vm.gas), 79973)

    def test_suicideNotExistingAccount(self):
        """
        Testcase taken from https://github.com/ethereum/tests
        File: suicideNotExistingAccount.json
        sha256sum: e2cb030ec446c6acca6c87a741d254ededf0713f3147b6e5e725d6795b4b9fea
        Code:     PUSH20 0xaa1722f3947def4cf144679da39c4c32bdc35681
                  SELFDESTRUCT
        """    
    
        def solve(val):
            return self._solve(constraints, val)

        constraints = ConstraintSet()

        blocknumber = constraints.new_bitvec(256, name='blocknumber')
        constraints.add(blocknumber == 0)

        timestamp = constraints.new_bitvec(256, name='timestamp')
        constraints.add(timestamp == 1)

        difficulty = constraints.new_bitvec(256, name='difficulty')
        constraints.add(difficulty == 256)

        coinbase = constraints.new_bitvec(256, name='coinbase')
        constraints.add(coinbase == 244687034288125203496486448490407391986876152250)

        gaslimit = constraints.new_bitvec(256, name='gaslimit')
        constraints.add(gaslimit == 10000000)

        world = evm.EVMWorld(constraints, blocknumber=blocknumber, timestamp=timestamp, difficulty=difficulty,
                             coinbase=coinbase, gaslimit=gaslimit)
    
        acc_addr = 0xf572e5295c57f15886f9b263e2f6d2d6c7b5ec6
        acc_code = unhexlify('73aa1722f3947def4cf144679da39c4c32bdc35681ff')
            
        acc_balance = constraints.new_bitvec(256, name='balance_0xf572e5295c57f15886f9b263e2f6d2d6c7b5ec6')
        constraints.add(acc_balance == 100000000000000000000000)

        acc_nonce = constraints.new_bitvec(256, name='nonce_0xf572e5295c57f15886f9b263e2f6d2d6c7b5ec6')
        constraints.add(acc_nonce == 0)

        world.create_account(address=acc_addr, balance=acc_balance, code=acc_code, nonce=acc_nonce)

        acc_addr = 0xcd1722f3947def4cf144679da39c4c32bdc35681
        acc_code = unhexlify('6000355415600957005b60203560003555')
            
        acc_balance = constraints.new_bitvec(256, name='balance_0xcd1722f3947def4cf144679da39c4c32bdc35681')
        constraints.add(acc_balance == 23)

        acc_nonce = constraints.new_bitvec(256, name='nonce_0xcd1722f3947def4cf144679da39c4c32bdc35681')
        constraints.add(acc_nonce == 0)

        world.create_account(address=acc_addr, balance=acc_balance, code=acc_code, nonce=acc_nonce)

        address = 0xf572e5295c57f15886f9b263e2f6d2d6c7b5ec6
        caller = 0xcd1722f3947def4cf144679da39c4c32bdc35681
        price = constraints.new_bitvec(256, name='price')
        constraints.add(price == 100000000000000)

        value = constraints.new_bitvec(256, name='value')
        constraints.add(value == 100000)

        gas = constraints.new_bitvec(256, name='gas')
        constraints.add(gas == 1000)

        data = ''
        # open a fake tx, no funds send
        world._open_transaction('CALL', address, price, data, caller, value, gas=gas)

        # This variable might seem redundant in some tests - don't forget it is auto generated
        # and there are cases in which we need it ;)
        result, returndata = self._test_run(world)

        # World sanity checks - those should not change, right?
        self.assertEqual(solve(world.block_number()), 0)
        self.assertEqual(solve(world.block_gaslimit()), 10000000)
        self.assertEqual(solve(world.block_timestamp()), 1)
        self.assertEqual(solve(world.block_difficulty()), 256)
        self.assertEqual(solve(world.block_coinbase()), 0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba)

        # Add post checks for account 0xaa1722f3947def4cf144679da39c4c32bdc35681
        # check nonce, balance, code
        self.assertEqual(solve(world.get_nonce(0xaa1722f3947def4cf144679da39c4c32bdc35681)), 0)
        self.assertEqual(solve(world.get_balance(0xaa1722f3947def4cf144679da39c4c32bdc35681)), 100000000000000000000000)
        self.assertEqual(world.get_code(0xaa1722f3947def4cf144679da39c4c32bdc35681), unhexlify(''))
        # Add post checks for account 0xcd1722f3947def4cf144679da39c4c32bdc35681
        # check nonce, balance, code
        self.assertEqual(solve(world.get_nonce(0xcd1722f3947def4cf144679da39c4c32bdc35681)), 0)
        self.assertEqual(solve(world.get_balance(0xcd1722f3947def4cf144679da39c4c32bdc35681)), 23)
        self.assertEqual(world.get_code(0xcd1722f3947def4cf144679da39c4c32bdc35681), unhexlify('6000355415600957005b60203560003555'))
        # check outs
        self.assertEqual(returndata, unhexlify(''))
        # check logs
        logs = [Log(unhexlify('{:040x}'.format(l.address)), l.topics, solve(l.memlog)) for l in world.logs]
        data = rlp.encode(logs)
        self.assertEqual(sha3.keccak_256(data).hexdigest(), '1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347')

        # test used gas
        self.assertEqual(solve(world.current_vm.gas), 997)

    def test_suicideSendEtherToMe(self):
        """
        Testcase taken from https://github.com/ethereum/tests
        File: suicideSendEtherToMe.json
        sha256sum: 2ff81b7cdd2b1dd1f69c4bc9ba0b7369b4c624291d5021fbe638ce130a18df26
        Code:     ADDRESS
                  SELFDESTRUCT
        """    
    
        def solve(val):
            return self._solve(constraints, val)

        constraints = ConstraintSet()

        blocknumber = constraints.new_bitvec(256, name='blocknumber')
        constraints.add(blocknumber == 0)

        timestamp = constraints.new_bitvec(256, name='timestamp')
        constraints.add(timestamp == 1)

        difficulty = constraints.new_bitvec(256, name='difficulty')
        constraints.add(difficulty == 256)

        coinbase = constraints.new_bitvec(256, name='coinbase')
        constraints.add(coinbase == 244687034288125203496486448490407391986876152250)

        gaslimit = constraints.new_bitvec(256, name='gaslimit')
        constraints.add(gaslimit == 10000000)

        world = evm.EVMWorld(constraints, blocknumber=blocknumber, timestamp=timestamp, difficulty=difficulty,
                             coinbase=coinbase, gaslimit=gaslimit)
    
        acc_addr = 0xf572e5295c57f15886f9b263e2f6d2d6c7b5ec6
        acc_code = unhexlify('30ff')
            
        acc_balance = constraints.new_bitvec(256, name='balance_0xf572e5295c57f15886f9b263e2f6d2d6c7b5ec6')
        constraints.add(acc_balance == 100000000000000000000000)

        acc_nonce = constraints.new_bitvec(256, name='nonce_0xf572e5295c57f15886f9b263e2f6d2d6c7b5ec6')
        constraints.add(acc_nonce == 0)

        world.create_account(address=acc_addr, balance=acc_balance, code=acc_code, nonce=acc_nonce)

        acc_addr = 0xcd1722f3947def4cf144679da39c4c32bdc35681
        acc_code = unhexlify('6000355415600957005b60203560003555')
            
        acc_balance = constraints.new_bitvec(256, name='balance_0xcd1722f3947def4cf144679da39c4c32bdc35681')
        constraints.add(acc_balance == 23)

        acc_nonce = constraints.new_bitvec(256, name='nonce_0xcd1722f3947def4cf144679da39c4c32bdc35681')
        constraints.add(acc_nonce == 0)

        world.create_account(address=acc_addr, balance=acc_balance, code=acc_code, nonce=acc_nonce)

        address = 0xf572e5295c57f15886f9b263e2f6d2d6c7b5ec6
        caller = 0xcd1722f3947def4cf144679da39c4c32bdc35681
        price = constraints.new_bitvec(256, name='price')
        constraints.add(price == 100000000000000)

        value = constraints.new_bitvec(256, name='value')
        constraints.add(value == 100000)

        gas = constraints.new_bitvec(256, name='gas')
        constraints.add(gas == 1000)

        data = ''
        # open a fake tx, no funds send
        world._open_transaction('CALL', address, price, data, caller, value, gas=gas)

        # This variable might seem redundant in some tests - don't forget it is auto generated
        # and there are cases in which we need it ;)
        result, returndata = self._test_run(world)

        # World sanity checks - those should not change, right?
        self.assertEqual(solve(world.block_number()), 0)
        self.assertEqual(solve(world.block_gaslimit()), 10000000)
        self.assertEqual(solve(world.block_timestamp()), 1)
        self.assertEqual(solve(world.block_difficulty()), 256)
        self.assertEqual(solve(world.block_coinbase()), 0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba)

        # Add post checks for account 0xcd1722f3947def4cf144679da39c4c32bdc35681
        # check nonce, balance, code
        self.assertEqual(solve(world.get_nonce(0xcd1722f3947def4cf144679da39c4c32bdc35681)), 0)
        self.assertEqual(solve(world.get_balance(0xcd1722f3947def4cf144679da39c4c32bdc35681)), 23)
        self.assertEqual(world.get_code(0xcd1722f3947def4cf144679da39c4c32bdc35681), unhexlify('6000355415600957005b60203560003555'))
        # check outs
        self.assertEqual(returndata, unhexlify(''))
        # check logs
        logs = [Log(unhexlify('{:040x}'.format(l.address)), l.topics, solve(l.memlog)) for l in world.logs]
        data = rlp.encode(logs)
        self.assertEqual(sha3.keccak_256(data).hexdigest(), '1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347')

        # test used gas
        self.assertEqual(solve(world.current_vm.gas), 998)

    def test_return2(self):
        """
        Testcase taken from https://github.com/ethereum/tests
        File: return2.json
        sha256sum: 25972361a5871003f44467255a656b9e7ba3762a5cfe02b56a0197318d375b9a
        Code:     PUSH1 0x37
                  PUSH1 0x0
                  MSTORE8
                  PUSH1 0x0
                  MLOAD
                  PUSH1 0x0
                  SSTORE
                  PUSH1 0x21
                  PUSH1 0x0
                  RETURN
        """    
    
        def solve(val):
            return self._solve(constraints, val)

        constraints = ConstraintSet()

        blocknumber = constraints.new_bitvec(256, name='blocknumber')
        constraints.add(blocknumber == 0)

        timestamp = constraints.new_bitvec(256, name='timestamp')
        constraints.add(timestamp == 1)

        difficulty = constraints.new_bitvec(256, name='difficulty')
        constraints.add(difficulty == 256)

        coinbase = constraints.new_bitvec(256, name='coinbase')
        constraints.add(coinbase == 244687034288125203496486448490407391986876152250)

        gaslimit = constraints.new_bitvec(256, name='gaslimit')
        constraints.add(gaslimit == 10000000)

        world = evm.EVMWorld(constraints, blocknumber=blocknumber, timestamp=timestamp, difficulty=difficulty,
                             coinbase=coinbase, gaslimit=gaslimit)
    
        acc_addr = 0xcd1722f3947def4cf144679da39c4c32bdc35681
        acc_code = unhexlify('603760005360005160005560216000f3')
            
        acc_balance = constraints.new_bitvec(256, name='balance_0xcd1722f3947def4cf144679da39c4c32bdc35681')
        constraints.add(acc_balance == 23)

        acc_nonce = constraints.new_bitvec(256, name='nonce_0xcd1722f3947def4cf144679da39c4c32bdc35681')
        constraints.add(acc_nonce == 0)

        world.create_account(address=acc_addr, balance=acc_balance, code=acc_code, nonce=acc_nonce)

        address = 0xcd1722f3947def4cf144679da39c4c32bdc35681
        caller = 0xf572e5295c57f15886f9b263e2f6d2d6c7b5ec6
        price = constraints.new_bitvec(256, name='price')
        constraints.add(price == 100000000000000)

        value = constraints.new_bitvec(256, name='value')
        constraints.add(value == 23)

        gas = constraints.new_bitvec(256, name='gas')
        constraints.add(gas == 100000)

        data = constraints.new_array(index_max=1)
        constraints.add(data == b'\xaa')

        # open a fake tx, no funds send
        world._open_transaction('CALL', address, price, data, caller, value, gas=gas)

        # This variable might seem redundant in some tests - don't forget it is auto generated
        # and there are cases in which we need it ;)
        result, returndata = self._test_run(world)

        # World sanity checks - those should not change, right?
        self.assertEqual(solve(world.block_number()), 0)
        self.assertEqual(solve(world.block_gaslimit()), 10000000)
        self.assertEqual(solve(world.block_timestamp()), 1)
        self.assertEqual(solve(world.block_difficulty()), 256)
        self.assertEqual(solve(world.block_coinbase()), 0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba)

        # Add post checks for account 0xcd1722f3947def4cf144679da39c4c32bdc35681
        # check nonce, balance, code
        self.assertEqual(solve(world.get_nonce(0xcd1722f3947def4cf144679da39c4c32bdc35681)), 0)
        self.assertEqual(solve(world.get_balance(0xcd1722f3947def4cf144679da39c4c32bdc35681)), 23)
        self.assertEqual(world.get_code(0xcd1722f3947def4cf144679da39c4c32bdc35681), unhexlify('603760005360005160005560216000f3'))
        # check storage
        self.assertEqual(solve(world.get_storage_data(0xcd1722f3947def4cf144679da39c4c32bdc35681, 0x00)), 0x3700000000000000000000000000000000000000000000000000000000000000)
        # check outs
        self.assertEqual(returndata, unhexlify('370000000000000000000000000000000000000000000000000000000000000000'))
        # check logs
        logs = [Log(unhexlify('{:040x}'.format(l.address)), l.topics, solve(l.memlog)) for l in world.logs]
        data = rlp.encode(logs)
        self.assertEqual(sha3.keccak_256(data).hexdigest(), '1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347')

        # test used gas
        self.assertEqual(solve(world.current_vm.gas), 79970)


if __name__ == '__main__':
    unittest.main()
