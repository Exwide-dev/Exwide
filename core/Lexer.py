import re

from core.Error import *
from core.Token import Token

class Lexer:
    def __init__(self):
        # 定义token模式，注意顺序：关键字在前，通用模式在后
        self.OPERATORS = {
            # 算术运算符
            '**':   'EXPONENT',
            '*':    'MULTIPLY', 
            '/':    'DIVIDE',
            '//':   'FLOOR_DIV',
            '%':    'MODULO',
            '+':    'PLUS',
            '-':    'MINUS',
            
            # 比较运算符
            '==':   'EQ',
            '!=':   'NEQ',
            '<':    'LT',
            '<=':   'LTE',
            '>':    'GT', 
            '>=':   'GTE',
            
            # 逻辑运算符
            'not':    'NOT',
            'and':   'AND',
            'or':   'OR',
        }
        self.token_specs = [
            ('ENDL',         r'\n'),
            ('WHITESPACE',   r'\s+'),        # 跳过空白
            ("MULTILINE_COMMENT", r"/\*.*?\*/"),  # 多行注释
            ("SINGLELINE_COMMENT", r"//[^\n]*"),  # 匹配 // 到行尾
            ('IF',           r'\bif\b'),     # 关键字
            ('ELSE',         r'\belse\b'),
            ('WHILE',        r'\bwhile\b'),
            ('FUNC',         r'\bfunc\b'),
            ('MFUNC',        r'\bmfunc\b'),
            ('IMPORT',       r'\bimport\b'),
            ('RETURN',       r'\breturn\b'),
            ('DO',           r'\bdo\b'),
            ('TRY',          r'\btry\b'),
            ('CATCH',        r'\bcatch\b'),
            ('NUMBER',       r'(\d+\.(?:\d*\(\d+\)\.\.\.|\d*)|\.\d+|\d+)'),        # 数字（支持循环小数语法，如0.(3)...）
            # ('OPERATOR',     r'[=<>!]=?|[+\-*/]'),  # 运算符
            # 根据self.OPERATORS生成运算符的正则表达式,先匹配长的再匹配短的，以保证优先匹配
            *[(name, re.escape(op)) for op, name in sorted(self.OPERATORS.items(), key=lambda x: -len(x[0]))],
            ('LPAREN',       r'\('),         # 左括号
            ('RPAREN',       r'\)'),         # 右括号
            ('LBRACE',       r'\{'),         # 左花括号
            ('RBRACE',       r'\}'),         # 右花括号
            ('LBRACK',      r'\['),         # 左方括号
            ('RBRACK',      r'\]'),         # 右方括号
            ('SEMICOLON',    r';'),          # 分号
            ('COMMA',        r'\,'),
            ('COLON',        r':'),
            ('DOT',          r'\.'),         # 点操作符（用于包访问）
            ('STRING',    r'"[^"]*"|\'[^\']*\''), # 字符串
            ('IDENTIFIER',   r'[a-zA-Z_]\w*'),  # 标识符
            ('ASSIGN',       r'='),       # 赋值
            ('MISMATCH',     r'.'),          # 任何未匹配的字符
        ]
        
        # 编译正则表达式，使用命名组，添加 re.DOTALL 让多行注释可以跨行匹配
        self.pattern = '|'.join(f'(?P<{name}>{pattern})' 
                               for name, pattern in self.token_specs)
        self.regex = re.compile(self.pattern, re.DOTALL)  # 添加 re.DOTALL
    def tokenize(self, code) -> list[Token]:
        tokens = []
        line = 0
        col = 0
        
        # 将代码按行分割，便于后续获取整行代码
        lines = code.split('\n')
        
        for match in self.regex.finditer(code):
            kind = match.lastgroup
            value = match.group()
            
            # 计算当前匹配的位置
            start_pos = match.start()
            end_pos = match.end()
            
            # 计算行号和列号
            # 统计匹配前的换行符数量
            line += code[:start_pos].count('\n') - code[:col].count('\n') if col != 0 else code[:start_pos].count('\n')
            # 计算当前行的起始位置
            line_start = code.rfind('\n', 0, start_pos) + 1 if '\n' in code[:start_pos] else 0
            # 计算列号
            col = start_pos - line_start
            
            # 获取当前行的完整代码
            current_line = lines[line] if line < len(lines) else ''
            
            if kind in ['SINGLELINE_COMMENT', 'MULTILINE_COMMENT']:
                continue  # 跳过注释
            elif kind == 'WHITESPACE':
                # 保留换行符，其他空白字符跳过
                for char in value:
                    if char == '\n':
                        token = Token('ENDL', '\n', line, col)
                        # 添加当前行的代码到token
                        token.code = current_line
                        tokens.append(token)
                        line += 1
                        col = 0
                    else:
                        col += 1
                continue
            elif kind == 'MISMATCH':
                raise_err(EW_SYNTAX_ERROR, f'Unexpected character: {value}', line=line, pos=col, code=current_line)
                return EW_SYNTAX_ERROR
            elif kind in self.OPERATORS.values():
                token = Token('OPERATOR', value, line, col)
                # 添加当前行的代码到token
                token.code = current_line
                tokens.append(token)
                col += len(value)
            else:
                token = Token(kind, value, line, col)
                # 添加当前行的代码到token
                token.code = current_line
                tokens.append(token)
                col += len(value)
        
        return tokens

if __name__ == '__main__':
    code = """
foobar = do (a) {
    return a + 1
}
print(foobar(4 ** 2))
    """
    toks = Lexer().tokenize(code)
    print(ld_show(toks))
    for ks, tok in enumerate(toks):
        print(f'Token {ks:<5} {tok.typ:16}{repr(tok.val)[1:-1]}')
