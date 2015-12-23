# command line utility for totalling cryptocurrency balances

import argparse
import os
import json
import requests
import inspect

dir_path = str(os.path.realpath(__file__)).rsplit('/', 1)[0]
addr_file_path = dir_path + '/addresses.json'
info_file_path = dir_path + '/addr_info.json'

def verify_files(file_lst=[]):
    for file_path in file_lst:
        if not os.path.isfile(file_path) or os.stat(file_path).st_size == 0:
            with open(file_path, 'w') as f:
                f.write('{}')

def json_from_file(file_name):
    with open(file_name, 'r') as f:
        return json.load(f)

def json_to_file(file_path, content):
    with open(file_path, 'w') as f:
        payload = json.dumps(content, indent=4, sort_keys=True)
        f.seek(0)
        f.write(payload)

def add_new_addr(args=[]):
    """

    """
    addr_type = args[0].upper()
    addr_lst = args[1:]

    type_data = json_from_file(info_file_path)
    api_base = type_data[addr_type]['API']

    addr_data = json_from_file(addr_file_path)

    updated_addr_lst = []
    if addr_type in addr_data:
        updated_addr_lst = addr_data[addr_type]

    for addr in addr_lst:
        if addr in updated_addr_lst:
            # do not re-add existing existing addresses, begin next loop iteration
            continue
        try:
            url = api_base + addr
            resp = requests.get(url)
            # check if api call using address is valid
            if resp.status_code == 200:
                updated_addr_lst.append(addr)
            else:
                print('Invalid address {0}'.format(addr))
        except Exception as e:
            print('Error occurred while checking {0}'.format(addr), e.args)
            pass

    addr_data[addr_type] = updated_addr_lst
    json_to_file(addr_file_path, addr_data)

def rev_eval(var):
    """
    Returns variable name of var as string
    """
    callers_local_vars = inspect.currentframe().f_back.f_locals.items()
    return [k for k,v in callers_local_vars if v is var][0]

def merge_lst(lst, delimeters=['', '']):
    """
    Returns a string comprised of element in lst, optionally surrounded by delimiters
    """
    lst_str = ''
    for element in lst:
        lst_str += delimeters[0] + element + delimeters[1]
    return lst_str

def json_value_by_key(json_obj, key=[]):
    """
    Returns value at json_obj[key] where key is a list of sub keys, i.e. json_obj['a']['b']['c']
    """
    json_key_path = merge_lst(key, ['[\'', '\']'])
    str_stmt = rev_eval(json_obj) + json_key_path
    return eval(str_stmt)

def same_char_str(str_obj, exclusions=[]):
    """
    Returns true if element is all the same character, ignoring characters in exclusions
    """
    str_obj = str(str_obj)
    for c in str_obj:
        if c != str_obj[0] and c not in exclusions:
            return False
    return True

def min_args(nmin):
    class RequiredLength(argparse.Action):
        def __call__(self, parser, args, values, option_string=None):
            if not nmin <= len(values):
                msg ='argument \'{0}\' requires at least {1} arguments'.format(self.dest, nmin)
                raise argparse.ArgumentTypeError(msg)
            setattr(args, self.dest, values)
    return RequiredLength

def update_balances(total_balances, token_name, token_balance):
    if token_name in total_balances:
        total_balances[token_name] += float(token_balance)
    else:
        total_balances[token_name] = float(token_balance)
    return total_balances

def longest_kv_pair(dict_obj):
    longest = None
    for k, v in dict_obj.items():
        kv_len = len(str(k)) + len(str(v))
        if not longest or kv_len > longest:
            longest = kv_len
    return longest

def len_before_char(str_obj, char_obj):
    str_obj, char_obj = str(str_obj), str(char_obj)
    substr_before_char = str_obj.split(char_obj, 1)[0]
    return len(substr_before_char)

def print_balances(total_balances):
    # expand each balance entry to show 8 digits after decimal and include thousands separators
    for asset_name, balance in total_balances.items():
        total_balances[asset_name] = '{0:,.8f}'.format(balance)

    width = longest_kv_pair(total_balances)

    for asset_name, balance in total_balances.items():
        # ignore zero balance entries
        if not same_char_str(balance, ['.']):
            line_len = len(asset_name) + len_before_char(balance, '.') + 8
            fill_len = width - line_len + 5
            print('{key}{fill}{value}'.format(key=asset_name, fill=' '*fill_len, value=balance))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--add', nargs='+', action=min_args(2),
                        help='Add addresses for the given address type, e.x. -a btc <address1> <address2>')
    args = parser.parse_args()

    verify_files([addr_file_path, info_file_path])

    if args.add:
        add_new_addr(args.add)

    addr_data = json_from_file(addr_file_path)

    total_balances = {}

    type_data = json_from_file(info_file_path)
    for addr_type, addr_lst in addr_data.items():
        api_base_url = type_data[addr_type]['API']
        data_key = type_data[addr_type]['DATA_KEY']

        if type_data[addr_type]['MULTI_ASSET']:
            for addr in addr_lst:
                url = api_base_url + addr
                r = requests.get(url).text
                resp = json.loads(r)
                asset_name_key = type_data[addr_type]['ASSET_NAME_KEY']
                balance_key = type_data[addr_type]['BALANCE_KEY']
                asset_lst = json_value_by_key(resp, data_key)
                for asset_dict in asset_lst:
                    asset_name = json_value_by_key(asset_dict, asset_name_key)
                    balance = json_value_by_key(asset_dict, balance_key)
                    total_balances = update_balances(total_balances, asset_name, balance)
        else:
            url = api_base_url + merge_lst(addr_lst, ['', ','])
            r = requests.get(url).text
            resp = json.loads(r)

            balance_key = type_data[addr_type]['BALANCE_KEY']
            balance = sum(json_value_by_key(r, balance_key) for r in json_value_by_key(resp, data_key))
            total_balances = update_balances(total_balances, addr_type, balance)

    if len(total_balances) == 0:
        print('No addresses have been added')
    else:
        print_balances(total_balances)
if __name__ == '__main__':
    main()