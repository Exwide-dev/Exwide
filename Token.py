# Exwide的lex部分，负责提取词法单元
import re
import Error

class Token:
    def __init__(self, typ, value):
        self.typ = typ  # 词法单元类型
        self.val = value  # 词法单元值
        self.tup = (typ, value)
    
    def __getitem__(self, index):
        return self.tup[index]

    def __repr__(self):
        kval = (
            self.val
            .replace('\n', '\\n')
            .replace('\t', '\\t')
            .replace('(', '<left_paren>')
            .replace(')', '<right_paren>')
            .replace('{', '<left_brace>')
            .replace('}', '<right_brace>')
            .replace('[', '<left_bracket>')
            .replace(']', '<right_bracket>')
        )
        return f'Token: {self.typ}({kval})'
    
    __str__ = __repr__
