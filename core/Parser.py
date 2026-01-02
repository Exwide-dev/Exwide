from core.Lexer import *
from core.Token import *
from core.Env import *
from core.Type import *
from core.Package import import_package, EW_Package, auto_load_all_packages, packages
from core.Error import raise_err, push_stack, pop_stack
from typing import Any, TypeAlias
from core.ew_builtins import ew_builtins
import sys
sys.setrecursionlimit(1000000)

ASTNode: TypeAlias = dict[str, Any]
MayASTNode: TypeAlias = ASTNode | None
ASTNodelist: TypeAlias = list[ASTNode]

class Parser:
    """语法解析器"""
    
    def __init__(self, tokens: list[Token], code: str = None):
        self.tokens = tokens
        self.current = 0
        self.ast = []
        self.paren_stack = []  # 括号跟踪栈，元素类型：'paren', 'bracket', 'table', 'block'
        self.code = code  # 原始代码，用于错误显示
        self.line_info = self._build_line_info(code) if code else None  # 行信息，用于错误定位
    
    def parse(self) -> ASTNodelist:
        """解析token序列为AST"""
        clog(f'函数 parse({ld_show(self.tokens)}) 开始')
        
        while self._is_valid():
            clog(f'当前位于 token #{self.current}: {self._current_token()}')
            node = self._parse_statement()
            if node:
                self.ast.append(node)
        
        clog('函数 parse 结束')
        return self.ast
    
    def _parse_statement(self) -> MayASTNode:
        """解析语句"""
        token = self._current_token()
        
        # 跳过换行符
        if token.typ == 'ENDL':
            self._advance()
            return None
            
        # 先检查关键字，避免将关键字解析为装饰器
        if token.typ == 'IF':
            return self._parse_if_statement()
        elif token.typ == 'RETURN':
            return self._parse_return_statement()
        elif token.typ == 'WHILE':
            return self._parse_while_statement()
        elif token.typ == 'FUNC':
            return self._parse_func_statement()
        elif token.typ == 'MFUNC':
            return self._parse_mfunc_statement()
        elif token.typ == 'IMPORT':
            return self._parse_import_statement()
        elif token.typ == 'IDENTIFIER':
            # 保存初始位置，用于回溯
            start_pos = self.current
            
            # 检查是否是装饰器+函数声明的形式
            # 先解析可能的装饰器表达式
            decorator_expr = self._parse_expression()
            
            # 检查下一个token是否是FUNC或MFUNC
            if self._is_valid() and self._current_token().typ in ['FUNC', 'MFUNC']:
                # 是装饰器+函数声明的形式，解析函数声明
                token = self._current_token()
                decorators = [decorator_expr]
                if token.typ == 'FUNC':
                    return self._parse_func_statement(decorators)
                elif token.typ == 'MFUNC':
                    return self._parse_mfunc_statement(decorators)
            
            # 不是装饰器+函数声明的形式，回溯
            self.current = start_pos
            
            # 解析完整表达式，包括可能的赋值
            left_expr = self._parse_expression()
            
            # 检查是否是赋值语句
            if self._is_valid() and self._current_token().typ == 'ASSIGN':
                # 是赋值语句，解析赋值
                self._advance()  # 跳过赋值符号
                value = self._parse_expression()
                self._consume_endls()
                
                if left_expr['kind'] == 'VarRef':
                    # 简单变量赋值
                    return {
                        'kind': 'VarAssign',
                        'name': left_expr['name'],
                        'value': value
                    }
                elif left_expr['kind'] == 'TableAccess':
                    # Table访问赋值
                    return {
                        'kind': 'TableAssign',
                        'table': left_expr['table'],
                        'key': left_expr['key'],
                        'value': value
                    }
                else:
                    raise_err(EW_SYNTAX_ERROR, f'Cannot assign to expression of type {left_expr["kind"]}')
                    return None
            else:
                # 不是赋值语句，解析为表达式语句
                self._consume_endls()
                return left_expr
        else:
            return self._parse_expression_statement()
    
    def _parse_expression_statement(self) -> MayASTNode:
        """解析表达式语句（只处理ENDL作为语句结束符）"""
        clog('95 发现表达式语句')
        expr = self._parse_expression()
        clog(f'表达式语句解析完成: 表达式={expr}')
        if expr:
            # 检查是否有后续表达式
            if self._is_valid() and self._current_token().typ != 'ENDL':
                raise_err(EW_SYNTAX_ERROR, f'Unexpected token after expression: {self._current_token().val}')
                return None
            self._consume_endls()  # 消费后续的换行符
        return expr
    
    def _consume_endls(self):
        """消费连续的换行符"""
        while self._is_valid() and self._current_token().typ == 'ENDL':
            self._advance()
    
    def _parse_return_statement(self) -> ASTNode:
        """解析return语句"""
        clog('发现return语句')
        self._advance()  # 跳过 'return'
        
        # 解析返回值表达式
        value = None
        clog(f'当前Token: {self._current_token()}')
        if self._is_valid() and self._current_token().typ not in ['ENDL', 'RBRACE']:
            value = self._parse_expression()
            clog(f'value: {value}')
        
        # 消费语句结束符
        self._consume_endls()
        
        clog(f'return语句解析完成: 返回值={value}')
        return {
            'kind': 'Return',
            'value': value
        }
    
    def _parse_if_statement(self) -> ASTNode:
        """解析if语句"""
        clog('发现if语句')
        self._advance()  # 跳过 'if'
        
        # 解析条件表达式
        if not self._is_valid() or self._current_token().typ != 'LPAREN':
            raise_err(EW_SYNTAX_ERROR, 'Expected "(" after "if"')
            return None
        
        self._advance()  # 跳过 '('
        condition = self._parse_expression()
        
        if not self._is_valid() or self._current_token().typ != 'RPAREN':
            raise_err(EW_SYNTAX_ERROR, 'Expected ")" after condition')
            return None
        
        self._advance()  # 跳过 ')'
        
        # 消费可能的换行符
        self._consume_endls()
        
        # 解析if代码块
        if not self._is_valid() or self._current_token().typ != 'LBRACE':
            raise_err(EW_SYNTAX_ERROR, 'Expected "{" after if condition')
            return None
        
        self._advance()  # 跳过 '{'
        if_body = self._parse_block()
        
        if not self._is_valid() or self._current_token().typ != 'RBRACE':
            raise_err(EW_SYNTAX_ERROR, 'Expected "}" after if body')
            return None
        
        self._advance()  # 跳过 '}'
        
        # 消费可能的换行符
        self._consume_endls()
        
        # 解析可选的else分支
        else_body = None
        if self._is_valid() and self._current_token().typ == 'ELSE':
            self._advance()  # 跳过 'else'
            
            # 消费可能的换行符
            self._consume_endls()
            
            if not self._is_valid() or self._current_token().typ != 'LBRACE':
                raise_err(EW_SYNTAX_ERROR, 'Expected "{" after "else"')
                return None
            
            self._advance()  # 跳过 '{'
            else_body = self._parse_block()
            
            if not self._is_valid() or self._current_token().typ != 'RBRACE':
                raise_err(EW_SYNTAX_ERROR, 'Expected "}" after else body')
                return None
            
            self._advance()  # 跳过 '}'
            self._consume_endls()
        
        clog(f'if语句解析完成: 条件={condition}, if分支长度={len(if_body)}, else分支长度={0 if else_body is None else len(else_body)}')
        return {
            'kind': 'If',
            'condition': condition,
            'if_body': if_body,
            'else_body': else_body
        }
    
    def _parse_block(self) -> ASTNodelist:
        """解析代码块（大括号内的语句序列）"""
        block = []
        self.paren_stack.append('block')  # 进入代码块花括号
        
        while self._is_valid() and self._current_token().typ != 'RBRACE':
            # 在代码块内，换行符作为语句分隔符
            if self._current_token().typ == 'ENDL':
                self._advance()
                continue
                
            node = self._parse_statement()
            if node:
                block.append(node)
        
        self.paren_stack.pop()  # 退出代码块花括号
        return block
    
    def _parse_while_statement(self) -> ASTNode:
        """解析while语句"""
        clog('发现while语句')
        self._advance()  # 跳过 'while'
        
        # 解析条件表达式
        if not self._is_valid() or self._current_token().typ != 'LPAREN':
            raise_err(EW_SYNTAX_ERROR, 'Expected "(" after "while"')
        
        self._advance()  # 跳过 '('
        condition = self._parse_expression()
        
        if not self._is_valid() or self._current_token().typ != 'RPAREN':
            raise_err(EW_SYNTAX_ERROR, 'Expected ")" after condition')
        
        self._advance()  # 跳过 ')'
        
        # 消费可能的换行符
        self._consume_endls()
        
        # 解析循环体
        if not self._is_valid() or self._current_token().typ != 'LBRACE':
            raise_err(EW_SYNTAX_ERROR, 'Expected "{" after while condition')
            
        self._advance()  # 跳过 '{'
        body = self._parse_block()
        
        if not self._is_valid() or self._current_token().typ != 'RBRACE':
            raise_err(EW_SYNTAX_ERROR, 'Expected "}" to close while statement')
            
        self._advance()  # 跳过 '}'
        
        return {
            'kind': 'WhileStatement',
            'condition': condition,
            'body': body
        }

    def _parse_func_statement(self, decorators=None) -> ASTNode:
        """解析函数声明语句
        
        Args:
            decorators: 装饰器列表，默认为空
        
        Returns:
            包含装饰器信息的函数声明AST节点
        """
        clog('发现函数声明')
        self._advance()  # 跳过 'func'
        
        # 检查标识符是否合法
        if not self._is_valid() or self._current_token().typ != 'IDENTIFIER':
            raise_err(EW_SYNTAX_ERROR, 'Expected identifier after "func"')
            return None
        
        name = self._current_token().val
        self._advance()  # 跳过标识符
        
        # 检查参数列表
        params = []
        if self._is_valid() and self._current_token().typ == 'LPAREN':
            self._advance()  # 跳过 '('
            self.paren_stack.append('paren')  # 进入圆括号
            
            # 解析参数列表
            while self._is_valid() and self._current_token().typ != 'RPAREN':
                # 根据当前括号类型决定是否跳过换行符
                if self._current_token().typ == 'ENDL' and self._should_ignore_endl():
                    self._advance()
                    continue
                    
                # 解析参数名
                if self._current_token().typ == 'IDENTIFIER':
                    param_name = self._current_token().val
                    params.append(param_name)
                    self._advance()
                    
                    # 检查是否有逗号分隔更多参数
                    if self._is_valid() and self._current_token().typ == 'COMMA':
                        self._advance()  # 跳过 ','
                    elif self._is_valid() and self._current_token().typ != 'RPAREN':
                        # 不是逗号也不是右括号，报错
                        raise_err(EW_SYNTAX_ERROR, f'Expected comma or closing parenthesis after parameter, got {self._current_token().val}')
                        return None
                else:
                    # 不是标识符，报错
                    raise_err(EW_SYNTAX_ERROR, 'Expected parameter name')
                    return None
            
            # 检查右括号
            if not self._is_valid() or self._current_token().typ != 'RPAREN':
                raise_err(EW_SYNTAX_ERROR, 'Expected ")" after parameters')
                return None
            
            self._advance()  # 跳过 ')'
            self.paren_stack.pop()  # 退出圆括号
        
        # 消费可能的换行符
        self._consume_endls()
        
        # 解析函数体
        if not self._is_valid() or self._current_token().typ != 'LBRACE':
            raise_err(EW_SYNTAX_ERROR, 'Expected "{" after function parameters')
            return None
        
        self._advance()  # 跳过 '{'
        body = self._parse_block()
        
        if not self._is_valid() or self._current_token().typ != 'RBRACE':
            raise_err(EW_SYNTAX_ERROR, 'Expected "}" after function body')
            return None
        
        self._advance()  # 跳过 '}'
        
        # 消费可能的换行符
        self._consume_endls()
        
        # 生成AST节点，包含装饰器信息
        func_node = {
            'kind': 'FuncDecl',
            'name': name,
            'params': params,
            'body': body
        }
        
        # 添加装饰器信息
        if decorators:
            func_node['decorators'] = decorators
        
        clog(f'函数声明解析完成: 名称={name}, 参数={params}, 装饰器={decorators}, 函数体长度={len(body)}')
        return func_node

    def _parse_mfunc_statement(self, decorators=None) -> ASTNode:
        """解析mfunc语句
        
        Args:
            decorators: 装饰器列表，默认为空
        
        Returns:
            包含装饰器信息的mfunc声明AST节点
        """
        clog('发现mfunc语句')
        self._advance()  # 跳过 'mfunc'
        
        # 检查标识符是否合法
        if not self._is_valid() or self._current_token().typ != 'IDENTIFIER':
            raise_err(EW_SYNTAX_ERROR, 'Expected identifier after "mfunc"')
            return None
        
        name = self._current_token().val
        self._advance()  # 跳过标识符
        
        # 检查参数列表
        params = []
        if self._is_valid() and self._current_token().typ == 'LPAREN':
            self._advance()  # 跳过 '('
            self.paren_stack.append('paren')  # 进入圆括号
            
            # 解析参数列表
            while self._is_valid() and self._current_token().typ != 'RPAREN':
                # 根据当前括号类型决定是否跳过换行符
                if self._current_token().typ == 'ENDL' and self._should_ignore_endl():
                    self._advance()
                    continue
                    
                # 解析参数名
                if self._current_token().typ == 'IDENTIFIER':
                    param_name = self._current_token().val
                    params.append(param_name)
                    self._advance()
                    
                    # 检查是否有逗号分隔更多参数
                    if self._is_valid() and self._current_token().typ == 'COMMA':
                        self._advance()  # 跳过 ','
                    elif self._is_valid() and self._current_token().typ != 'RPAREN':
                        # 不是逗号也不是右括号，报错
                        raise_err(EW_SYNTAX_ERROR, f'Expected comma or closing parenthesis after parameter, got {self._current_token().val}')
                        return None
                else:
                    # 不是标识符，报错
                    raise_err(EW_SYNTAX_ERROR, 'Expected parameter name')
                    return None
            
            # 检查右括号
            if not self._is_valid() or self._current_token().typ != 'RPAREN':
                raise_err(EW_SYNTAX_ERROR, 'Expected ")" after parameters')
                return None
            
            self._advance()  # 跳过 ')'
            self.paren_stack.pop()  # 退出圆括号
        
        # 消费可能的换行符
        self._consume_endls()
        
        # 解析函数体
        if not self._is_valid() or self._current_token().typ != 'LBRACE':
            raise_err(EW_SYNTAX_ERROR, 'Expected "{" after mfunc parameters')
            return None
        
        self._advance()  # 跳过 '{'
        body = self._parse_block()
        
        if not self._is_valid() or self._current_token().typ != 'RBRACE':
            raise_err(EW_SYNTAX_ERROR, 'Expected "}" after mfunc body')
            return None
        
        self._advance()  # 跳过 '}'
        
        # 消费可能的换行符
        self._consume_endls()
        
        # 生成AST节点，包含装饰器信息
        mfunc_node = {
            'kind': 'MFuncDecl',
            'name': name,
            'params': params,
            'body': body
        }
        
        # 添加装饰器信息
        if decorators:
            mfunc_node['decorators'] = decorators
        
        clog(f'mfunc声明解析完成: 名称={name}, 参数={params}, 装饰器={decorators}, 函数体长度={len(body)}')
        return mfunc_node
    
    def _parse_import_statement(self) -> ASTNode:
        """解析import语句"""
        clog('发现import语句')
        self._advance()  # 跳过 'import'
        
        # 检查包名是否合法
        if not self._is_valid() or self._current_token().typ != 'IDENTIFIER':
            raise_err(EW_SYNTAX_ERROR, 'Expected package name after "import"')
            return None
        
        package_name = self._current_token().val
        self._advance()  # 跳过包名
        
        # 消费语句结束符
        self._consume_endls()
        
        clog(f'import声明解析完成: 包名={package_name}')
        return {
            'kind': 'Import',
            'name': package_name
        }

    def _parse_expression(self) -> MayASTNode:
        """解析表达式"""
        # 根据当前括号类型决定是否跳过换行符
        clog(f'解析表达式：{self._is_valid()=}, {self._current_token()=}')
        while self._is_valid() and self._current_token().typ == 'ENDL' and self._should_ignore_endl():
            self._advance()
        
        if not self._is_valid():
            return None
            
        # 直接调用_parse_operator_expression，从最低优先级开始解析
        return self._parse_operator_expression()
    
    def _parse_call_expression(self) -> MayASTNode:
        """解析调用表达式（最高优先级）"""
        left = self._parse_primary()
        
        # 检查是否是函数调用
        while self._is_valid() and self._current_token().typ == 'LPAREN':
            left = self._parse_function_call(left)
        
        return left
    
    def _parse_operator_expression(self, left=None, precedence=0) -> MayASTNode:
        """解析操作符表达式，实现正确的运算符优先级
        
        Args:
            left: 左侧表达式
            precedence: 当前优先级级别
        """
        # 定义运算符优先级（数字越大，优先级越高）
        precedence_map = {
            'or': 1,
            'and': 2,
            '==': 3,
            '!=': 3,
            '<': 4,
            '<=': 4,
            '>': 4,
            '>=': 4,
            '+': 5,
            '-': 5,
            '*': 6,
            '/': 6,
            '**': 7
        }
        
        if left is None:
            # 获取左侧表达式，可能是基本表达式或括号表达式
            left = self._parse_primary()
        
        if left is None:
            return None
            
        # 处理运算符链
        while (self._is_valid() and 
               self._current_token().typ == 'OPERATOR' and 
               self._current_token().val in precedence_map):
            
            current_op = self._current_token().val
            current_prec = precedence_map[current_op]
            
            # 检查运算符优先级，如果当前运算符优先级小于等于当前优先级，返回结果
            if current_prec <= precedence:
                return left
            
            self._advance()
            
            # 获取右侧的基本表达式（优先级最高的表达式）
            right = self._parse_primary()
            
            if right is None:
                raise_err(EW_SYNTAX_ERROR, 'Expected expression after operator')
                return None
            
            # 处理右侧表达式可能有的更高优先级运算符
            # 对于右结合运算符（如**），使用当前优先级
            next_prec = current_prec + 1
            if current_op == '**':
                next_prec = current_prec
            
            # 递归解析右侧表达式的剩余部分
            right = self._parse_operator_expression(right, next_prec)
            
            # 构建运算符节点
            left = {
                'kind': 'Operator',
                'operator': current_op,
                'left': left,
                'right': right
            }
        
        return left
    
    def _parse_function_call(self, func_expr: ASTNode) -> ASTNode:
        """解析函数调用（作为运算符处理）"""
        clog(f'351 发现函数调用{func_expr}, 当前Token #{self.current}: {self._current_token()}')
        self._advance()  # 跳过左括号
        self.paren_stack.append('paren')  # 进入圆括号
        clog(f'353 跳过括号, 当前Token #{self.current}: {self._current_token()}')
        
        args = []
        
        no_args = False

        # 如果右括号紧跟着，说明没有参数
        if self._is_valid() and self._current_token().typ == 'RPAREN':
            no_args = True
            clog('[')
            clog(f'令no_args为True')
            clog(f'对于对函数{func_expr}的parse, 当前Token #{self.current}: {self._current_token()}')
            self._advance()  # 跳过右括号
            self.paren_stack.pop()  # 退出圆括号
            clog(f'函数{func_expr}调用: 无参数')
            clog(f'366 跳过括号，当前Token #{self.current}: {self._current_token()}')
            clog(']')
        else:
            # 解析参数列表
            while self._is_valid():
                # 检查是否遇到右括号（参数列表结束）
                if self._current_token().typ == 'RPAREN':
                    clog(f'374 当前的Token #{self.current}为: {self._current_token()}, 跳过右括号')
                    break
                    
                # 跳过换行符
                if self._current_token().typ == 'ENDL':
                    self._advance()
                    continue
                    
                # 解析参数表达式
                arg = self._parse_expression()
                if arg is not None:  # 允许空表达式
                    args.append(arg)
                
                # 检查是否有更多参数
                if self._is_valid() and self._current_token().typ == 'COMMA':
                    self._advance()  # 跳过逗号
                elif self._is_valid() and self._current_token().typ == 'RPAREN':
                    # 遇到右括号，参数列表结束
                    break
                elif self._is_valid() and self._current_token().typ == 'ENDL':
                    # 换行符，继续解析
                    self._advance()
                else:
                    # 不是逗号也不是右括号，报错
                    clog(f'398 当前的Token #{self.current}为: {self._current_token()}')
                    raise_err(EW_SYNTAX_ERROR, f'Expected comma or closing parenthesis, got {self._current_token().val if self._current_token().val != "\n" else "a newline"}')
                    return None
    
        clog(f'402 当前对于对{func_expr}的parse的Token #{self.current}为: {self._current_token()}')
        # 检查右括号
        if not self._is_valid() or self._current_token().typ != 'RPAREN' and not no_args:
            raise_err(EW_SYNTAX_ERROR, f'Expected closing parenthesis, got {self._current_token().val if self._current_token().val != "\n" else "a newline"}')
            return None
        clog(f'{no_args}')
        if not no_args:
            self._advance()
            self.paren_stack.pop()  # 退出圆括号
            clog(f'跳过括号后, 当前对于对{func_expr}的parse的Token #{self.current}: {self._current_token()}')
        else:
            clog('不跳过括号')
        clog(f'函数{func_expr}调用: 参数数量: {len(args)}')
        result = {
            'kind': 'FuncCall',
            'func': func_expr,
            'args': args
        }
        clog(f'函数{func_expr}调用结束, 将会返回 {ld_show(result)}')
        
        # 检查并处理可能的后续表达式操作，如列表访问或属性访问
        # 检查是否是包访问表达式，如package.func
        while self._is_valid() and self._current_token().typ == 'DOT':
            result = self._parse_package_access(result)
        
        # 检查是否是Table访问表达式，如table[key]或list[index]
        while self._is_valid() and self._current_token().typ == 'LBRACK':
            result = self._parse_table_access(result)
        
        return result

    def _parse_primary(self) -> MayASTNode:
        """解析基本表达式，包括函数调用作为最高优先级操作"""
        if not self._is_valid():
            return None
            
        token = self._current_token()
        
        # 根据当前括号类型决定是否跳过换行符
        if token.typ == 'ENDL' and self._should_ignore_endl():
            self._advance()
            return self._parse_primary()
            
        if token.typ == 'IDENTIFIER':
            # 检查是否是布尔字面量
            if token.val == 'true' or token.val == 'false':
                expr = self._parse_boolean_literal()
            else:
                expr = self._parse_identifier_expr()
        elif token.typ in ('NUMBER', 'STRING'):
            expr = self._parse_literal()
        elif token.typ == 'LPAREN':
            expr = self._parse_parenthesized()
        elif token.typ == 'LBRACE':
            expr = self._parse_table_literal()
        elif token.typ == 'LBRACK':
            expr = self._parse_list_literal()
        elif token.typ == 'DO':
            clog(f'token #{ self.current } {token}: do')
            expr = self._parse_do_expression()
        else:
            clog(f'当前的Token类型为: {token.typ}, 未知')
            # 使用token中记录的行列位置
            line = token.line
            
            # 生成多个位置标记，每个字符对应一个位置
            pos = []
            for i in range(len(token.val)):
                pos.append(token.col + i)
            
            # 获取当前行的代码
            code_line = None
            if self.code:
                lines = self.code.split('\n')
                if 0 <= line < len(lines):
                    code_line = lines[line]
            # 只显示token的value，而不是完整的token对象
            raise_err(EW_SYNTAX_ERROR, f'Unexpected token: {token.val}', line=line, code=code_line, pos=pos)
            return None
        
        # 检查是否是包访问表达式，如package.func
        while self._is_valid() and self._current_token().typ == 'DOT':
            expr = self._parse_package_access(expr)
        
        # 检查是否是Table访问表达式，如table[key]或list[index]
        while self._is_valid() and self._current_token().typ == 'LBRACK':
            expr = self._parse_table_access(expr)
        
        # 检查是否是函数调用（最高优先级操作）
        while self._is_valid() and self._current_token().typ == 'LPAREN':
            expr = self._parse_function_call(expr)
        
        return expr
    
    def _parse_do_expression(self) -> ASTNode:
        """解析do表达式"""
        clog('发现do表达式')
        self._advance()  # 跳过 'do'
        
        # 解析参数列表
        params = []
        if self._is_valid() and self._current_token().typ == 'LPAREN':
            self._advance()  # 跳过 '('
            self.paren_stack.append('paren')  # 进入圆括号
            
            # 解析参数列表，直到遇到右括号
            while self._is_valid() and self._current_token().typ != 'RPAREN':
                # 跳过换行符
                if self._current_token().typ == 'ENDL' and self._should_ignore_endl():
                    self._advance()
                    continue
                
                # 解析参数名
                if self._current_token().typ == 'IDENTIFIER':
                    params.append(self._current_token().val)
                    self._advance()
                    
                    # 如果有逗号，继续解析下一个参数
                    if self._is_valid() and self._current_token().typ == 'COMMA':
                        self._advance()  # 跳过 ','
                    elif self._is_valid() and self._current_token().typ != 'RPAREN':
                        # 不是逗号也不是右括号，报错
                        raise_err(EW_SYNTAX_ERROR, f'Expected comma or closing parenthesis after parameter, got {self._current_token().val}')
                        return None
                elif self._current_token().typ == 'RPAREN':
                    # 遇到右括号，退出循环
                    break
                else:
                    # 不是标识符，报错
                    raise_err(EW_SYNTAX_ERROR, f'Expected parameter name, got {self._current_token().val}')
                    return None
            
            if not self._is_valid() or self._current_token().typ != 'RPAREN':
                raise_err(EW_SYNTAX_ERROR, 'Expected ")" after parameters')
                return None
            
            self._advance()  # 跳过 ')'
            self.paren_stack.pop()  # 退出圆括号
        
        # 消费可能的换行符
        self._consume_endls()
        
        # 解析函数体
        if not self._is_valid() or self._current_token().typ != 'LBRACE':
            raise_err(EW_SYNTAX_ERROR, 'Expected "{" after do parameters')
            return None
        
        self._advance()  # 跳过 '{'
        body = self._parse_block()
        
        if not self._is_valid() or self._current_token().typ != 'RBRACE':
            raise_err(EW_SYNTAX_ERROR, 'Expected "}" after do body')
            return None
        
        self._advance()  # 跳过 '}'
        
        clog(f'do表达式解析完成: 参数={params}, 函数体长度={len(body)}')
        return {
            'kind': 'DoExpr',
            'params': params,
            'body': body
        }
    
    def _parse_identifier_expr(self) -> ASTNode:
        """解析标识符表达式（变量引用）"""
        identifier = self._current_token()
        self._advance()
        return self._create_var_reference(identifier)
    
    def _parse_assignment(self) -> ASTNode:
        """解析变量赋值"""
        clog('发现赋值操作')
        identifier = self._current_token()
        self._advance()  # 跳过标识符
        
        if not self._is_valid() or self._current_token().typ != 'ASSIGN':
            raise_err(EW_SYNTAX_ERROR, 'Expected assignment operator')
            return None
        
        self._advance()  # 跳过赋值符号
        
        # 解析赋值表达式
        value = self._parse_expression()
        
        # 消费语句结束符
        self._consume_endls()
        
        clog(f'赋值: {identifier.val} = {value}')
        return {
            'kind': 'VarAssign',
            'name': identifier.val,
            'value': value
        }
    
    def _parse_literal(self) -> ASTNode:
        """解析字面量"""
        clog('发现字面量')
        token = self._current_token()
        self._advance()
        
        if token.typ == 'NUMBER':
            value_type = EW_Number
            value = EW_Number(token.val)
        else:  # STRING
            value_type = EW_String
            value = EW_String(token.val)
        
        return {
            'kind': 'Lit',
            'type': value_type,
            'val': value
        }
    
    def _parse_boolean_literal(self) -> ASTNode:
        """解析布尔字面量 true 和 false"""
        clog('发现布尔字面量')
        token = self._current_token()
        self._advance()
        
        # 创建布尔值
        value = EW_Boolean(True if token.val == 'true' else False)
        
        return {
            'kind': 'Lit',
            'type': EW_Boolean,
            'val': value
        }
    
    def _parse_table_literal(self) -> ASTNode:
        """解析Table字面量，如 {"foobar": 42, 24: "Hi!"}"""
        clog('发现Table字面量')
        self._advance()  # 跳过左花括号
        self.paren_stack.append('table')  # 进入Table花括号
        
        pairs = []
        
        # 解析键值对
        while self._is_valid() and self._current_token().typ != 'RBRACE':
            # 跳过换行符
            if self._current_token().typ == 'ENDL':
                self._advance()
                continue
            
            # 解析键
            key = self._parse_expression()
            
            # 跳过可能的换行符
            if self._is_valid() and self._current_token().typ == 'ENDL':
                self._advance()
            
            # 检查冒号
            if not self._is_valid() or self._current_token().typ != 'COLON':
                raise_err(EW_SYNTAX_ERROR, f'Expected colon after key, got {self._current_token().val}')
                return None
            
            self._advance()  # 跳过冒号
            
            # 跳过可能的换行符
            if self._is_valid() and self._current_token().typ == 'ENDL':
                self._advance()
            
            # 解析值
            value = self._parse_expression()
            
            # 添加到键值对列表
            pairs.append((key, value))
            
            # 检查是否有逗号
            self._consume_endls()
            if self._is_valid() and self._current_token().typ == 'COMMA':
                self._advance()  # 跳过逗号
            elif self._current_token().typ != 'RBRACE':
                # 不是逗号也不是右花括号，报错
                raise_err(EW_SYNTAX_ERROR, f'Expected comma or closing brace, got {self._current_token().val!r}')
                return None
        
        # 检查右花括号
        if not self._is_valid() or self._current_token().typ != 'RBRACE':
            raise_err(EW_SYNTAX_ERROR, f'Expected closing brace, got {self._current_token().val}')
            return None
        
        self._advance()  # 跳过右花括号
        self.paren_stack.pop()  # 退出Table花括号
        
        return {
            'kind': 'TableLit',
            'pairs': pairs
        }
    
    def _parse_list_literal(self) -> ASTNode:
        """解析列表字面量，如 [1, true, 'Hi!', do (x) {return x + 1}]"""
        clog('发现List字面量')
        self._advance()  # 跳过左方括号
        self.paren_stack.append('bracket')  # 进入方括号
        
        elements = []
        
        # 解析列表元素
        while self._is_valid() and self._current_token().typ != 'RBRACK':
            # 跳过换行符
            if self._current_token().typ == 'ENDL':
                self._advance()
                continue
            
            # 解析元素表达式
            element = self._parse_expression()
            if element is not None:
                elements.append(element)
            
            # 检查是否有逗号
            self._consume_endls()
            if self._is_valid() and self._current_token().typ == 'COMMA':
                self._advance()  # 跳过逗号
            elif self._current_token().typ != 'RBRACK':
                # 不是逗号也不是右方括号，报错
                raise_err(EW_SYNTAX_ERROR, f'Expected comma or closing bracket, got {self._current_token().val!r}')
                return None
        
        # 检查右方括号
        if not self._is_valid() or self._current_token().typ != 'RBRACK':
            raise_err(EW_SYNTAX_ERROR, f'Expected closing bracket, got {self._current_token().val}')
            return None
        
        self._advance()  # 跳过右方括号
        self.paren_stack.pop()  # 退出方括号
        
        return {
            'kind': 'ListLit',
            'elements': elements
        }
    
    def _parse_table_access(self, table_expr: ASTNode) -> ASTNode:
        """解析Table访问表达式，如 table[key]"""
        clog('发现Table访问表达式')
        self._advance()  # 跳过左方括号
        
        # 解析键表达式
        key_expr = self._parse_expression()
        
        # 检查右方括号
        if not self._is_valid() or self._current_token().typ != 'RBRACK':
            raise_err(EW_SYNTAX_ERROR, f'Expected closing bracket, got {self._current_token().val}')
            return None
        
        self._advance()  # 跳过右方括号
        
        return {
            'kind': 'TableAccess',
            'table': table_expr,
            'key': key_expr
        }
    
    def _parse_package_access(self, obj_expr: ASTNode) -> ASTNode:
        """解析包访问表达式，如 package.func"""
        clog('发现包访问表达式')
        self._advance()  # 跳过点操作符
        
        # 检查方法名是否合法
        if not self._is_valid() or self._current_token().typ != 'IDENTIFIER':
            raise_err(EW_SYNTAX_ERROR, f'Expected identifier after dot, got {self._current_token().val}')
            return None
        
        # 获取方法名
        method_name = self._current_token().val
        self._advance()  # 跳过方法名
        
        # 包访问表达式可以转换为TableAccess表达式，使用字符串作为键
        return {
            'kind': 'TableAccess',
            'table': obj_expr,
            'key': {
                'kind': 'Lit',
                'type': EW_String,
                'val': EW_String(f'"{method_name}"')
            }
        }
    
    def _parse_parenthesized(self) -> MayASTNode:
        """解析括号表达式"""
        self._advance()  # 跳过左括号
        self.paren_stack.append('paren')  # 进入圆括号
        expr = self._parse_expression()
        
        # 检查并跳过可能存在的换行符
        while self._is_valid() and self._current_token().typ == 'ENDL' and self._should_ignore_endl():
            self._advance()
        
        if not self._is_valid() or self._current_token().typ != 'RPAREN':
            raise_err(EW_SYNTAX_ERROR, 'Expected closing parenthesis')
            return None
        
        self._advance()  # 跳过右括号
        self.paren_stack.pop()  # 退出圆括号
        return expr
    
    def _create_var_reference(self, identifier: Token) -> ASTNode:
        """创建变量引用节点，包含位置信息"""
        return {
            'kind': 'VarRef',
            'name': identifier.val,
            'line': identifier.line,
            'col': identifier.col,
            'code': identifier.code
        }
    
    def _peek_next(self) -> Token | None:
        """查看下一个token但不移动指针"""
        next_pos = self.current + 1
        if 0 <= next_pos < len(self.tokens):
            return self.tokens[next_pos]
        return None
    
    def _build_line_info(self, code: str) -> list[tuple[int, int]]:
        """
        构建行信息，记录每行的起始和结束位置
        
        Args:
            code: 原始代码字符串
        
        Returns:
            行信息列表，每个元素是(行起始位置, 行结束位置)
        """
        line_info = []
        start = 0
        for i, char in enumerate(code):
            if char == '\n':
                line_info.append((start, i))
                start = i + 1
        if start < len(code):
            line_info.append((start, len(code)))
        return line_info
    
    def _current_token(self) -> Token:
        """获取当前token"""
        return self.tokens[self.current] if self._is_valid() else None
    
    def _advance(self) -> None:
        """前进到下一个token"""
        self.current += 1
    
    def _is_valid(self) -> bool:
        """检查当前位置是否有效"""
        return 0 <= self.current < len(self.tokens)
    
    def _get_token_position(self) -> tuple[int, int]:
        """
        获取当前token在原始代码中的位置信息
        
        Returns:
            (行号, 行内位置)，从0开始
        """
        if not self.code or not self.line_info:
            return (-1, -1)
        
        # 简单实现：返回当前token的大致位置
        # 注意：这是一个简化实现，实际应用中可能需要更精确的位置计算
        # 我们假设每个token占一个位置，实际应该根据token在原始代码中的位置计算
        char_count = 0
        for i in range(self.current):
            if i < len(self.tokens):
                char_count += len(self.tokens[i].val)
        
        # 查找对应的行
        line = 0
        pos = 0
        for i, (start, end) in enumerate(self.line_info):
            if start <= char_count <= end:
                line = i
                pos = char_count - start
                break
        
        return (line, pos)
    
    def _should_ignore_endl(self) -> bool:
        """根据当前括号类型决定是否忽略换行符"""
        if not self.paren_stack:
            return False  # 不在任何括号内，不忽略换行符
        
        # 获取当前最内层的括号类型
        current_paren = self.paren_stack[-1]
        
        # 忽略圆括号、方括号和Table花括号内的换行符
        return current_paren in ['paren', 'bracket', 'table']  # 代码块block不忽略换行符

class Interpreter:
    """解释执行器"""
    
    def __init__(self, env: Env | None = None):
        self.env = env or GENV
    
    def run(self, ast: ASTNodelist) -> Any:
        """执行AST"""
        clog(f'函数 run({ld_show(ast)}) 开始')
        
        result = None
        for node in ast:
            clog(f'当前执行节点: {ld_show(node)}')
            result = self._execute_node(node)
        
        clog(f'函数 run({ld_show(ast)}) 结束')
        return result
    
    def _execute_node(self, node: ASTNode) -> Any:
        """执行单个AST节点"""
        node_kind = node['kind']
        handler_name = f'_execute_{node_kind.lower()}'
        handler = getattr(self, handler_name, None)
        
        if handler:
            return handler(node)
        else:
            raise_err(EW_RUNTIME_ERROR, f'Unknown node type: {node_kind}')
            return None
    
    def _execute_funcdecl(self, node: ASTNode) -> None:
        """执行函数声明，将函数绑定到当前环境"""
        clog('执行函数声明')
        
        # 获取函数名
        function_name = node['name']
        
        # 创建函数对象，传递正确的函数名
        func = EW_Function(node['params'], node['body'], self.env, function_name)
        clog(f'创建函数对象: {func}')
        
        # 应用装饰器
        if 'decorators' in node:
            for decorator in node['decorators']:
                # 执行装饰器函数，获取装饰器对象
                decorator_func = self._execute_node(decorator)
                # 应用装饰器，将函数作为参数传递给装饰器
                func = decorator_func(func)
                clog(f'应用装饰器: {decorator}, 装饰后的函数: {func}')
        
        # 将函数绑定到当前环境
        self.env[function_name] = func
        clog(f'将函数 {function_name} 绑定到环境')
        
        return None
    
    def _execute_mfuncdecl(self, node: ASTNode) -> None:
        """执行mfunc声明，将记忆化函数绑定到当前环境"""
        clog('执行mfunc声明')
        
        # 获取函数名
        function_name = node['name']
        
        # 创建记忆化函数对象，传递正确的函数名
        func = EW_MFunction(node['params'], node['body'], self.env, function_name)
        clog(f'创建记忆化函数对象: {func}')
        
        # 应用装饰器
        if 'decorators' in node:
            for decorator in node['decorators']:
                # 执行装饰器函数，获取装饰器对象
                decorator_func = self._execute_node(decorator)
                # 应用装饰器，将函数作为参数传递给装饰器
                func = decorator_func(func)
                clog(f'应用装饰器: {decorator}, 装饰后的函数: {func}')
        
        # 将函数绑定到当前环境
        self.env[function_name] = func
        clog(f'将记忆化函数 {function_name} 绑定到环境')
        
        return None
    
    def _execute_import(self, node: ASTNode) -> None:
        """执行import语句，导入包"""
        clog('执行import语句')
        
        package_name = node['name']
        
        # 导入包
        import_package(package_name, self.env)
        
        clog(f'导入包: {package_name}')
        return None
    
    def _execute_doexpr(self, node: ASTNode) -> 'EW_Function':
        """执行do表达式，返回函数对象"""
        clog('执行do表达式')
        
        # 创建函数对象，使用默认名称
        func = EW_Function(node['params'], node['body'], self.env)
        clog(f'创建函数对象: {func}')
        
        return func
    
    def _execute_return(self, node: ASTNode) -> ASTNode:
        """执行return语句"""
        clog('执行return语句')
        
        value = None
        if node['value']:
            value = self._execute_node(node['value'])
        
        clog(f'return值: {value}')
        return {
            'kind': 'ReturnValue',
            'value': value
        }
    
    def _execute_if(self, node: ASTNode) -> Any:
        """执行if语句"""
        clog('执行if语句')
        
        # 计算条件
        condition = self._execute_node(node['condition'])
        clog(f'if条件结果: {condition}')
        
        # 判断条件是否为真
        if condition:
            clog('执行if分支')
            result = None
            for stmt in node['if_body']:
                result = self._execute_node(stmt)
                # 检查是否有return语句
                if isinstance(result, dict) and result.get('kind') == 'ReturnValue':
                    return result
            return result
        elif node['else_body']:
            clog('执行else分支')
            result = None
            for stmt in node['else_body']:
                result = self._execute_node(stmt)
                # 检查是否有return语句
                if isinstance(result, dict) and result.get('kind') == 'ReturnValue':
                    return result
            return result
        else:
            clog('条件为假且无else分支，返回None')
            return None
    
    def _execute_varassign(self, node: ASTNode) -> None:
        """执行变量赋值"""
        variable_name = node['name']
        value = self._execute_node(node['value'])
        
        clog(f'将变量 {variable_name} 赋值为 {value}')
        self.env[variable_name] = value
        clog(f'当前环境: {ld_show(self.env[variable_name])}')
    
    def _execute_tableassign(self, node: ASTNode) -> None:
        """执行Table或列表赋值，如 table[key] = value 或 list[index] = value"""
        clog('执行Table/List赋值')
        
        # 执行对象表达式
        obj = self._execute_node(node['table'])
        
        # 执行键/索引表达式
        key = self._execute_node(node['key'])
        
        # 执行值表达式
        value = self._execute_node(node['value'])
        
        # 检查对象类型
        if isinstance(obj, EW_Table):
            # Table赋值
            obj[key] = value
            clog(f'Table赋值: {obj}[{key}] = {value}')
        elif isinstance(obj, EW_List):
            # 列表赋值
            # 检查索引类型
            if not isinstance(key, EW_Number) or not key._isint():
                raise_err(EW_RUNTIME_ERROR, f'List index must be an integer, got {type(key).__name__}')
                return None
            
            # 转换为Python整数索引
            index = int(key._decimal)
            
            # 检查索引范围
            if index < 0 or index >= len(obj.value):
                raise_err(EW_RUNTIME_ERROR, f'List index out of range: {index}')
                return None
            
            # 执行赋值
            obj.value[index] = value
            clog(f'List赋值: {obj}[{index}] = {value}')
        else:
            raise_err(EW_RUNTIME_ERROR, f'Expected Table or List, got {type(obj).__name__}')
            return None
    
    def _execute_whilestatement(self, node: ASTNode) -> None:
        """执行while循环语句"""
        while True:
            condition = self._execute_node(node['condition'])
            if not condition:
                break
            
            for stmt in node['body']:
                result = self._execute_node(stmt)
                
                if isinstance(result, dict) and result.get('kind') == 'ReturnValue':
                    return result

    def _execute_funccall(self, node: ASTNode) -> Any:
        """执行函数调用"""
        # 获取函数表达式
        func_expr = node['func']
        
        # 执行函数表达式来获取函数对象
        function = self._execute_node(func_expr)
        
        if function is None:
            raise_err(EW_RUNTIME_ERROR, 'Function expression returned None')
            return None
        
        # 解析参数 - 直接获取参数列表
        args = [self._execute_node(arg) for arg in node['args']]
        
        clog(f'调用函数: {func_expr}')
        clog(f'参数列表: {args} (长度: {len(args)})')
        clog(f'函数类型: {type(function)}')
        
        # 执行函数
        if isinstance(function, (EW_Function, EW_MFunction)):
            expected = len(function.params)
            got = len(args)
            if got != expected:
                raise_err(EW_RUNTIME_ERROR,
                          f'Function expects {expected} arguments but got {got}')
                return None
            # 参数数量正确，执行自定义函数
            result = self._execute_custom_function(function, args)
        elif callable(function):
            # 对于内置函数和包函数，仍用 try/except 兜底，但优先检查签名
            try:
                result = function(*args)
            except TypeError as e:
                # 仅捕获参数数量不匹配
                if "takes" in str(e) and "arguments" in str(e):
                    raise_err(EW_RUNTIME_ERROR,
                              f'The amount of the arguments is not correct: {e}')
                else:
                    raise_err(EW_RUNTIME_ERROR, f'Function calling error: {e}')
                return None
        else:
            # 非可调用对象
            raise_err(EW_RUNTIME_ERROR, f'Literal {function} is not callable')
            return None

        clog(f'函数调用完成: 结果: {result}')
        return result
    
    def _execute_custom_function(self, func: 'EW_Function | EW_MFunction', args: list[Any]) -> Any:
        """执行自定义函数"""
        clog(f'执行自定义函数: {func}')
        
        # 检查参数数量
        if len(args) != len(func.params):
            raise_err(EW_RUNTIME_ERROR, 
                    f'Function expects {len(func.params)} arguments but got {len(args)}')
            return None
        
        # 检查是否是记忆化函数
        is_mfunc = isinstance(func, EW_MFunction)
        
        # 生成缓存键 - 使用对象本身作为哈希键，因为EW_Number已经实现了__hash__方法
        cache_key = tuple(arg for arg in args)
        
        # 如果是记忆化函数，检查缓存
        if is_mfunc and cache_key in func._cache:
            clog(f'从缓存中获取结果: {func._cache[cache_key]}')
            return func._cache[cache_key]
        
        # 创建新的作用域，继承自函数定义时的环境
        new_env = Env()
        # 复制原环境中的所有变量
        for key, value in func.env.vals.items():
            new_env[key] = value
        clog(f'新建作用域: {new_env}')
        
        # 绑定参数
        for param_name, arg_value in zip(func.params, args):
            new_env[param_name] = arg_value
            clog(f'绑定参数: {param_name} = {arg_value}')
        
        # 在新的作用域中执行函数体
        old_env = self.env
        self.env = new_env
        
        result = None
        try:
            # 将函数调用压入调用栈
            push_stack(func.name if hasattr(func, 'name') and func.name else '<anonymous>')
            
            for stmt in func.body:
                stmt_result = self._execute_node(stmt)
                # 检查是否有return语句
                if isinstance(stmt_result, dict) and stmt_result.get('kind') == 'ReturnValue':
                    result = stmt_result['value']
                    break
                else:
                    result = stmt_result
        finally:
            # 从调用栈中弹出函数调用
            pop_stack()
            
            # 恢复原来的环境
            self.env = old_env
        
        # 如果是记忆化函数，缓存结果
        if is_mfunc:
            func._cache[cache_key] = result
            clog(f'缓存结果: {result}')
        
        clog(f'自定义函数执行完成，结果: {result}')
        return result

    def _execute_lit(self, node: ASTNode) -> Any:
        """执行字面量"""
        clog(f'字面量: {node["val"]}')
        return node['val']
    
    def _execute_varref(self, node: ASTNode) -> Any:
        """执行变量引用"""
        variable_name = node['name']
        clog(f'引用变量: {variable_name}')
        
        if variable_name not in self.env:
            # 使用节点中的位置信息调用raise_err
            line = node.get('line')
            col = node.get('col')
            code = node.get('code')
            raise_err(EW_RUNTIME_ERROR, f'Undefined variable: {variable_name}', 
                      line=line, code=code, pos=col)
        
        value = self.env[variable_name]
        clog(f'引用指向的值: {value}')
        return value
    
    def _execute_operator(self, node: ASTNode) -> Any:
        """执行操作符运算，手动实现运算逻辑，不依赖Python的运算符重载"""
        operator = node['operator']
        left_value = self._execute_node(node['left'])
        right_value = self._execute_node(node['right'])
        
        clog(f'运算符运算: {left_value} {operator} {right_value}')
        
        # 手动实现运算逻辑
        result = None
        
        # 处理算术运算符
        if operator in ['+', '-', '*', '/', '**']:
            # 确保操作数是数字类型
            if not isinstance(left_value, EW_Number) or not isinstance(right_value, EW_Number):
                raise_err(EW_TYPE_ERROR, f'Invalid operand types for {operator}: {type(left_value).__name__} and {type(right_value).__name__}')
                return None
            
            # 提取内部Decimal值进行手动运算
            left_dec = left_value._decimal
            right_dec = right_value._decimal
            
            match operator:
                case '+':
                    result = EW_Number(str(left_dec + right_dec))
                case '-':
                    result = EW_Number(str(left_dec - right_dec))
                case '*':
                    result = EW_Number(str(left_dec * right_dec))
                case '/':
                    if right_dec == 0:
                        raise_err(EW_RUNTIME_ERROR, 'Division by zero')
                        return None
                    result = EW_Number(str(left_dec / right_dec))
                case '**':
                    # 确保指数是整数
                    if not right_value._isint():
                        raise_err(EW_TYPE_ERROR, f'Exponent must be an integer for {operator}')
                        return None
                    exponent = int(right_dec)
                    result = EW_Number(str(left_dec ** exponent))
        
        # 处理比较运算符
        elif operator in ['==', '!=', '<', '>', '<=', '>=']:
            # 支持数值比较
            if isinstance(left_value, EW_Number) and isinstance(right_value, EW_Number):
                left_dec = left_value._decimal
                right_dec = right_value._decimal
                
                match operator:
                    case '==':
                        result = EW_Boolean(left_dec == right_dec)
                    case '!=':
                        result = EW_Boolean(left_dec != right_dec)
                    case '<':
                        result = EW_Boolean(left_dec < right_dec)
                    case '>':
                        result = EW_Boolean(left_dec > right_dec)
                    case '<=':
                        result = EW_Boolean(left_dec <= right_dec)
                    case '>=':
                        result = EW_Boolean(left_dec >= right_dec)
            # 支持布尔值比较
            elif isinstance(left_value, EW_Boolean) and isinstance(right_value, EW_Boolean):
                left_bool = bool(left_value)
                right_bool = bool(right_value)
                
                match operator:
                    case '==':
                        result = EW_Boolean(left_bool == right_bool)
                    case '!=':
                        result = EW_Boolean(left_bool != right_bool)
            # 支持字符串比较
            elif isinstance(left_value, EW_String) and isinstance(right_value, EW_String):
                left_str = left_value.value
                right_str = right_value.value
                
                match operator:
                    case '==':
                        result = EW_Boolean(left_str == right_str)
                    case '!=':
                        result = EW_Boolean(left_str != right_str)
                    case '<':
                        result = EW_Boolean(left_str < right_str)
                    case '>':
                        result = EW_Boolean(left_str > right_str)
                    case '<=':
                        result = EW_Boolean(left_str <= right_str)
                    case '>=':
                        result = EW_Boolean(left_str >= right_str)
            else:
                # 不同类型比较总是False
                match operator:
                    case '==':
                        result = EW_Boolean(False)
                    case '!=':
                        result = EW_Boolean(True)
                    case _:
                        raise_err(EW_TYPE_ERROR, f'Cannot compare {type(left_value).__name__} and {type(right_value).__name__} with {operator}')
                        return None
        
        # 处理逻辑运算符
        elif operator in ['and', 'or']:
            left_bool = bool(left_value)
            
            match operator:
                case 'and':
                    # 短路求值
                    if not left_bool:
                        result = EW_Boolean(False)
                    else:
                        result = EW_Boolean(bool(right_value))
                case 'or':
                    # 短路求值
                    if left_bool:
                        result = EW_Boolean(True)
                    else:
                        result = EW_Boolean(bool(right_value))
        
        # 处理字符串拼接（+）
        elif operator == '+' and isinstance(left_value, EW_String) and isinstance(right_value, EW_String):
            result = EW_String(left_value.value + right_value.value, without_quote=False)
        
        # 未知运算符
        else:
            raise_err(EW_RUNTIME_ERROR, f'Unsupported operator: {operator}')
            return None
        
        clog(f'运算结果: {result}')
        return result
    
    def _execute_tablelit(self, node: ASTNode) -> 'EW_Table':
        """执行Table字面量，创建EW_Table对象"""
        clog('执行Table字面量')
        
        # 创建空Table
        table = EW_Table()
        
        # 执行键值对并添加到Table中
        for key_expr, value_expr in node['pairs']:
            # 执行键表达式
            key = self._execute_node(key_expr)
            # 执行值表达式
            value = self._execute_node(value_expr)
            # 添加到Table
            table[key] = value
        
        clog(f'创建Table: {table}')
        return table
    
    def _execute_listlit(self, node: ASTNode) -> 'EW_List':
        """执行列表字面量，创建EW_List对象"""
        clog('执行List字面量')
        
        # 创建空列表
        lst = EW_List()
        
        # 执行元素表达式并添加到列表中
        for element_expr in node['elements']:
            # 执行元素表达式
            element = self._execute_node(element_expr)
            # 添加到列表
            lst.value.append(element)
        
        clog(f'创建List: {lst}')
        return lst
    
    def _execute_tableaccess(self, node: ASTNode) -> Any:
        """执行Table、列表或包访问，获取指定键、索引或函数的值"""
        clog('执行Table/List/Package访问')
        
        # 执行对象表达式
        obj = self._execute_node(node['table'])
        
        # 执行键/索引表达式
        key = self._execute_node(node['key'])
        
        clog(f'访问对象: {obj}, 键/索引: {key}')
        
        # 检查对象类型
        if isinstance(obj, EW_Table):
            # Table访问
            try:
                value = obj[key]
            except KeyError:
                raise_err(EW_RUNTIME_ERROR, f'Key not found in Table: {key}')
                return None
        elif isinstance(obj, EW_List):
            # 列表访问
            # 检查索引类型
            if not isinstance(key, EW_Number) or not key._isint():
                raise_err(EW_RUNTIME_ERROR, f'List index must be an integer, got {type(key).__name__}')
                return None
            
            # 转换为Python整数索引
            index = int(key._decimal)
            
            # 检查索引范围
            if index < 0 or index >= len(obj.value):
                raise_err(EW_RUNTIME_ERROR, f'List index out of range: {index}')
                return None
            
            value = obj.value[index]
        elif isinstance(obj, EW_Package):
            # 包访问
            try:
                value = obj[key]
            except KeyError:
                raise_err(EW_RUNTIME_ERROR, f'Function {key} not found in package {obj.name}')
                return None
        else:
            raise_err(EW_RUNTIME_ERROR, f'Expected Table, List or Package, got {type(obj).__name__}')
            return None
        
        clog(f'访问结果: {value}')
        return value


# 全局环境
EW_BUILTINS = Env(
    **ew_builtins
)
GENV = EW_BUILTINS

# 自动加载所有包搜索路径下的所有包
auto_load_all_packages()

# 将加载的包添加到全局环境
for package_name, package in packages.items():
    GENV[package_name] = package


def parse(tokens: list[Token], code: str = None) -> ASTNodelist:
    """解析tokens为AST (兼容旧接口)"""
    return Parser(tokens, code).parse()


def run(ast: ASTNodelist, env: Env | None = None) -> Any:
    """执行AST (兼容旧接口)"""
    return Interpreter(env).run(ast)

def directly_run(code):
    """直接运行代码字符串"""
    lexer = Lexer()
    tokens = lexer.tokenize(code)
    ast = parse(tokens, code)
    return run(ast)

if __name__ == "__main__":
    code = r'''
import math
'''
    directly_run(code)