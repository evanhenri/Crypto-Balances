from queue import Queue
from threading import Thread

from decimal import Decimal

from src import util, asset
from src.asset import Asset

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

class Portfolio(object):
    def __init__(self, address_data, address_config, exclusion_lst=[]):
        self.addr_families = []
        self.addr_assets = {}
        self.filtered_addr_assets = {}
        self.exclusion_lst = [i.upper() for i in exclusion_lst]
        self.unique_assets = set()
        self.asset_prices = {}

        for addr_type, addr_lst in address_data.items():
            F = Family(addr_type, address_config)
            for addr in addr_lst:
                # initialize empty dict which will be filled with {asset_name:asset_obj,}
                self.addr_assets[addr] = {}
                # expand address list for each family object to match address config file
                F.addresses.append(addr)
            self.addr_families.append(F)

        for Fam in self.addr_families:
            if Fam.multi_asset_flag:
                self.multi_asset_request(Fam)
            elif Fam.group_request_flag:
                self.group_request(Fam)
            elif Fam.standard_flag:
                self.standard_request(Fam)

    def filter_addr_assets(self, min_balance):
        for address, asset_data in self.addr_assets.items():
            self.filtered_addr_assets[address] = {}
            for asset_name, asset_obj in asset_data.items():
                if asset_name not in self.exclusion_lst and asset_obj.balance > min_balance:
                    self.filtered_addr_assets[address][asset_name] = asset_obj
                    self.unique_assets.add(asset_name)

    def get_asset_prices(self, base_currency):
        base_currency = base_currency.upper()
        AP = asset.Prices()
        for asset_name in self.unique_assets:
            price = AP.get(asset_name, base_currency)
            self.asset_prices[asset_name] = price

    def get_asset_totals(self):
        """
        returns dictionary of {asset:balance} with combined totals for all address assets
        """
        asset_totals = {}
        for asset_data in self.filtered_addr_assets.values():
            for asset_name, asset_obj in asset_data.items():
                if asset_name in asset_totals:
                    asset_totals[asset_name] += asset_obj.balance
                else:
                    asset_totals[asset_name] = asset_obj.balance
        return asset_totals

    def group_request(self, F):
        """
        for addresses where the specified api allows multiple addresses included in single api call
        """
        q = Queue()
        threads = []
        max_per_call = F.multi_request_max
        addr_lst_chunks = util.chunk_list(list(F.addresses), max_per_call)

        for nested_lst in addr_lst_chunks:
            addr_payload = util.merge_lst(nested_lst, ['', ','])
            threads.append(Thread(target=util.api_call, args=(F.api_base, addr_payload, q)))
            threads[-1].start()
        [t.join() for t in threads]
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

    def isempty(self):
        return len(self.addr_families) == 0

    def multi_asset_request(self, F):
        """
        for addresses that have multiple assets associated with each address e.g. Counterparty
        """
        q = Queue()
        threads = []
        for addr in F.addresses:
            threads.append(Thread(target=util.api_call, args=(F.api_base, addr, q)))
            threads[-1].start()
        [t.join() for t in threads]
        while not q.empty():
            addr, raw_resp = q.get()
            resp = util.json_value_by_key(raw_resp, F.data_key)
            for asset_data in resp:
                asset_name = util.json_value_by_key(asset_data, F.id_key)
                asset_balance = util.json_value_by_key(asset_data, F.balance_key) * F.multiplier
                self.update_balance(addr, asset_name, asset_balance)

    def standard_request(self, F):
        """
        for addresses that have a single asset and whose api has limit of one address per call
        """
        q = Queue()
        threads = []
        for addr in F.addresses:
            threads.append(Thread(target=util.api_call, args=(F.api_base, addr, q)))
            threads[-1].start()
        [t.join() for t in threads]
        while not q.empty():
            addr, raw_resp = q.get()
            resp = util.json_value_by_key(raw_resp, F.data_key)[0]
            asset_name = F()
            asset_balance = util.json_value_by_key(resp, F.balance_key) * F.multiplier
            self.update_balance(addr, asset_name, asset_balance)

    def update_balance(self, addr, asset_name, asset_balance):
        asset_balance = Decimal(asset_balance)
        if asset_name in self.addr_assets[addr]:
            self.addr_assets[addr][asset_name].balance += asset_balance
        else:
            self.addr_assets[addr][asset_name] = Asset(asset_balance)

    def print_address_balances(self, asset_prec_digits, value_prec_digits):
        """
        prints individual asset balances for each individual address
        """
        asset_prec = '1.{0}'.format('0'*asset_prec_digits)
        value_prec = '1.{0}'.format('0'*value_prec_digits)

        longest_width = 0
        fmt_addr_assets = {}
        for addr, asset_data in self.filtered_addr_assets.items():
            fmt_addr_assets[addr] = {}
            for asset_name, asset_obj in asset_data.items():
                asset_obj.balance = asset_obj.balance.quantize(Decimal(asset_prec))
                fmt_addr_assets[addr][asset_name] = asset_obj

                width = len('{0}{1}'.format(asset_name, str(asset_obj.balance)))
                if width > longest_width:
                    longest_width = width

        for addr, asset_data in fmt_addr_assets.items():
            if len(fmt_addr_assets[addr]) > 0:
                print(addr)
                for asset_name, asset_obj in asset_data.items():
                    line_width = len('{0}{1}'.format(asset_name, asset_obj.balance))
                    fill = '.' * (longest_width-line_width+5)
                    asset_value = Decimal(asset_obj.balance * self.asset_prices[asset_name]).quantize(Decimal(value_prec))

                    print('{0}{1}{2:.{asset_prec}f} = {3:.{val_prec}f}'.format(
                            asset_name, fill, asset_obj.balance, asset_value,
                            asset_prec=asset_prec_digits, val_prec=value_prec_digits))
                print()

    def print_total_balances(self, asset_prec_digits, value_prec_digits):
        """
        prints combined asset totals
        """
        asset_totals = self.get_asset_totals()
        longest_width = util.longest_kv_length(asset_totals)

        for asset, balance in asset_totals.items():
            line_width = len('{0}{1}'.format(asset, balance))
            fill = '.' * (longest_width-line_width+5)
            print('{0}{1}{2}'.format(asset, fill, balance))




