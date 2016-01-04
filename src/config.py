import os
from queue import Queue
from threading import Thread

from src import util

dir_path = str(os.path.realpath(__file__)).rsplit('/', 1)[0]
address_file = dir_path + '/addresses.json'
address_config_file = dir_path + '/address_config.json'
exclusions_file = dir_path + '/exclusions.txt'

app_file_paths = [address_file, address_config_file, exclusions_file]

for file_path in app_file_paths:
    file_name, file_extension = os.path.splitext(file_path)
    if not os.path.isfile(file_path) or os.stat(file_path).st_size == 0:
        with open(file_path, 'w') as f:
            if file_extension == '.json':
                # write empty dict to files designated as json if they must be created
                f.write('{}')
            else:
                pass
    #print('{0} ok'.format(file_path))

def add_addr(addr_type, new_addr_lst):
    """
    updates addresses from file to include new addresses of addr_type after verifying the address as valid
    """
    addr_type = addr_type.upper()
    type_data = util.json_from_file(address_config_file)
    addr_data = util.json_from_file(address_file)
    api_base = type_data[addr_type]['API']

    addr_lst = []
    if addr_type in addr_data:
        addr_lst = addr_data[addr_type]

    q = Queue()
    threads = []
    for addr in new_addr_lst:
        if addr not in addr_lst:
            threads.append(Thread(target=util.api_call, args=(api_base, addr, q)))
            threads[-1].start()
    [t.join() for t in threads]
    while not q.empty():
        addr_lst.append(q.get())

    addr_data[addr_type] = addr_lst
    util.json_to_file(address_file, addr_data)

def add_exclusion(asset_lst):
    exlusion_lst = [i.upper() for i in util.list_from_file(exclusions_file)]
    for asset in asset_lst:
        asset = asset.upper()
        if asset not in exlusion_lst:
            exlusion_lst.append(asset)
    with open(exclusions_file, 'w') as f:
        [f.write(e + '\n') for e in exlusion_lst]

def remove_addr(addr_type, rm_addr_lst):
    """
    updates addresses from file so addresses in rm_addr_lst are removed if they are present
    """
    addr_type = addr_type.upper()
    addr_data = util.json_from_file(address_file)
    if addr_type not in addr_data:
        print('No addresses with type {0} found'.format(addr_type))
        return
    addr_lst = list(filter(lambda x: x not in rm_addr_lst, addr_data[addr_type]))
    addr_data[addr_type] = addr_lst
    util.json_to_file(address_file, addr_data)