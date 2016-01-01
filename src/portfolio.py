from queue import Queue
from threading import Thread

from src import util
from src.address import Address, Family

class Portfolio(object):
    def __init__(self, address_dict, exclusion_lst):
        self.multi_asset_addresses = {}
        self.group_request_addresses = {}
        self.standard_addresses = {}
        self.exclusion_lst = [i.upper() for i in exclusion_lst]

        # Initialize Address by type and add to self.addresses dictionary where k=addr and v=Address
        for addr_family, addr_lst in address_dict.items():
            F = Family(addr_family)
            for addr in addr_lst:
                if F.multi_asset_flag:
                    self.multi_asset_addresses[addr] = Address(addr, F)
                elif F.multi_request_max:
                    self.group_request_addresses[addr] = Address(addr, F)
                elif F.standard_flag:
                    self.standard_addresses[addr] = Address(addr, F)

        q = Queue()

        #multi_asset threaded api requests
        multi_asset_threads = []
        multi_asset_family = list(self.multi_asset_addresses.values())[0].family
        for addr in self.multi_asset_addresses.keys():
            multi_asset_threads.append(Thread(target=util.api_call, args=(multi_asset_family.api_base, addr, q)))
            multi_asset_threads[-1].start()
        [t.join() for t in multi_asset_threads]
        while not q.empty():
            addr, raw_resp = q.get()
            resp = util.json_value_by_key(raw_resp, multi_asset_family.data_key)

            for asset_data in resp:
                asset_type = util.json_value_by_key(asset_data, multi_asset_family.id_key)
                balance = util.json_value_by_key(asset_data, multi_asset_family.balance_key) * multi_asset_family.multiplier
                self.update_balance(addr, asset_type, balance, self.multi_asset_addresses)

        # group_address threaded api request
        group_request_threads = []
        group_request_family = list(self.group_request_addresses.values())[0].family
        max_per_call = group_request_family.multi_request_max
        addr_lst_chunks = util.chunk_list(list(self.group_request_addresses.keys()), max_per_call)

        for nested_lst in addr_lst_chunks:
            addr_payload = util.merge_lst(nested_lst, ['', ','])
            group_request_threads.append(Thread(target=util.api_call, args=(group_request_family.api_base, addr_payload, q)))
            group_request_threads[-1].start()
        [t.join() for t in group_request_threads]
        while not q.empty():
            # need to get address from within json reponse to differentiate the balance data,
            # ignore address in position 0 of [address, response] that is returned from q.get()
            raw_resp = q.get()[1]
            resp_data = util.json_value_by_key(raw_resp, group_request_family.data_key)
            for addr_data in resp_data:
                addr = util.json_value_by_key(addr_data, group_request_family.id_key)
                # blockr api sometime sends more responses than were requested as {'':0}, filter them out
                if addr != '':
                    balance = util.json_value_by_key(addr_data, group_request_family.balance_key) * group_request_family.multiplier
                    self.update_balance(addr, self.group_request_addresses[addr].family(), balance, self.group_request_addresses)

        # standard address threaded api request
        standard_threads = []
        standard_family = list(self.standard_addresses.values())[0].family
        for addr in self.standard_addresses.keys():
            standard_threads.append(Thread(target=util.api_call, args=(standard_family.api_base, addr, q)))
            standard_threads[-1].start()
        [t.join() for t in standard_threads]
        while not q.empty():
            addr, raw_resp = q.get()
            resp = util.json_value_by_key(raw_resp, standard_family.data_key)[0]
            balance = util.json_value_by_key(resp, standard_family.balance_key) * standard_family.multiplier
            self.update_balance(addr, self.standard_addresses[addr].family(), balance, self.standard_addresses)

    def update_balance(self, addr, asset_name, asset_balance, addr_family_dict):
        if asset_name in addr_family_dict[addr].asset_balances:
            addr_family_dict[addr].asset_balances[asset_name] += float(asset_balance)
        else:
            addr_family_dict[addr].asset_balances[asset_name] = float(asset_balance)

    def get_asset_totals(self):
        addresses = [self.multi_asset_addresses, self.group_request_addresses, self.standard_addresses]
        asset_totals = {}
        for addr_family in addresses:
            for addr_obj in addr_family.values():
                for asset, balance in addr_obj.asset_balances.items():
                    if asset in asset_totals:
                        asset_totals[asset] += float(balance)
                    else:
                        asset_totals[asset] = float(balance)
        return asset_totals

    def get_address_totals(self):
        addresses = [self.multi_asset_addresses, self.group_request_addresses, self.standard_addresses]
        address_totals = {}
        for addr_family in addresses:
            for addr, addr_obj in addr_family.items():
                for asset, balance in addr_obj.asset_balances.items():
                    if addr in address_totals:
                        if asset in address_totals[addr]:
                            address_totals[addr][asset] += float(balance)
                        else:
                            address_totals[addr][asset] = float(balance)
                    else:
                        address_totals[addr] = {}
        return address_totals

    def print_address_balances(self):
        address_totals = self.get_address_totals()

        for addr, addr_assets in address_totals.items():
            print(addr)
            for asset, balance in addr_assets.items():
                #if asset.upper() not in self.exclusion_lst:
                print('{0}\t{1}'.format(asset, balance))
            print()

    def print_total_balances(self):
        asset_totals = self.get_asset_totals()

        for asset, balance in asset_totals.items():
            #if asset.upper() not in self.exclusion_lst:
            print('{0}\t{1}'.format(asset, balance))





