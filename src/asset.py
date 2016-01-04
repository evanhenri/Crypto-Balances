from src import util
from queue import Queue
from threading import Thread
from decimal import Decimal

class Asset(object):
    def __init__(self, balance):
        self.balance = Decimal(balance)
        self.price = 0
        self.value = 0

class Prices(object):
    def __init__(self):
        self.cryptocurrency_ticker_symbols = {}
        self.cryptocurrency_ticker_names = {}
        self.fiat_ticker_symbols = {}

        q = Queue()
        threads = [Thread(target=util.api_call, args=('http://api.cryptocoincharts.info/', 'listCoins', q)),
                   Thread(target=util.api_call, args=('http://api.bitcoincharts.com/v1/', 'markets.json', q))]
        [t.start() for t in threads]
        [t.join() for t in threads]

        while not q.empty():
            url_path, ticker_data = q.get()
            if url_path == 'listCoins':
                for ticker in ticker_data:
                    btc_price = Decimal(ticker['price_btc'])
                    if btc_price > 0:
                        self.cryptocurrency_ticker_symbols[ticker['id'].upper()] = btc_price
                        self.cryptocurrency_ticker_names[ticker['name'].upper()] = btc_price
            elif url_path == 'markets.json':
                for ticker in ticker_data:
                    btc_price = ticker['bid']
                    if btc_price:
                        self.fiat_ticker_symbols[ticker['currency']] = Decimal(btc_price)

    def get(self, target_currency, base_currency):
        def currency_to_btc(currency):
            if currency in self.cryptocurrency_ticker_symbols:
                return self.cryptocurrency_ticker_symbols[currency]
            elif currency in self.fiat_ticker_symbols:
                return self.fiat_ticker_symbols[currency]
            elif currency in self.cryptocurrency_ticker_names:
                return self.cryptocurrency_ticker_names[currency]
            else:
                return Decimal(0)

        target, base = target_currency.upper(), base_currency.upper()
        target_price = currency_to_btc(target)
        base_price = currency_to_btc(base)

        if all([target_price, base_price]):
            if base != 'BTC':
                if base in self.cryptocurrency_ticker_symbols or base in self.cryptocurrency_ticker_names:
                    target_price /= base_price
                else:
                    target_price *= base_price
            return target_price
        return Decimal(0)

