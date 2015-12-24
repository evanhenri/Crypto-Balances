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

def verify_files(file_lst=[]):
    """
    checks if a file exists at path specified by file_lst index, creates file and writes '{}' to it if not exists
    """
    for file_path in file_lst:
        if not os.path.isfile(file_path) or os.stat(file_path).st_size == 0:
            with open(file_path, 'w') as f:
                f.write('{}')

def api_data_request(api_base, addr, results_queue):
    """
    puts json response from api request to api_base + addr into results queue
    """
    url = api_base + addr
    try:
        resp = requests.get(url).text
        results_queue.put(json.loads(resp))
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
    width = None
    for addr, asset_lst in address_balances.items():
        for asset_info in asset_lst:
            for asset, balance in asset_info.items():
                asset_info[asset] = '{0:,.8f}'.format(float(balance))
                line_len = len(asset) + len(str(balance))
                if not width or line_len > width:
                    width = line_len

    for addr, asset_lst in address_balances.items():
        print(addr)
        for asset_info in asset_lst:
            for asset, balance in sorted(asset_info.items()):
                if not same_char_str(balance, '0', ['.',',']):
                    line_len = len(asset) + len(str(balance))
                    fill = width - line_len + 15
                    print('{indent}{asset_name}{fill}{balance}'.format(
                            indent=' '*3, asset_name=asset, fill='.'*fill, balance=balance))
        print()

def print_total_balances(address_balances):
    """
    sums total for each asset type and prints formatted totals
    """
    total_balances = {}
    width = None
    for addr, asset_lst in address_balances.items():
        for asset_info in asset_lst:
            for asset, balance in asset_info.items():
                asset_info[asset] = '{0:,.8f}'.format(float(balance))
                line_len = len(asset) + len(str(balance))
                if not width or line_len > width:
                    width = line_len
                if asset in total_balances:
                    total_balances[asset] += float(balance)
                else:
                    total_balances[asset] = float(balance)

    for asset, balance in sorted(total_balances.items()):
        if not same_char_str(balance, '0', ['.',',']):
            balance = '{0:,.8f}'.format(balance)
            line_len = len(asset) + len(str(balance))
            fill = width - line_len + 15
            print('{asset_name}{fill}{balance}'.format(asset_name=asset, fill='.'*fill, balance=balance))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--add', nargs='+', action=min_args(2), help='Add addresses for the given type')
    parser.add_argument('-r', '--remove', nargs='+', action=min_args(2), help='Remove addresses for the given type')
    parser.add_argument('-i', '--individual', action='store_true', help='Print individual address balances instead of totals')
    args = parser.parse_args()

    verify_files([addr_file_path, info_file_path])

    if args.add:
        add_new_addr(args.add[0], args.add[1:])
    if args.remove:
        remove_old_addr(args.remove[0], args.remove[1:])

    address_balances = {}

    addr_file_data = json_from_file(addr_file_path)
    type_data = json_from_file(info_file_path)
    for addr_type, addr_lst in addr_file_data.items():
        api_base = type_data[addr_type]['API']
        resp_data_key = type_data[addr_type]['DATA_KEY']
        id_key = type_data[addr_type]['IDENTIFIED_KEY']
        balance_key = type_data[addr_type]['BALANCE_KEY']
        multi_asset_flag = type_data[addr_type]['MULTI_ASSET']
        multi_req_flag, multi_req_max = type_data[addr_type]['MULTI_REQUEST']

        q = Queue()
        # if data for multiple addresses can be retrieved in single api request
        if multi_req_flag:
            multi_addr_resp = []
            # split addresses into maximum amount allowed per api request
            addr_chunks = [addr_lst[x:x+multi_req_max] for x in range(0, len(addr_lst), multi_req_max)]
            threads = []
            for max_api_chunk in addr_chunks:
                addrs = merge_lst(max_api_chunk, ['', ','])
                threads.append(Thread(target=api_data_request, args=(api_base, addrs, q)))
                threads[-1].start()
            [t.join() for t in threads]
            while not q.empty():
                resp = q.get()
                # accumulate addr chunk api responses into multi_addr_resp
                multi_addr_resp += json_value_by_key(resp, resp_data_key)
            for addr_resp in multi_addr_resp:
                addr = json_value_by_key(addr_resp, id_key)
                balance = json_value_by_key(addr_resp, balance_key)

                # blockr api sometime sends more addresses in response than were requested
                # these extra responses have an empty address field, filter them out
                if addr != '':
                    if addr in address_balances:
                        address_balances[addr].append({addr_type:balance})
                    else:
                        address_balances[addr] = [{addr_type:balance}]

        # if multi assets are associated with the given address
        elif multi_asset_flag:
            threads = []
            for addr in addr_lst:
                threads.append(Thread(target=api_data_request, args=(api_base, addr, q)))
                threads[-1].start()
            [t.join() for t in threads]
            while not q.empty():
                resp = q.get()
                multi_asset_resp = json_value_by_key(resp, resp_data_key)
                for asset_resp in multi_asset_resp:
                    asset_name = json_value_by_key(asset_resp, id_key)
                    balance = json_value_by_key(asset_resp, balance_key)
                    if addr in address_balances:
                        address_balances[addr].append({asset_name:balance})
                    else:
                        address_balances[addr] = [{asset_name:balance}]

    if len(address_balances) == 0:
        print('No addresses have been added')
    elif args.individual:
        print_address_balances(address_balances)
    else:
        print_total_balances(address_balances)
if __name__ == '__main__':
    main()