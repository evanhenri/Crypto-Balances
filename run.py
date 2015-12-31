import argparse

from src.address import Address, Family
from src import config
from src import portfolio
from src import util

def min_args(nmin):
    """
    verifies that a minimum of nmin arguements have been entered if cooresponding argument flag has been entered
    """
    class RequiredLength(argparse.Action):
        def __call__(self, parser, args, values, option_string=None):
            if not nmin <= len(values):
                msg ='argument \'{0}\' requires at least {1} arguments'.format(self.dest, nmin)
                raise argparse.ArgumentTypeError(msg)
            setattr(args, self.dest, values)
    return RequiredLength

def print_address_balances(address_balances):
    """
    prints formatted asset balances for each address
    """
    line_width = None
    # find length of longest {asset:formatted balance} pair
    for addr, asset_lst in address_balances.items():
        for asset_balance_pair in asset_lst:
            for asset, balance in asset_balance_pair.items():
                asset_balance_pair[asset] = '{0:,.8f}'.format(float(balance))
                line_len = len(asset) + len(str(balance))
                if not line_width or line_len > line_width:
                    line_width = line_len

    # print formatted asset balances for each address
    for addr, asset_lst in address_balances.items():
        print(addr)
        for asset_balance_pair in asset_lst:
            for asset, balance in sorted(asset_balance_pair.items()):
                if not util.same_char_str(balance, '0', ['.', ',']):
                    line_len = len(asset) + len(str(balance))
                    fill = line_width - line_len + 15
                    print('{0}{1}{2}{3}'.format(' '*3, asset, '.'*fill, balance))
        print()

def print_total_balances(address_balances):
    """
    sums total for each asset type and prints formatted totals
    """
    total_balances = {}
    line_width = None
    # find length of longest {address:formatted balance} pair
    # and accumulate asset balances into total_balances
    for addr, asset_lst in address_balances.items():
        for asset_balance_pair in asset_lst:
            for asset, balance in asset_balance_pair.items():
                asset_balance_pair[asset] = '{0:,.8f}'.format(float(balance))
                line_len = len(asset) + len(str(balance))
                if not line_width or line_len > line_width:
                    line_width = line_len
                if asset in total_balances:
                    total_balances[asset] += float(balance)
                else:
                    total_balances[asset] = float(balance)

    # print formatted asset balance totals
    for asset, balance in sorted(total_balances.items()):
        if not util.same_char_str(balance, '0', ['.', ',']):
            balance = '{0:,.8f}'.format(balance)
            line_len = len(asset) + len(str(balance))
            fill = line_width - line_len + 15
            print('{0}{1}{2}'.format(asset,'.'*fill,balance))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--add', nargs='+', action=min_args(2), help='Add addresses for the given type')
    parser.add_argument('-r', '--remove', nargs='+', action=min_args(2), help='Remove addresses for the given type')
    parser.add_argument('-i', '--individual', action='store_true', help='Print individual address balances instead of totals')
    parser.add_argument('-e', '--exclude', nargs='+', help='Exclude the listed assets from inclusion in final balances')
    parser.add_argument('-d', '--denomination', nargs=1, default=['btc'], help='Set denomination for balances')
    args = parser.parse_args()

    if args.add:
        config.add_new_addr(args.add[0], args.add[1:])
    if args.remove:
        config.remove_old_addr(args.remove[0], args.remove[1:])
    if args.exclude:
        config.add_to_exlusion_lst(args.exclude)
    balance_value_denomination = args.denomination[0]

    P = portfolio.Portfolio()
    P.get_balances()

    if len(P.addresses) == 0:
        print('No addresses have been added')
    elif args.individual:
        P.print_address_balances()
    else:
        P.print_total_balances()

if __name__ == '__main__':
    main()

"""

KNOWN BUGS
Sometimes only balances for multiasset addresses are retrieved and other times only
multi request addresses are retrieved, but never both as should be happening
- appears to be caused by multithreaded requests to api's for asset info

TO DO
necessary to have address variable for Address objects if that is the key for each Address in portfolio.addresses ?

add functionality to get exchange value for each asset with option to denominate that value in the currency specified
by the user

"""