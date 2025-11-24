from decimal import Decimal, getcontext
from fractions import Fraction
import re
from typing import Any
from Env import Env
from Error import clog

# 设置高精度计算环境
getcontext().prec = 100  # 设置100位精度

class EW_Type:
    def __init__(self, value):
        self.value = value
    
    def __repr__(self):
        return str(self.value)

class EW_Number(EW_Type):
    def __init__(self, value):
        if isinstance(value, (int, float, str)):
            self.value = Decimal(str(value))
        elif isinstance(value, Decimal):
            self.value = value
        elif isinstance(value, Fraction):
            self.value = Decimal(value.numerator) / Decimal(value.denominator)
        else:
            raise ValueError(f"Unsupported type for EW_Number: {type(value)}")
    
    def _detect_repeating_decimal(self):
        """检测循环小数并返回字符串表示"""
        if self.value == 0:
            return "0"
        
        # 转换为分数来检测循环节
        try:
            # 尝试将Decimal转换为分数
            frac = Fraction(float(self.value)).limit_denominator(1000000)
            numerator, denominator = frac.numerator, frac.denominator
            
            # 检查分母是否只有2和5的因子（有限小数）
            temp = denominator
            while temp % 2 == 0:
                temp //= 2
            while temp % 5 == 0:
                temp //= 5
            
            if temp == 1:
                # 有限小数
                return str(self.value)
            else:
                # 循环小数，手动计算循环节
                return self._find_repeating_sequence()
        except:
            return str(self.value)
    
    def _find_repeating_sequence(self):
        """查找循环节"""
        num_str = str(self.value)
        if '.' not in num_str:
            return num_str
        
        # 分离整数和小数部分
        integer_part, decimal_part = num_str.split('.')
        
        # 对于简单情况，直接检查
        if decimal_part.count(decimal_part[0]) == len(decimal_part):
            # 所有小数位都相同
            repeating_digit = decimal_part[0]
            if repeating_digit == '0':
                return integer_part
            else:
                return f"{integer_part}.({repeating_digit})"
        
        # 更复杂的循环节检测
        for length in range(1, len(decimal_part) // 2 + 1):
            for i in range(len(decimal_part) - length * 2 + 1):
                pattern = decimal_part[i:i+length]
                if decimal_part[i+length:].startswith(pattern):
                    # 找到循环节
                    non_repeating = decimal_part[:i]
                    if non_repeating:
                        return f"{integer_part}.{non_repeating}({pattern})"
                    else:
                        return f"{integer_part}.({pattern})"
        
        return num_str
    
    def __repr__(self):
        repeating_repr = self._detect_repeating_decimal()
        return repeating_repr

    def __add__(self, other):
        if isinstance(other, EW_Number):
            return EW_Number(self.value + other.value)
        else:
            return NotImplemented
    
    def __mul__(self, other):
        if isinstance(other, EW_Number):
            return EW_Number(self.value * other.value)
        else:
            return NotImplemented
    
    def __sub__(self, other):
        if isinstance(other, EW_Number):
            return EW_Number(self.value - other.value)
        else:
            return NotImplemented

    def __truediv__(self, other):
        if isinstance(other, EW_Number):
            if other.value == 0:
                raise ZeroDivisionError("Division by zero")
            return EW_Number(self.value / other.value)
        else:
            return NotImplemented

    def __eq__(self, other):
        if isinstance(other, EW_Number):
            return EW_Boolean(self.value == other.value)
        else:
            return NotImplemented
    
    def __lt__(self, other):
        if isinstance(other, EW_Number):
            return EW_Boolean(self.value < other.value)
        else:
            return NotImplemented

    def __gt__(self, other):
        if isinstance(other, EW_Number):
            return EW_Boolean(self.value > other.value)
        else:
            return NotImplemented
    
    def __le__(self, other):
        if isinstance(other, EW_Number):
            return EW_Boolean(self.value <= other.value)
        else:
            return NotImplemented
    
    def __ge__(self, other):
        if isinstance(other, EW_Number):
            return EW_Boolean(self.value >= other.value)
        else:
            return NotImplemented
    
    def __pow__(self, other):
        if isinstance(other, EW_Number):
            return EW_Number(self.value ** other.value)
        else:
            return NotImplemented

class EW_String(EW_Type):
    def __init__(self, value, without_quote=True):
        if without_quote:
            self.value = value[1:-1]  # 舍弃左右的引号
            clog(f"Removed quotes from string: {self.value}")
        else:
            self.value = value
            clog(f"String: {self.value}")

    def __add__(self, other):
        if isinstance(other, EW_String):
            return EW_String(self.value + other.value, without_quote=False)
        else:
            return NotImplemented
    
    def __repr__(self):
        return f'{self.value}'

class EW_Boolean(EW_Type):
    def __repr__(self):
        return "true" if self.value else "false"

class EW_Function:
    """函数类型"""
    
    def __init__(self, params: list[str], body: list[dict[str, Any]], env: Env):
        self.params = params
        self.body = body
        self.env = env
        self.name = "do_func"  # 可以为匿名函数设置默认名称
    
    def __call__(self, *args):
        # 函数调用逻辑将在解释器中实现
        return self
    
    def __str__(self):
        return f"<function {self.name} at {hex(id(self))}>"
    
    def __repr__(self):
        return self.__str__()

# 测试代码
if __name__ == "__main__":
    # 测试基本运算
    a = EW_Number(2)
    b = EW_Number(3)
    print(f"2 / 3 = {a/b}")  # 应该显示 0.(6) 或类似表示
    
    # 测试更多例子
    c = EW_Number(1)
    d = EW_Number(7)
    print(f"1 / 7 = {c/d}")  # 循环小数 0.(142857)
    
    e = EW_Number(1)
    f = EW_Number(2)
    print(f"1 / 2 = {e/f}")  # 有限小数 0.5
    
    # 测试高精度
    g = EW_Number("0.33333333333333333333333333333333333333")
    print(f"0.33... = {g}")  # 应该识别为 0.(3)
    
    # 测试比较运算
    print(f"2 == 3: {a == b}")
    print(f"2 < 3: {a < b}")