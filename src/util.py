import inspect
import json
import requests
from queue import Queue

__all__ = ['api_call', 'api_test_call', 'json_from_file', 'json_to_file', 'json_value_by_key',
           'list_from_file', 'make_list_chunks', 'merge_lst', 'rev_eval', 'same_char_str']

def api_call(api_base, api_path, results_queue=None):
    """
    If results_queue provided, json response from api call to api_base + api_path put into results_queue
    otherwise the json response is returned
    """
    url = api_base + api_path
    try:
        resp = requests.get(url).text
        if results_queue and isinstance(results_queue, Queue):
            results_queue.put([api_path, json.loads(resp)])
        else:
            return json.loads(resp)
    except Exception as e:
        print('Error occurred while requesting {0}'.format(url), e.args)

def chunk_list(lst, chunk_size):
    """
    Returns a list of sub lists where each sublist is at most chunk_size in length
    """
    return [lst[x : x+chunk_size] for x in range(0, len(lst), chunk_size)]

def json_from_file(file_path):
    """
    Returns contents of file at file_path as json
    """
    with open(file_path, 'r') as f:
        return json.load(f)

def json_to_file(file_path, content):
    """
    Writes the contents of file at file_path with content
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

def list_from_file(file_path):
    """
    Returns a list where each element is the content of a single line in file at file_path
    """
    lst = []
    with open(file_path, 'r') as f:
        for line in f:
            stripped_line = line.strip('\r\n')
            if len(stripped_line) > 0:
                lst.append(stripped_line)
    return lst

def list_to_file(file_path, lst=[]):
    """
    Writes the contents of lst to file_path where each lst element is writen to its own line
    """
    with open(file_path, 'w') as f:
        [f.write('{0}\n'.format(i)) for i in lst]

def longest_kv_length(dictionary):
    """
    Returns the length of the longest string representation of each {key:value} pair in dictionary
    """
    longest_len = 0
    for k,v in dictionary.items():
        kv_length = len('{0}{1}'.format(k,v))
        if kv_length > longest_len:
            longest_len = kv_length
    return longest_len

def merge_lst(lst, delimeters=['', '']):
    """
    Returns a string comprised of element in lst, optionally surrounded by delimiters
    """
    lst_str = ''
    for element in lst:
        lst_str += delimeters[0] + element + delimeters[1]
    return lst_str

def rev_eval(variable):
    """
    Returns string representation of variable name
    """
    callers_local_vars = inspect.currentframe().f_back.f_locals.items()
    return [k for k,v in callers_local_vars if v is variable][0]

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