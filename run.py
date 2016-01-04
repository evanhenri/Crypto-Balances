import argparse

from src import config, util, portfolio

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

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--add', nargs='+', action=min_args(2), help='Add addresses for the given type')
    parser.add_argument('-r', '--remove', nargs='+', action=min_args(2), help='Remove addresses for the given type')
    parser.add_argument('-i', '--itemized', action='store_true', help='Print itemized address balances instead of totals')
    parser.add_argument('-e', '--exclude', nargs='+', help='Exclude the listed assets from inclusion in final balances')
    parser.add_argument('-b', '--base', nargs=1, default=['btc'], help='Base currency for asset values')
    parser.add_argument('-m', '--minimum', nargs=1, default=[0], help='Minimum balance for displayed asset balances')
    parser.add_argument('-p', '--precision', nargs=2, default=[8, 8], help='Asset quantity and asset value precision')
    args = parser.parse_args()

    if args.add:
        config.add_addr(args.add[0], args.add[1:])
    if args.remove:
        config.remove_addr(args.remove[0], args.remove[1:])
    if args.exclude:
        config.add_exclusion(args.exclude)

    base_currency = args.base[0]
    min_balance = int(args.minimum[0])
    asset_precision = int(args.precision[0])
    value_precision = int(args.precision[1])

    address_dict = util.json_from_file(config.address_file)
    address_config = util.json_from_file(config.address_config_file)
    exclusion_lst = util.list_from_file(config.exclusions_file)

    P = portfolio.Portfolio(address_dict, address_config, exclusion_lst)
    P.filter_addr_assets(min_balance)
    P.retrieve_asset_prices(base_currency)

    if P.isempty():
        print('No addresses have been added')
    elif args.itemized:
        P.print_address_balances(asset_precision, value_precision)
    else:
        P.print_total_balances(asset_precision, value_precision)

if __name__ == '__main__':
    main()

"""

KNOWN BUGS

TO DO

change config file so that absolute paths to json values can be used
option to remove an exclusion

"""