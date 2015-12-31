from src import config
from src import util

class Family(object):
    def __init__(self, family):
        conf = util.json_from_file(config.address_config_file)
        self.family = family.upper()

        self.data_key = conf[self.family]['DATA_KEY']
        self.balance_key = conf[self.family]['BALANCE_KEY']
        self.api_base = conf[self.family]['API']
        self.id_key = conf[self.family]['ID_KEY']
        self.multi_asset_flag = conf[self.family]['MULTI_ASSET_FLAG']
        self.multi_request_flag = conf[self.family]['MULTI_REQUEST_FLAG_MAX'][0]
        self.multi_request_max = conf[self.family]['MULTI_REQUEST_FLAG_MAX'][1]
        self.multiplier = conf[self.family]['MULTIPLIER']
        self.single_asset_single_request = not any([self.multi_asset_flag, self.multi_request_flag])
    def __call__(self, *args, **kwargs):
        return self.family


class Address(object):
    def __init__(self, address, family_obj):
        self.family = family_obj
        self.address = address
        self.asset_balances = {} # {'name':balance}
    def __call__(self, *args, **kwargs):
        return self.address