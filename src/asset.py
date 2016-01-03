from src import util

class Asset(object):
    def __init__(self, balance):
        self.balance = balance
        self.price = 0
        self.value = 0

class Price(object):
    def __init__(self, api_base, ticker_method):
        self.api_base = api_base
        self.raw_ticker_data = util.api_call(api_base, ticker_method)
        self.ticker_data_by_symbol = {}
        self.ticker_data_by_name = {}
        for currency in self.raw_ticker_data:
            ticker_symbol = currency['id'].strip().upper()
            ticker_name = currency['name'].strip().upper()
            self.ticker_data_by_symbol[ticker_symbol] = float(currency['price_btc'])
            self.ticker_data_by_name[ticker_name] = float(currency['price_btc'])

    def get_price(self, target_currency, base_currency):
        print(target_currency)
        target = target_currency.upper()
        base = base_currency.upper()
        if base == 'BTC':
            try:
                return self.ticker_data_by_symbol[target]
            except KeyError:
                try:
                    return self.ticker_data_by_name[target]
                except KeyError:
                    for name, price in self.ticker_data_by_name.items():
                        if target in name:
                            return price
            return 0

