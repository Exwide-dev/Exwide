from time import sleep, strftime, localtime

LOG = 0

# 全局调用栈，用于跟踪函数调用，每个元素是包含函数名和上下文信息的字典
execution_stack = []

def clog(msg):
    timenow = strftime('%H:%M:%S', localtime())
    if LOG:
        #sleep(.05)
        print(f'[DEBUG OUTPUT {timenow}] {msg}\n', flush = True)
    # write_file('debug.log', f'[DEBUG OUTPUT {timenow}] {msg}\n')

def push_stack(function_name, line=None, code=None):
    """
    将函数调用压入调用栈
    
    Args:
        function_name: 函数名
        line: 函数调用所在行号
        code: 函数调用所在行的代码
    """
    execution_stack.append({
        'name': function_name,
        'line': line,
        'code': code
    })

def pop_stack():
    """
    从调用栈中弹出函数调用
    """
    if execution_stack:
        execution_stack.pop()

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

def raise_err(err, msg, line=None, code=None, pos=None):
    clog(f'raise_err({err.__name__!r}, {msg!r}, {line!r}, {code!r}, {pos!r})')
    """
    抛出错误并显示友好的错误信息
    
    Args:
        err: 错误类型
        msg: 错误信息
        line: 错误所在行
        code: 错误代码行文本
        pos: 错误位置在代码行中的索引，可以是单个整数或整数列表
    """
    # 将内部错误类型映射为用户友好的错误类型
    err_map = {
        'EW_SYNTAX_ERROR': 'SyntaxError',
        'EW_TYPE_ERROR': 'TypeError',
        'EW_RUNTIME_ERROR': 'RuntimeError',
        'EW_ERROR': 'Error'
    }
    
    err_name = err_map.get(err.__name__, err.__name__)
    print(f'\033[31mError occured!\033[0m')
    
    # 如果提供了代码行和位置，显示友好的错误位置
    if code and pos is not None:
        print()
        # 打印代码行
        print(f'    \033[34m{code}\033[0m')
        
        # 处理单个位置或位置列表
        positions = [pos] if isinstance(pos, int) else pos
        
        # 生成错误位置指示符字符串
        max_pos = max(positions) if positions else 0
        indicator = [' '] * (max_pos + 1)
        
        # 在所有错误位置标记~符号
        for p in positions:
            if p < len(indicator):
                indicator[p] = '~'
        
        # 打印错误位置指示符
        print(f'    \033[32m{''.join(indicator)}\033[0m')

        # 打印错误名称
        print()
        if msg:
            print(f'\033[31m{err_name}: {msg}\033[0m')
        else:
            print(f'\033[31m{err_name}\033[0m')
    else:
        if msg:
            print(f'\033[31m{err_name}: {msg}\033[0m')
        else:
            print(f'\033[31m{err_name}\033[0m')
    
    # 打印调用栈
    if execution_stack:
        print('\n\033[33mCall Stack:\033[0m')
        for i, frame in enumerate(reversed(execution_stack)):
            indent = '  ' * i
            func_name = frame['name']
            frame_line = frame['line']
            frame_code = frame['code']
            
            # 打印函数调用信息
            print(f'{indent}-> {func_name}', end='')
            
            # 打印行号和代码片段（如果有）
            if frame_line is not None:
                print(f' (line {frame_line})')
                if frame_code:
                    print(f'{indent}   \033[36m{frame_code.strip()}\033[0m')
            else:
                print()
    
    # 如果提供了错误位置，显示错误位置标注
    if line is not None and code is not None:
        print('\n\033[31mError Location:\033[0m')
        print(f'  Line {line}: \033[34m{code.strip()}\033[0m')
        if pos is not None:
            # 生成错误位置指示符
            positions = [pos] if isinstance(pos, int) else pos
            max_pos = max(positions) if positions else 0
            indicator = [' '] * (max_pos + 1)
            for p in positions:
                if p < len(indicator):
                    indicator[p] = '^'
            # 计算缩进，确保指示器对齐
            indent_length = len(f'Line {line}: ') - 2
            print(f'  {' ' * indent_length}\033[32m{''.join(indicator)}\033[0m')
    
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