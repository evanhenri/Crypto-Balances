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
    parser.add_argument('-i', '--individual', action='store_true', help='Print individual address balances instead of totals')
    parser.add_argument('-e', '--exclude', nargs='+', help='Exclude the listed assets from inclusion in final balances')
    parser.add_argument('-b', '--base', nargs=1, default=['btc'], help='Base currency for asset values')
    parser.add_argument('-m', '--minimum', nargs=1, default=[0], help='Minimum balance for displayed asset balances')
    parser.add_argument('-p', '--precision', nargs=1, default=[8], help='Number of digits beyond decimal point to be shown')
    args = parser.parse_args()

    if args.add:
        config.add_new_addr(args.add[0], args.add[1:])
    if args.remove:
        config.remove_old_addr(args.remove[0], args.remove[1:])
    if args.exclude:
        config.add_to_exlusion_lst(args.exclude)
    base_currency = args.base_currency[0]
    min_balance = args.minimum[0]
    precision = args.precision[0]

    address_dict = util.json_from_file(config.address_file)
    address_config = util.json_from_file(config.address_config_file)
    exclusion_lst = util.list_from_file(config.exclusions_file)

    P = portfolio.Portfolio(address_dict, address_config, exclusion_lst)
    P.filter_addr_assets(min_balance)

    if P.isempty():
        print('No addresses have been added')
    elif args.individual:
        P.print_address_balances()
    else:
        P.print_total_balances()

if __name__ == '__main__':
    main()

"""

KNOWN BUGS

TO DO
add functionality to get exchange value for each asset with option to denominate that value in the currency specified
by the user

change config file so that absolute paths to json values can be used

"""