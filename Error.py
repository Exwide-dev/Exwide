from time import sleep, strftime, localtime

LOG = 0
def clog(msg):
    timenow = strftime('%H:%M:%S', localtime())
    if LOG:
        sleep(.05)
        print(f'[DEBUG OUTPUT {timenow}] {msg}\n', flush = True)
    write_file('debug.log', f'[DEBUG OUTPUT {timenow}] {msg}\n')

def write_file(filename, content):
    with open(filename, 'a', encoding='UTF-8') as f:
        f.write(content)

class EW_ERROR(Exception):
    pass

class EW_SYNTAX_ERROR(EW_ERROR):
    pass

class EW_TYPE_ERROR(EW_ERROR):
    pass

class EW_RUNTIME_ERROR(EW_ERROR):
    pass

def raise_err(err, msg):
    print(f'\033[31m{err.__name__}: {msg}\033[0m')
    raise Exception

def ld_show(data, indent=0, is_last=True, is_root=True):
    """
    以换行缩进的方式将列表字典嵌套结构转换为字符串
    
    Args:
        data: 要转换的数据（列表、字典或其他类型）
        indent: 当前缩进级别
        is_last: 当前元素是否是父容器中的最后一个元素
        is_root: 是否是根元素
    """
    INDENT_SIZE = 2
    current_indent = ' ' * indent
    child_indent = ' ' * (indent + INDENT_SIZE)
    
    # 处理字典
    if isinstance(data, dict):
        if not data:  # 空字典
            return '{}'
        
        if is_root:
            result = '{\n'
        else:
            result = '{\n' if is_last else '{\n'
        
        items = list(data.items())
        for i, (key, value) in enumerate(items):
            is_last_item = i == len(items) - 1
            prefix = child_indent + f'"{key}": ' if isinstance(key, str) else child_indent + f'{key}: '
            
            result += prefix + ld_show(value, indent + INDENT_SIZE, is_last_item, False)
            
            if not is_last_item:
                result += ',\n'
            else:
                result += '\n'
        
        result += current_indent + '}'
        return result
    
    # 处理列表
    elif isinstance(data, list):
        if not data:  # 空列表
            return '[]'
        
        if is_root:
            result = '[\n'
        else:
            result = '[\n' if is_last else '[\n'
        
        for i, item in enumerate(data):
            is_last_item = i == len(data) - 1
            result += child_indent + ld_show(item, indent + INDENT_SIZE, is_last_item, False)
            
            if not is_last_item:
                result += ',\n'
            else:
                result += '\n'
        
        result += current_indent + ']'
        return result
    
    # 处理字符串（添加引号）
    elif isinstance(data, str):
        return f'"{data}"'
    
    # 处理其他基本类型
    else:
        return str(data)

if __name__ == '__main__':
    print(ld_show({'a': 1, 'b': 2, 'c': {'d': 3, 'e': 4}}))
    clog('DOING')