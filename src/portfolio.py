from queue import Queue
from threading import Thread

from src import util, exchange

class Family(object):
    def __init__(self, family, conf):
        self.family = family.upper()
        self.data_key = conf[self.family]['DATA_KEY']
        self.balance_key = conf[self.family]['BALANCE_KEY']
        self.api_base = conf[self.family]['API']
        self.id_key = conf[self.family]['ID_KEY']
        self.multi_asset_flag = conf[self.family]['MULTI_ASSET_FLAG']
        self.group_request_flag = conf[self.family]['MULTI_REQUEST_FLAG_MAX'][0]
        self.multi_request_max = conf[self.family]['MULTI_REQUEST_FLAG_MAX'][1]
        self.multiplier = conf[self.family]['MULTIPLIER']
        self.standard_flag = not any([self.multi_asset_flag, self.group_request_flag])
        self.addresses = []
    def __call__(self, *args, **kwargs):
        return self.family

class Asset(object):
    def __init__(self, balance):
        self.balance = balance
        self.price = 0
        self.value = 0

class Portfolio(object):
    def __init__(self, address_data, address_config, exclusion_lst=[]):
        self.addr_families = []
        self.addr_assets = {}
        self.exclusion_lst = [i.upper() for i in exclusion_lst]
        self.unique_assets = set()

        for addr_type, addr_lst in address_data.items():
            F = Family(addr_type, address_config)
            for addr in addr_lst:
                # initialize empty dict which will be filled with {asset_name:Asset obj,}
                self.addr_assets[addr] = {}
                # expand address list for each family object to match address config file
                F.addresses.append(addr)
            self.addr_families.append(F)

        for Fam in self.addr_families:
            if Fam.multi_asset_flag:
                self.multi_asset_requests(Fam)
            elif Fam.group_request_flag:
                self.group_requests(Fam)
            elif Fam.standard_flag:
                self.standard_requests(Fam)

    def filter_addr_assets(self, min_balance):
        filtered_addr_assets = {}
        for address, asset_data in self.addr_assets.items():
            filtered_addr_assets[address] = {}
            for asset_name, asset_obj in asset_data.items():
                if asset_name not in self.exclusion_lst and asset_obj.balance > min_balance:
                    filtered_addr_assets[address][asset_name] = asset_obj
        self.addr_assets = filtered_addr_assets

    def isempty(self):
        return len(self.addr_families) == 0

    def update_balance(self, addr, asset_name, asset_balance):
        if asset_name in self.addr_assets[addr]:
            self.addr_assets[addr][asset_name].balance += float(asset_balance)
        else:
            self.unique_assets.add(asset_name)
            self.addr_assets[addr][asset_name] = Asset(float(asset_balance))

    def multi_asset_requests(self, F):
        """
        for addresses that have multiple assets associated with each address e.g. Counterparty
        """
        q = Queue()
        multi_asset_threads = []
        for addr in F.addresses:
            multi_asset_threads.append(Thread(target=util.api_call, args=(F.api_base, addr, q)))
            multi_asset_threads[-1].start()
        [t.join() for t in multi_asset_threads]
        while not q.empty():
            addr, raw_resp = q.get()
            resp = util.json_value_by_key(raw_resp, F.data_key)
            for asset_data in resp:
                asset_name = util.json_value_by_key(asset_data, F.id_key)
                asset_balance = util.json_value_by_key(asset_data, F.balance_key) * F.multiplier
                self.update_balance(addr, asset_name, asset_balance)

    def group_requests(self, F):
        """
        for addresses where the specified api allows multiple addresses included in single api call
        """
        q = Queue()
        group_request_threads = []
        max_per_call = F.multi_request_max
        addr_lst_chunks = util.chunk_list(list(F.addresses), max_per_call)

        for nested_lst in addr_lst_chunks:
            addr_payload = util.merge_lst(nested_lst, ['', ','])
            group_request_threads.append(Thread(target=util.api_call, args=(F.api_base, addr_payload, q)))
            group_request_threads[-1].start()
        [t.join() for t in group_request_threads]
        while not q.empty():
            # need to get address from within json reponse to differentiate the balance data,
            # ignore address in position 0 of [address, response] that is returned from q.get()
            raw_resp = q.get()[1]
            resp_data = util.json_value_by_key(raw_resp, F.data_key)
            for addr_data in resp_data:
                addr = util.json_value_by_key(addr_data, F.id_key)
                # blockr api sometime sends more responses than were requested as {'':0}, filter them out
                if addr != '':
                    asset_name = F()
                    asset_balance = util.json_value_by_key(addr_data, F.balance_key) * F.multiplier
                    self.update_balance(addr, asset_name, asset_balance)

    def standard_requests(self, F):
        """
        for addresses that have a single asset and whose api has limit of one address per call
        """
        q = Queue()
        standard_threads = []
        for addr in F.addresses:
            standard_threads.append(Thread(target=util.api_call, args=(F.api_base, addr, q)))
            standard_threads[-1].start()
        [t.join() for t in standard_threads]
        while not q.empty():
            addr, raw_resp = q.get()
            resp = util.json_value_by_key(raw_resp, F.data_key)[0]
            asset_name = F()
            asset_balance = util.json_value_by_key(resp, F.balance_key) * F.multiplier
            self.update_balance(addr, asset_name, asset_balance)

    def get_asset_totals(self):
        """
        returns dictionary of {asset:balance} with combined totals for all address assets
        """
        asset_totals = {}
        for asset_data in self.addr_assets.values():
            for asset_name, asset_obj in asset_data.items():
                if asset_name in asset_totals:
                    asset_totals[asset_name] += float(asset_obj.balance)
                else:
                    asset_totals[asset_name] = float(asset_obj.balance)
        return asset_totals

    def print_address_balances(self, precision=8):
        """
        prints individual asset balances for each individual address
        """
        # do not print addresses with no assets to show
        formatted = {}
        longest_width = 0
        for address, asset_data in self.addr_assets.items():
            formatted[address] = {}
            for asset_name, asset_obj in asset_data.items():
                asset_obj.balance = '{0:,.{p}f}'.format(asset_obj.balance, p=precision)
                width = len('{0}{1}'.format(asset_name, asset_obj.balance))
                if width > longest_width: longest_width = width
                formatted[address][asset_name] = asset_obj

        for address, asset_data in formatted.items():
            print(address)
            for asset_name, asset_obj in asset_data.items():
                line_width = len('{0}{1}'.format(asset_name, asset_obj.balance))
                fill = '.' * (longest_width-line_width+5)
                print('{0}{1}{2}'.format(asset_name, fill, asset_obj.balance))
            print()

    def print_total_balances(self):
        """
        prints combined asset totals
        """
        asset_totals = self.get_asset_totals()

        # filter out exluded assets and assets with zero balance
        # format balances to 8 decimal places with commas in thousandths places to measure line lengths
        filtered_totals = {k:('{0:,.8f}'.format(v)) for k,v in asset_totals.items()
                           if k not in self.exclusion_lst and v > 0}
        longest_width = util.longest_kv_length(filtered_totals)

        for asset, balance in filtered_totals.items():
            line_width = len('{0}{1}'.format(asset, balance))
            fill = '.' * (longest_width-line_width+5)
            print('{0}{1}{2}'.format(asset, fill, balance))




