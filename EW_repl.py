from copy import deepcopy
from Parser import *
from Parser import parse, run
from os import system


now_env = deepcopy(GENV)

def is_balanced(code):
    """
    检测代码中的括号是否平衡，忽略字符串中的括号
    :param code: 要检测的代码字符串
    :return: True 表示括号平衡，False 表示不平衡
    """
    stack = []
    # 定义括号映射关系
    pairs = {')': '(', '}': '{', ']': '['}
    
    # 字符串状态标志
    in_single_quote = False
    in_double_quote = False
    escape_next = False
    
    i = 0
    while i < len(code):
        char = code[i]
        
        # 处理转义字符
        if escape_next:
            escape_next = False
            i += 1
            continue
            
        # 处理转义字符
        if char == '\\':
            escape_next = True
            i += 1
            continue
            
        # 处理单引号字符串
        if char == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
            i += 1
            continue
            
        # 处理双引号字符串
        if char == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
            i += 1
            continue
            
        # 如果在字符串中，跳过所有字符
        if in_single_quote or in_double_quote:
            i += 1
            continue
            
        # 处理括号
        if char in '({[':
            stack.append(char)
        elif char in ')}]':
            if not stack or stack[-1] != pairs[char]:
                return False
            stack.pop()
            
        i += 1
    
    # 如果栈为空，则所有括号都已正确闭合
    return len(stack) == 0

def repl():
    """
    交互式解释器 (Read-Eval-Print Loop)
    """
    system("title Exwide REPL")
    print("Exwide REPL v0.0.1-Alpha")
    print("Powered by CPython, made by CGrakeski")
    print('Type "help()", "copyright()" or "license()" for more information, "exit()" to quit')
    lexer = Lexer()
    while True:
        try:
            # 初始化多行输入缓冲区
            buffer = ""
            prompt = ">>> "
            
            while True:
                # 获取用户输入
                line = input(prompt)
                
                # 将输入添加到缓冲区
                if buffer:
                    buffer += "\n" + line
                else:
                    buffer = line
                
                # 检查括号是否平衡
                if is_balanced(buffer):
                    break
                else:
                    # 如果括号不平衡，更改提示符并继续等待输入
                    prompt = "... "
            
            # 使用完整的缓冲区进行词法分析和解析
            tok = lexer.tokenize(buffer + '\n')
            fin = run(parse(tok), now_env)
            if fin is not None:
                print(fin)
        except Exception as e:
            print(e)
            continue

if __name__ == '__main__':
    repl()