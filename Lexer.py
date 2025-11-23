import re

from Error import *
from Token import Token

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

            # 其他特殊符号
            ',':    'COMMA',
        }
        self.token_specs = [
            ('WHITESPACE',   r'\s+'),        # 跳过空白
            ("MULTILINE_COMMENT", r"/\*.*?\*/"),  # 多行注释
            ("SINGLELINE_COMMENT", r"//[^\n]*"),  # 匹配 // 到行尾
            ('IF',           r'\bif\b'),     # 关键字
            ('ELSE',         r'\belse\b'),
            ('WHILE',        r'\bwhile\b'),
            ('FUNC',         r'\bfunc\b'),
            ('RETURN',       r'\breturn\b'),
            ('DO',           r'\bdo\b'),
            ('NUMBER',       r'(\d+\.\d*|\.\d+|\d+)'),        # 数字（使其能识别小数）
            # ('OPERATOR',     r'[=<>!]=?|[+\-*/]'),  # 运算符
            # 根据self.OPERATORS生成运算符的正则表达式,先匹配长的再匹配短的，以保证优先匹配
            *[(name, re.escape(op)) for op, name in sorted(self.OPERATORS.items(), key=lambda x: -len(x[0]))],
            ('LPAREN',       r'\('),         # 左括号
            ('RPAREN',       r'\)'),         # 右括号
            ('LBRACE',       r'\{'),         # 左花括号
            ('RBRACE',       r'\}'),         # 右花括号
            ('SEMICOLON',    r';'),          # 分号
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
        for match in self.regex.finditer(code):
            kind = match.lastgroup
            value = match.group()
            
            if kind in ['WHITESPACE', 'SINGLELINE_COMMENT', 'MULTILINE_COMMENT']:
                continue  # 跳过空白和注释
            elif kind == 'MISMATCH':
                raise_err(EW_SYNTAX_ERROR, f'Unexpected character: {value}')
                return EW_SYNTAX_ERROR
            elif kind in self.OPERATORS.values():
                tokens.append(Token('OPERATOR', value))
            else:
                tokens.append(Token(kind, value))
        
        return tokens

if __name__ == '__main__':
    code = """
foobar = do (a) {
    return a + 1;
}
print(foobar(4 ** 2));
    """
    toks = Lexer().tokenize(code)
    print(toks)
    for ks, tok in enumerate(toks):
        print(f'Token {ks:<5} {tok.typ:16}{tok.val}')
