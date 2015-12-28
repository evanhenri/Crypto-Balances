import argparse
import os
import json
import requests
import inspect
from queue import Queue
from threading import Thread

dir_path = str(os.path.realpath(__file__)).rsplit('/', 1)[0]
addr_file_path = dir_path + '/addresses.json'
info_file_path = dir_path + '/addr_info.json'
exclusion_file_path = dir_path + '/exclusions.txt'

def merge_lst(lst, delimeters=['', '']):
    """
    Returns a string comprised of element in lst, optionally surrounded by delimiters
    """
    lst_str = ''
    for element in lst:
        lst_str += delimeters[0] + element + delimeters[1]
    return lst_str

def rev_eval(var):
    """
    Returns variable name of var as string
    """
    callers_local_vars = inspect.currentframe().f_back.f_locals.items()
    return [k for k,v in callers_local_vars if v is var][0]

def same_char_str(str_obj, char_obj=None, exclusion_lst=[]):
    """
    Returns true if str_obj is comprised of the same character, ignoring characters in exclusions
    If optional char_obj is specified, it is used for comparison rather than the default, first character in str_obj
    """
    str_obj = str(str_obj)
    if char_obj:
        char_obj = str(char_obj)
    else:
        char_obj = str_obj[0]
    for c in str_obj:
        if c != char_obj and c not in exclusion_lst:
            return False
    return True

def json_from_file(file_path):
    """
    returns contents of file at file_path as json
    """
    with open(file_path, 'r') as f:
        return json.load(f)

def list_from_file(file_path):
    """
    returns a list where each element is the content of a single line in file at file_path
    """
    lst = []
    with open(file_path, 'r') as f:
        for line in f:
            stripped_line = line.strip('\r\n')
            if len(stripped_line) > 0:
                lst.append(stripped_line)
    return lst

def json_to_file(file_path, content):
    """
    writes the contents of file at file_path with content
    """
    with open(file_path, 'w') as f:
        payload = json.dumps(content, indent=4, sort_keys=True)
        f.seek(0)
        f.write(payload)

def json_value_by_key(json_obj, key_lst=[]):
    """
    Returns value at json_obj[key] where key is a list of sub keys, i.e. json_obj['a']['b']['c']
    """
    json_key_path = merge_lst(key_lst, ['[\'', '\']'])
    str_stmt = rev_eval(json_obj) + json_key_path
    return eval(str_stmt)

def verify_files(file_type_dict={}):
    """
    checks if a file exists at path specified by file_lst index, creates file and writes '{}' to it if not exists
    """
    for file_type, path_lst in file_type_dict.items():
        for file_path in path_lst:
            if not os.path.isfile(file_path) or os.stat(file_path).st_size == 0:
                with open(file_path, 'w') as f:
                    if file_type == 'json':
                        # write empty dict to files designated as json if they must be created
                        f.write('{}')
                    else:
                        pass

def api_data_request(api_base, addr, results_queue):
    """
    puts json response from api request to api_base + addr into results queue
    """
    url = api_base + addr
    try:
        resp = requests.get(url).text
        results_queue.put([addr, json.loads(resp)])
    except Exception as e:
        print('Error occurred while requesting {0}'.format(url), e.args)

def api_verify_request(api_base, address, results_queue):
    """
    puts address into results_queue if valid response received from request to api_base + address
    """
    url = api_base + address
    try:
        resp = requests.get(url)
        if resp.status_code == 200:
            results_queue.put(address)
    except Exception as e:
        print('Error occurred while requesting {0}'.format(url), e.args)

def add_new_addr(addr_type, new_addr_lst):
    """
    updates addresses from file to include new addresses of addr_type after verifying the address as valid
    """
    addr_type = addr_type.upper()
    type_data = json_from_file(info_file_path)
    addr_data = json_from_file(addr_file_path)
    api_base = type_data[addr_type]['API']

    addr_lst = []
    if addr_type in addr_data:
        addr_lst = addr_data[addr_type]

    q = Queue()
    threads = []
    for addr in new_addr_lst:
        if addr not in addr_lst:
            threads.append(Thread(target=api_verify_request, args=(api_base, addr, q)))
            threads[-1].start()
    [t.join() for t in threads]
    while not q.empty():
        addr_lst.append(q.get())

    addr_data[addr_type] = addr_lst
    json_to_file(addr_file_path, addr_data)

def remove_old_addr(addr_type, rm_addr_lst):
    """
    updates addresses from file so addresses in rm_addr_lst are removed if they are present
    """
    addr_type = addr_type.upper()
    addr_data = json_from_file(addr_file_path)
    if addr_type not in addr_data:
        print('No addresses with type {0} found'.format(addr_type))
        return
    addr_lst = list(filter(lambda x: x not in rm_addr_lst, addr_data[addr_type]))
    addr_data[addr_type] = addr_lst
    json_to_file(addr_file_path, addr_data)

def add_to_exlusion_lst(asset_lst):
    exlusion_lst = [i.upper() for i in list_from_file(exclusion_file_path)]
    for asset in asset_lst:
        asset = asset.upper()
        if asset not in exlusion_lst:
            exlusion_lst.append(asset)
    with open(exclusion_file_path, 'w') as f:
        [f.write(e + '\n') for e in exlusion_lst]

def update_final_balances(address, address_type, balance, final_balances={}):
    if address in final_balances:
        # include the type of the address and its balance in the existing address value list
        final_balances[address].append({address_type:balance})
    else:
        # create new list to associate with address where the type and balance is the first entry
        final_balances[address] = [{address_type:balance}]

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
                if not same_char_str(balance, '0', ['.',',']):
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
        if not same_char_str(balance, '0', ['.',',']):
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
    args = parser.parse_args()

    verify_files({'json':[addr_file_path, info_file_path],
                  'txt':[exclusion_file_path]})

    if args.add:
        add_new_addr(args.add[0], args.add[1:])
    if args.remove:
        remove_old_addr(args.remove[0], args.remove[1:])
    if args.exclude:
        add_to_exlusion_lst(args.exclude)

    final_balances = {}

    address_data = json_from_file(addr_file_path)
    type_data = json_from_file(info_file_path)
    exclusion_lst = [i.upper() for i in list_from_file(exclusion_file_path)]

    for addr_type, addr_lst in address_data.items():
        api_base = type_data[addr_type]['API']
        resp_data_key = type_data[addr_type]['DATA_KEY']
        id_key = type_data[addr_type]['ID_KEY']
        balance_key = type_data[addr_type]['BALANCE_KEY']
        multi_asset_flag = type_data[addr_type]['MULTI_ASSET_FLAG']
        multi_req_flag, multi_req_max = type_data[addr_type]['MULTI_REQUEST_FLAG_MAX']
        multiplier = type_data[addr_type]['MULTIPLIER']

        q = Queue()

        if addr_type.upper() not in exclusion_lst:
            if multi_req_flag:
                # split addresses into maximum amount allowed per api request
                addr_chunks = [addr_lst[x:x+multi_req_max] for x in range(0, len(addr_lst), multi_req_max)]
                threads = []
                for chunk in addr_chunks:
                    addrs = merge_lst(chunk, ['', ','])
                    threads.append(Thread(target=api_data_request, args=(api_base, addrs, q)))
                    threads[-1].start()
                [t.join() for t in threads]

                while not q.empty():
                    # need to get address from within json reponse to differentiate the balance data,
                    # ignore address in position 0 of [address, response] that is returned from q.get()
                    raw_resp = q.get()[1]
                    response = json_value_by_key(raw_resp, resp_data_key)
                    for addr_data in response:
                        address = json_value_by_key(addr_data, id_key)
                        # blockr api sometime sends more responses than were requested as {'':0}, filter them out
                        if address != '':
                            balance = json_value_by_key(addr_data, balance_key) * multiplier
                            update_final_balances(address, addr_type, balance, final_balances)

            elif multi_asset_flag:
                threads = []
                for addr in addr_lst:
                    threads.append(Thread(target=api_data_request, args=(api_base, addr, q)))
                    threads[-1].start()
                [t.join() for t in threads]

                while not q.empty():
                    address, raw_resp = q.get()
                    response = json_value_by_key(raw_resp, resp_data_key)

                    for asset_data in response:
                        asset_type = json_value_by_key(asset_data, id_key)
                        if asset_type.upper() not in exclusion_lst:
                            balance = json_value_by_key(asset_data, balance_key) * multiplier
                            update_final_balances(address, asset_type, balance, final_balances)
            else:
                threads = []
                for addr in addr_lst:
                    threads.append(Thread(target=api_data_request, args=(api_base, addr, q)))
                    threads[-1].start()
                [t.join() for t in threads]

                while not q.empty():
                    address, raw_resp = q.get()
                    response = json_value_by_key(raw_resp, resp_data_key)[0]
                    balance = json_value_by_key(response, balance_key) * multiplier
                    update_final_balances(address, addr_type, balance, final_balances)

    if len(final_balances) == 0:
        print('No addresses have been added')
    elif args.individual:
        print_address_balances(final_balances)
    else:
        print_total_balances(final_balances)

if __name__ == '__main__':
    main()

"""
todo

add option to ignore certain assets from inclusion in totals
"""