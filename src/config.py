import os

from src import util

dir_path = str(os.path.realpath(__file__)).rsplit('/', 1)[0]
addr_data_file = dir_path + '/addresses.json'
addr_config_file = dir_path + '/address_config.json'
excluded_assets_file = dir_path + '/exclusions.txt'

app_file_paths = [addr_data_file, addr_config_file, excluded_assets_file]

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

def add_address(addr_type, addr_lst=[]):
    """
    updates addresses from file to include new addresses of addr_type after verifying the address as valid
    """
    addr_type = addr_type.upper()
    type_data = util.json_from_file(addr_config_file)
    addr_data = util.json_from_file(addr_data_file)

    if addr_type in addr_data:
        [addr_data[addr_type].append(addr) for addr in addr_lst]

    else:
        # settings template for new address type
        type_data[addr_type] = {'API':'',
                                'DATA_KEY':[''],
                                'ID_KEY':[''],
                                'BALANCE_KEY':[''],
                                'MULTI_ASSET_FLAG':False,
                                'MULTI_REQUEST_FLAG_MAX':[False, 0],
                                'MULTIPLIER':1}
        addr_data[addr_type] = [addr for addr in addr_lst]
        util.json_to_file(addr_config_file, type_data)
        print('Update address type params for {0} addresses at\n{1}'.format(addr_type, addr_config_file))

    util.json_to_file(addr_data_file, addr_data)

def add_exclusion(asset_lst=[]):
    """
    Adds each asset in asset_lst to current exclusions
    """
    exlusion_lst = [i.upper() for i in util.list_from_file(excluded_assets_file)]
    for asset in asset_lst:
        asset = asset.upper()
        if asset not in exlusion_lst:
            exlusion_lst.append(asset)
    with open(excluded_assets_file, 'w') as f:
        [f.write(e + '\n') for e in exlusion_lst]

def display_addresses():
    """
    Prints all assets for each address
    """
    addr_data = util.json_from_file(addr_data_file)
    for addr_type, addr_lst in addr_data.items():
        print(addr_type)
        [print('   {0}'.format(addr)) for addr in addr_lst]

def display_exclusions():
    """
    Prints all excluded assets
    """
    exclusion_lst = util.list_from_file(excluded_assets_file)
    [print('   {0}'.format(e)) for e in exclusion_lst]

def remove_address(addr_type, addr_lst=[]):
    """
    updates addresses from file so addresses in rm_addr_lst are removed if they are present
    """
    addr_type = addr_type.upper()
    addr_data = util.json_from_file(addr_data_file)
    if addr_type not in addr_data:
        print('No addresses with type {0} found'.format(addr_type))
        return
    addr_data[addr_type] = [addr for addr in addr_data[addr_type] if addr not in addr_lst]
    util.json_to_file(addr_data_file, addr_data)

def remove_exclusion(asset_lst=[]):
    """
    Removes all assets in asset_lst from current exclusions list
    """
    asset_lst = [asset.upper() for asset in asset_lst]
    old_exclusion_lst = util.list_from_file(excluded_assets_file)
    new_exclusion_lst = list(set(old_exclusion_lst) - set(asset_lst))
    util.list_to_file(excluded_assets_file, new_exclusion_lst)
