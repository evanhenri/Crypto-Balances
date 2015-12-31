from queue import Queue
from threading import Thread

from src import config
from src import util
from src.address import Address, Family


class Portfolio(object):
    def __init__(self):
        self.addresses = {}
        self.exclusion_lst = [i.upper() for i in util.list_from_file(config.exclusions_file)]

        addr_data = util.json_from_file(config.address_file)

        for addr_family, addr_lst in addr_data.items():
            for addr in addr_lst:
                self.addresses[addr] = Address(addr, Family(addr_family))

    def add_address(self, addr, address_obj):
        self.addresses[addr] = address_obj

    def get_balances(self):
        self.addresses = dict(filter(lambda x: x[1].family() not in self.exclusion_lst, self.addresses.items()))
        self.multi_request()
        self.multi_asset()
        self.single_asset_single_request()

    def _set_balance(self, _address, _asset_type, _balance):
        self.addresses[_address].balance[_asset_type] = _balance

    def multi_request(self):
        q = Queue()
        addr_lst = list(filter(lambda x: x[1].multi_request_flag, self.addresses.items()))###############################errorr here AttributeError: 'Address' object has no attribute 'multi_request_flag'
        if len(addr_lst) > 0:
            max_per_call = addr_lst[0].family.multi_request_max
            api_base = addr_lst[0].family.api_base
            data_key = addr_lst[0].family.data_key
            id_key = addr_lst[0].family.id_key
            balance_key = addr_lst[0].family.balance_key
            multiplier = addr_lst[0].family.multiplier
            addr_chunks = util.chunk_list(addr_lst, max_per_call)
            threads = []
            for chunk in addr_chunks:
                addrs = util.merge_lst(chunk, ['', ','])
                threads.append(Thread(target=util.api_call, args=(api_base, addrs, q)))
                threads[-1].start()
            [t.join() for t in threads]
            while not q.empty():
                # need to get address from within json reponse to differentiate the balance data,
                # ignore address in position 0 of [address, response] that is returned from q.get()
                raw_resp = q.get()[1]
                resp = util.json_value_by_key(raw_resp, data_key)
                for addr_data in resp:
                    addr = util.json_value_by_key(addr_data, id_key)
                    # blockr api sometime sends more responses than were requested as {'':0}, filter them out
                    if addr != '':
                        balance = util.json_value_by_key(addr_data, balance_key) * multiplier
                        self._set_balance(addr, self.addresses[addr].family(), balance)

    def multi_asset(self):
        q = Queue()
        addr_lst = list(filter(lambda x: x[1].multi_asset_flag, self.addresses.items()))
        if len(addr_lst) > 0:
            api_base = addr_lst[0].family.api_base
            data_key = addr_lst[0].family.data_key
            id_key = addr_lst[0].family.id_key
            balance_key = addr_lst[0].family.balance_key
            multiplier = addr_lst[0].family.multiplier
            threads = []
            for addr in addr_lst:
                threads.append(Thread(target=util.api_call, args=(api_base, addr, q)))
                threads[-1].start()
            [t.join() for t in threads]

            while not q.empty():
                addr, raw_resp = q.get()
                resp = util.json_value_by_key(raw_resp, data_key)

                for asset_data in resp:
                    asset_type = util.json_value_by_key(asset_data, id_key)
                    if asset_type.upper() not in self.exclusion_lst:
                        balance = util.json_value_by_key(asset_data, balance_key) * multiplier
                        self._set_balance(addr, asset_type, balance)

    def single_asset_single_request(self):
        q = Queue()
        addr_lst = list(filter(lambda x: not all([x[1].multi_request_flag, x[1].multi_asset_flag]), self.addresses.items()))
        if len(addr_lst) > 0:
            api_base = addr_lst[0].family.api_base
            data_key = addr_lst[0].family.data_key
            balance_key = addr_lst[0].family.balance_key
            multiplier = addr_lst[0].family.multiplier
            threads = []
            for addr in addr_lst:
                threads.append(Thread(target=util.api_call, args=(api_base, addr, q)))
                threads[-1].start()
            [t.join() for t in threads]

            while not q.empty():
                addr, raw_resp = q.get()
                resp = util.json_value_by_key(raw_resp, data_key)[0]
                balance = util.json_value_by_key(resp, balance_key) * multiplier
                self._set_balance(addr, self.addresses[addr].family(), balance)





