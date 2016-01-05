"""Crypto-Balances

Usage:
  run.py [(address [(--add|--remove) <address_type> <address>...])]
         [(exclusion [(--add|--remove) <asset>...])]
         [base <currency> [--precision <n>]]
         [-m --minimum <balance>]
         [-i --itemize]

Options:
  -h --help              Show this screen
  -v --version           Show version
  -a --add
  -r --remove
  -i --itemize           Show asset balance for individual addresses
  -b --base <currency>   Asset value base denomination
  -p --precision <n>     Base currency decimal places
  -m --minimum <balance> Threshold asset balance for print
"""
from docopt import docopt
from src import config, util, portfolio

def main(argv):
    config_manip = [argv['--add'], argv['--remove']]
    if argv['address']:
        if argv['--add']:
            config.add_address(argv['<address_type>'], argv['<address>'])
        if argv['--remove']:
            config.remove_address(argv['<address_type>'], argv['<address>'])
        if not any(config_manip):
            config.display_addresses()
    if argv['exclusion']:
        if argv['--add']:
            config.add_exclusion(argv['<asset>'])
        if argv['--remove']:
            config.remove_exclusion(argv['<asset>'])
        if not any(config_manip):
            config.display_exclusions()

    base_currency = argv['<currency>'] or 'BTC'
    base_precision = argv['--precision'] or 8
    min_balance = argv['--minimum'] or 0

    addr_data = util.json_from_file(config.addr_data_file)
    addr_config = util.json_from_file(config.addr_config_file)
    excluded_assets = util.list_from_file(config.excluded_assets_file)

    P = portfolio.Portfolio(addr_data, addr_config, excluded_assets)
    P.filter_addr_assets(min_balance)
    P.retrieve_asset_prices(base_currency)

    if P.isempty():
        print('No addresses have been added')
    elif argv['--itemize']:
        P.print_address_balances(8, base_precision)
    else:
        P.print_total_balances(8, base_precision)

if __name__ == '__main__':
    args = docopt(__doc__, version='Crypto-Balances 1.0')
    main(args)

# """
#
# KNOWN BUGS
# add/remove addr not working correctly
#
# TO DO
#
# update README
# change config file so that absolute paths to json values can be used
#
# """