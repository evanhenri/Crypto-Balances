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

    def add_address(self, addr, addr_obj):
        self.addresses[addr] = addr_obj

    def get_balances(self):
        self.addresses = {k:v for (k,v) in self.addresses.items() if v.family() not in self.exclusion_lst}
        self.multi_request()
        self.multi_asset()
        self.single_asset_single_request()

    def update_balance(self, addr, asset_name, asset_balance):
        if asset_name in self.addresses[addr].asset_balances:
            self.addresses[addr].asset_balances[asset_name] += asset_balance
        else:
            self.addresses[addr].asset_balances[asset_name] = asset_balance

    def multi_request(self):
        multi_request_addresses = {k:v for (k,v) in self.addresses.items() if v.family.multi_request_flag}
        if len(multi_request_addresses) > 0:
            record = list(multi_request_addresses.values())[0]
            max_per_call = record.family.multi_request_max
            api_base = record.family.api_base
            data_key = record.family.data_key
            id_key = record.family.id_key
            balance_key = record.family.balance_key
            multiplier = record.family.multiplier
            addr_lst_chunks = util.chunk_list(list(multi_request_addresses.keys()), max_per_call)
            threads = []
            q = Queue()
            for addr_lst in addr_lst_chunks:
                addr_payload = util.merge_lst(addr_lst, ['', ','])
                threads.append(Thread(target=util.api_call, args=(api_base, addr_payload, q)))
                threads[-1].start()
            [t.join() for t in threads]
            while not q.empty():
                # need to get address from within json reponse to differentiate the balance data,
                # ignore address in position 0 of [address, response] that is returned from q.get()
                raw_resp = q.get()[1]
                resp_data = util.json_value_by_key(raw_resp, data_key)
                for addr_data in resp_data:
                    addr = util.json_value_by_key(addr_data, id_key)
                    # blockr api sometime sends more responses than were requested as {'':0}, filter them out
                    if addr != '':
                        balance = util.json_value_by_key(addr_data, balance_key) * multiplier
                        self.update_balance(addr, self.addresses[addr].family(), balance)

    def multi_asset(self):
        multi_asset_addresses = {k:v for (k, v) in self.addresses.items() if v.family.multi_asset_flag}
        if len(multi_asset_addresses) > 0:
            record = list(multi_asset_addresses.values())[0]
            api_base = record.family.api_base
            data_key = record.family.data_key
            id_key = record.family.id_key
            balance_key = record.family.balance_key
            multiplier = record.family.multiplier
            threads = []
            q = Queue()
            for addr in multi_asset_addresses.keys():
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
                        self.update_balance(addr, asset_type, balance)

    def single_asset_single_request(self):
        single_asset_addresses = {k:v for (k, v) in self.addresses.items() if v.family.single_asset_single_request}
        if len(single_asset_addresses) > 0:
            record = list(single_asset_addresses.values())[0]
            api_base = record.family.api_base
            data_key = record.family.data_key
            balance_key = record.family.balance_key
            multiplier = record.family.multiplier
            threads = []
            q = Queue()
            for addr in single_asset_addresses.keys():
                threads.append(Thread(target=util.api_call, args=(api_base, addr, q)))
                threads[-1].start()
            [t.join() for t in threads]

            while not q.empty():
                addr, raw_resp = q.get()
                resp = util.json_value_by_key(raw_resp, data_key)[0]
                balance = util.json_value_by_key(resp, balance_key) * multiplier
                self.update_balance(addr, self.addresses[addr].family(), balance)

    def print_address_balances(self):
        for addr, addr_obj in self.addresses.items():
            print(addr)
            for asset, balance in addr_obj.asset_balances.items():
                if asset not in self.exclusion_lst:
                    print('{0}\t{1}'.format(asset, balance))
            print()

    def print_total_balances(self):
        asset_totals = {}
        for addr_obj in self.addresses.values():
            for asset, balance in addr_obj.asset_balances.items():
                if asset not in self.exclusion_lst:
                    if asset in asset_totals:
                        asset_totals[asset] += float(balance)
                    else:
                        asset_totals[asset] = float(balance)
        for asset, balance in asset_totals.items():
            print('{0}\t{1}'.format(asset, balance))





