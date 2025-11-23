from Lexer import *
from Token import *
from Env import *
from Type import *
from typing import List, Dict, Any, Optional, Union
from ew_builtins import ew_builtins

class Parser:
    """语法解析器"""
    
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.current = 0
        self.ast = []
    
    def parse(self) -> List[Dict[str, Any]]:
        """解析token序列为AST"""
        clog(f'函数 parse({ld_show(self.tokens)}) 开始')
        
        while self._is_valid():
            clog(f'当前位于 token #{self.current}: {self._current_token()}')
            node = self._parse_statement()
            if node:
                self.ast.append(node)
        
        clog('函数 parse 结束')
        return self.ast
    
    def _parse_statement(self) -> Optional[Dict[str, Any]]:
        """解析语句"""
        token = self._current_token()
        
        if token.typ == 'IF':
            return self._parse_if_statement()
        elif token.typ == 'RETURN':
            return self._parse_return_statement()
        elif token.typ == 'IDENTIFIER':
            # 检查是否是赋值语句
            if self._peek_next() and self._peek_next().typ == 'ASSIGN':
                return self._parse_assignment()
            else:
                return self._parse_expression()
        else:
            return self._parse_expression()
    
    def _parse_return_statement(self) -> Dict[str, Any]:
        """解析return语句"""
        clog('发现return语句')
        self._advance()  # 跳过 'return'
        
        # 解析返回值表达式
        value = None
        if self._is_valid() and self._current_token().typ != 'SEMICOLON':
            value = self._parse_expression()
        
        # 跳过分号（如果存在）
        if self._is_valid() and self._current_token().typ == 'SEMICOLON':
            self._advance()
        
        clog(f'return语句解析完成: 返回值={value}')
        return {
            'kind': 'Return',
            'value': value
        }
    
    def _parse_if_statement(self) -> Dict[str, Any]:
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
        
        # 解析可选的else分支
        else_body = None
        if self._is_valid() and self._current_token().typ == 'ELSE':
            self._advance()  # 跳过 'else'
            
            if not self._is_valid() or self._current_token().typ != 'LBRACE':
                raise_err(EW_SYNTAX_ERROR, 'Expected "{" after "else"')
                return None
            
            self._advance()  # 跳过 '{'
            else_body = self._parse_block()
            
            if not self._is_valid() or self._current_token().typ != 'RBRACE':
                raise_err(EW_SYNTAX_ERROR, 'Expected "}" after else body')
                return None
            
            self._advance()  # 跳过 '}'
        
        clog(f'if语句解析完成: 条件={condition}, if分支长度={len(if_body)}, else分支长度={0 if else_body is None else len(else_body)}')
        return {
            'kind': 'If',
            'condition': condition,
            'if_body': if_body,
            'else_body': else_body
        }
    
    def _parse_block(self) -> List[Dict[str, Any]]:
        """解析代码块（大括号内的语句序列）"""
        block = []
        
        while self._is_valid() and self._current_token().typ != 'RBRACE':
            node = self._parse_statement()
            if node:
                block.append(node)
        
        return block
    
    def _parse_expression(self) -> Optional[Dict[str, Any]]:
        """解析表达式"""
        return self._parse_operator_expression()
    
    def _parse_operator_expression(self) -> Optional[Dict[str, Any]]:
        """解析操作符表达式"""
        left = self._parse_primary()
        
        # 支持的运算符
        operators = ['+', '-', '*', '/', '==', '!=', '<', '>', '<=', '>=', 'and', 'or', '**']
        
        while (self._is_valid() and 
               self._current_token().typ == 'OPERATOR' and 
               self._current_token().val in operators):
            
            operator = self._current_token()
            self._advance()
            right = self._parse_primary()
            
            left = {
                'kind': 'Operator',
                'operator': operator.val,
                'left': left,
                'right': right
            }
        
        return left
    
    def _parse_primary(self) -> Optional[Dict[str, Any]]:
        """解析基本表达式"""
        token = self._current_token()
        
        if token.typ == 'IDENTIFIER':
            return self._parse_identifier_expr()
        elif token.typ in ('NUMBER', 'STRING'):
            return self._parse_literal()
        elif token.typ == 'LPAREN':
            return self._parse_parenthesized()
        elif token.typ == 'DO':
            return self._parse_do_expression()
        else:
            clog(f'当前的Token类型为: {token.typ}, 未知')
            raise_err(EW_SYNTAX_ERROR, f'Unexpected token: {token}')
            return None
    
    def _parse_do_expression(self) -> Dict[str, Any]:
        """解析do表达式"""
        clog('发现do表达式')
        self._advance()  # 跳过 'do'
        
        # 解析参数列表
        params = []
        if self._is_valid() and self._current_token().typ == 'LPAREN':
            self._advance()  # 跳过 '('
            
            # 如果有参数
            if self._is_valid() and self._current_token().typ == 'IDENTIFIER':
                params.append(self._current_token().val)
                self._advance()
                
                # 解析多个参数
                while self._is_valid() and self._current_token().typ == 'COMMA':
                    self._advance()  # 跳过 ','
                    if self._is_valid() and self._current_token().typ == 'IDENTIFIER':
                        params.append(self._current_token().val)
                        self._advance()
                    else:
                        raise_err(EW_SYNTAX_ERROR, 'Expected parameter name after comma')
                        return None
            
            if not self._is_valid() or self._current_token().typ != 'RPAREN':
                raise_err(EW_SYNTAX_ERROR, 'Expected ")" after parameters')
                return None
            
            self._advance()  # 跳过 ')'
        
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
    
    def _parse_identifier_expr(self) -> Dict[str, Any]:
        """解析标识符表达式（变量引用或函数调用）"""
        identifier = self._current_token()
        
        # 检查是否是函数调用
        if self._peek_next() and self._peek_next().typ == 'LPAREN':
            return self._parse_function_call(identifier)
        else:
            self._advance()  # 只有变量引用时才前进
            return self._create_var_reference(identifier)
    
    def _parse_assignment(self) -> Dict[str, Any]:
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
        
        # 跳过分号（如果存在）
        if self._is_valid() and self._current_token().typ == 'SEMICOLON':
            self._advance()
        
        clog(f'赋值: {identifier.val} = {value}')
        return {
            'kind': 'VarAssign',
            'name': identifier.val,
            'value': value
        }
    
    def _parse_function_call(self, identifier: Token) -> Dict[str, Any]:
        """解析函数调用"""
        clog('发现函数调用')
        self._advance()  # 跳过标识符
        self._advance()  # 跳过左括号
        
        args = []
        
        # 如果右括号紧跟着，说明没有参数
        if self._is_valid() and self._current_token().typ == 'RPAREN':
            self._advance()  # 跳过右括号
            clog(f'函数调用: {identifier.val}, 无参数')
            return {
                'kind': 'FuncCall',
                'name': identifier.val,
                'args': args  # 空列表
            }
        
        # 解析第一个参数
        arg = self._parse_expression()
        if arg:
            args.append(arg)
        
        # 解析后续参数（必须有逗号分隔）
        while self._is_valid() and self._current_token().typ == 'COMMA':
            self._advance()  # 跳过逗号
            
            # 逗号后面必须有参数
            if not self._is_valid() or self._current_token().typ == 'RPAREN':
                raise_err(EW_SYNTAX_ERROR, 'Expected argument after comma')
                return None
            
            arg = self._parse_expression()
            if arg:
                args.append(arg)
        
        # 检查右括号
        if not self._is_valid() or self._current_token().typ != 'RPAREN':
            raise_err(EW_SYNTAX_ERROR, 'Expected closing parenthesis')
            return None
        
        self._advance()  # 跳过右括号
        
        # 跳过分号（如果存在）
        if self._is_valid() and self._current_token().typ == 'SEMICOLON':
            self._advance()
        
        clog(f'函数调用: {identifier.val}, 参数数量: {len(args)}')
        return {
            'kind': 'FuncCall',
            'name': identifier.val,
            'args': args  # 直接返回参数列表
        }
    
    def _parse_literal(self) -> Dict[str, Any]:
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
    
    def _parse_parenthesized(self) -> Optional[Dict[str, Any]]:
        """解析括号表达式"""
        self._advance()  # 跳过左括号
        expr = self._parse_expression()
        
        if not self._is_valid() or self._current_token().typ != 'RPAREN':
            raise_err(EW_SYNTAX_ERROR, 'Expected closing parenthesis')
            return None
        
        self._advance()  # 跳过右括号
        return expr
    
    def _create_var_reference(self, identifier: Token) -> Dict[str, Any]:
        """创建变量引用节点"""
        return {
            'kind': 'VarRef',
            'name': identifier.val
        }
    
    def _peek_next(self) -> Optional[Token]:
        """查看下一个token但不移动指针"""
        next_pos = self.current + 1
        if 0 <= next_pos < len(self.tokens):
            return self.tokens[next_pos]
        return None
    
    def _current_token(self) -> Token:
        """获取当前token"""
        return self.tokens[self.current]
    
    def _advance(self) -> None:
        """前进到下一个token"""
        self.current += 1
    
    def _is_valid(self) -> bool:
        """检查当前位置是否有效"""
        return 0 <= self.current < len(self.tokens)


class Interpreter:
    """解释执行器"""
    
    def __init__(self, env: Optional[Env] = None):
        self.env = env or GENV
    
    def run(self, ast: List[Dict[str, Any]]) -> Any:
        """执行AST"""
        clog(f'函数 run({ld_show(ast)}) 开始')
        
        result = None
        for node in ast:
            clog(f'当前执行节点: {ld_show(node)}')
            result = self._execute_node(node)
        
        clog(f'函数 run({ld_show(ast)}) 结束')
        return result
    
    def _execute_node(self, node: Dict[str, Any]) -> Any:
        """执行单个AST节点"""
        node_kind = node['kind']
        handler_name = f'_execute_{node_kind.lower()}'
        handler = getattr(self, handler_name, None)
        
        if handler:
            return handler(node)
        else:
            raise_err(EW_RUNTIME_ERROR, f'Unknown node type: {node_kind}')
            return None
    
    def _execute_doexpr(self, node: Dict[str, Any]) -> 'EW_Function':
        """执行do表达式，返回函数对象"""
        clog('执行do表达式')
        
        # 创建函数对象
        func = EW_Function(node['params'], node['body'], self.env)
        clog(f'创建函数对象: {func}')
        
        return func
    
    def _execute_return(self, node: Dict[str, Any]) -> Dict[str, Any]:
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
    
    def _execute_if(self, node: Dict[str, Any]) -> Any:
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
    
    def _execute_varassign(self, node: Dict[str, Any]) -> None:
        """执行变量赋值"""
        variable_name = node['name']
        value = self._execute_node(node['value'])
        
        clog(f'将变量 {variable_name} 赋值为 {value}')
        self.env[variable_name] = value
        clog(f'当前环境: {ld_show(self.env[variable_name])}')
    
    def _execute_funccall(self, node: Dict[str, Any]) -> Any:
        """执行函数调用"""
        function_name = node['name']
        
        # 检查函数是否存在
        if function_name not in self.env:
            raise_err(EW_RUNTIME_ERROR, f'Undefined function: {function_name}')
            return None
        
        function = self.env[function_name]
        
        # 解析参数 - 直接获取参数列表
        args = [self._execute_node(arg) for arg in node['args']]
        
        clog(f'调用函数 {function_name}')
        clog(f'参数列表: {args} (长度: {len(args)})')
        clog(f'函数类型: {type(function)}')
        
        # 执行函数
        try:
            if isinstance(function, EW_Function):
                # 处理自定义函数
                result = self._execute_custom_function(function, args)
            elif callable(function):
                result = function(*args)
            else:
                result = function
            
            clog(f'函数调用完成: {function_name}, 结果: {result}')
            return result
        except TypeError as e:
            # 处理参数数量不匹配的错误
            error_msg = str(e)
            if "takes" in error_msg and "arguments" in error_msg:
                raise_err(EW_RUNTIME_ERROR, f'The amount of the arguments of the function {function_name} is not correct: {error_msg}')
            else:
                raise_err(EW_RUNTIME_ERROR, f'Function calling error: {error_msg}')
            return None
        except Exception as e:
            raise_err(EW_RUNTIME_ERROR, f'Function calling error: {e}')
            return None
    
    def _execute_custom_function(self, func: 'EW_Function', args: List[Any]) -> Any:
        """执行自定义函数"""
        clog(f'执行自定义函数: {func}')
        
        # 检查参数数量
        if len(args) != len(func.params):
            raise_err(EW_RUNTIME_ERROR, 
                    f'Function expects {len(func.params)} arguments but got {len(args)}')
            return None
        
        # 创建新的作用域，但继承函数定义时的环境
        new_env = func.env
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
            for stmt in func.body:
                stmt_result = self._execute_node(stmt)
                # 检查是否有return语句
                if isinstance(stmt_result, dict) and stmt_result.get('kind') == 'ReturnValue':
                    result = stmt_result['value']
                    break
                else:
                    result = stmt_result
        finally:
            # 恢复原来的环境
            self.env = old_env
        
        clog(f'自定义函数执行完成，结果: {result}')
        return result

    def _execute_lit(self, node: Dict[str, Any]) -> Any:
        """执行字面量"""
        clog(f'字面量: {node["val"]}')
        return node['val']
    
    def _execute_varref(self, node: Dict[str, Any]) -> Any:
        """执行变量引用"""
        variable_name = node['name']
        clog(f'引用变量: {variable_name}')
        
        if variable_name not in self.env:
            raise_err(EW_RUNTIME_ERROR, f'Undefined variable: {variable_name}')
        
        value = self.env[variable_name]
        clog(f'引用指向的值: {value}')
        return value
    
    def _execute_operator(self, node: Dict[str, Any]) -> Any:
        """执行操作符运算"""
        operator = node['operator']
        left_value = self._execute_node(node['left'])
        right_value = self._execute_node(node['right'])
        
        clog(f'运算符运算: {left_value} {operator} {right_value}')
        
        # 根据操作符执行相应的运算
        if operator == '+':
            result = left_value + right_value
        elif operator == '-':
            result = left_value - right_value
        elif operator == '*':
            result = left_value * right_value
        elif operator == '/':
            if right_value == 0:
                raise_err(EW_RUNTIME_ERROR, 'Division by zero')
                return None
            result = left_value / right_value
        elif operator == '==':
            result = left_value == right_value
        elif operator == '!=':
            result = left_value != right_value
        elif operator == '<':
            result = left_value < right_value
        elif operator == '>':
            result = left_value > right_value
        elif operator == '<=':
            result = left_value <= right_value
        elif operator == '>=':
            result = left_value >= right_value
        elif operator == 'and':
            result = left_value and right_value
        elif operator == 'or':
            result = left_value or right_value
        elif operator == '**':
            result = left_value ** right_value
        else:
            raise_err(EW_RUNTIME_ERROR, f'Unsupported operator: {operator}')
            return None
        
        clog(f'运算结果: {result}')
        return result


# 全局环境
EW_BUILTINS = Env(
    **ew_builtins
)
GENV = EW_BUILTINS


def parse(tokens: List[Token]) -> List[Dict[str, Any]]:
    """解析tokens为AST (兼容旧接口)"""
    return Parser(tokens).parse()


def run(ast: List[Dict[str, Any]], env: Optional[Env] = None) -> Any:
    """执行AST (兼容旧接口)"""
    return Interpreter(env).run(ast)


if __name__ == "__main__":
    clog("测试 Parser.py - 包含do表达式")
    
    # 测试do表达式
    code = '''
    a = do (x) {
        print('Hi!')
        return x + 1
    }
    result = a(1);
    print(result);
    print(a);
    '''
    
    lexer = Lexer()
    tokens = lexer.tokenize(code)
    ast = parse(tokens)
    result = run(ast)
    
    clog(f'最终结果: {result}')