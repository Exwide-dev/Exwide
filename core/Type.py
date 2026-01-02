from decimal import Decimal, getcontext
from fractions import Fraction
import re
from typing import Any
from core.Env import Env
from core.Error import EW_TYPE_ERROR, clog, ld_show

# 设置高精度计算环境
getcontext().prec = 100  # 设置100位精度

class EW_Type:
    def __init__(self, value):
        self.value = value
    
    def __repr__(self):
        return str(self.value)

class EW_Number(EW_Type):
    """高精度数字类型，使用Decimal库实现"""
    
    def __init__(self, value):
        """初始化高精度数字
        
        Args:
            value: 字符串或数字，表示要创建的高精度数字
        """
        # 转换为字符串处理
        if isinstance(value, (int, float, Decimal)):
            value = str(value)
        elif not isinstance(value, str):
            raise ValueError(f"Unsupported type for EW_Number: {type(value)}")
        
        # 保存原始字符串表示，用于检测循环小数
        self._original_str = value
        
        # 处理循环小数语法，如0.(3)...
        self._is_repeating = False
        self._repeating_part = ''
        
        # 检查是否是循环小数语法
        if '(' in value and ')...' in value:
            self._is_repeating = True
            # 提取循环节
            self._repeating_part = value.split('(')[1].split(')...')[0]
            # 将循环小数转换为有限小数近似值（使用足够多的位数）
            # 移除循环小数标记，使用有限部分进行计算
            finite_part = value.split('(')[0]
            # 生成足够多的循环节位数用于计算
            expanded = finite_part
            if '.' in finite_part:
                # 扩展循环节到足够的长度
                expanded = finite_part + self._repeating_part * 20  # 使用20次循环节
            value = expanded
        
        # 使用Decimal库进行高精度计算
        self._decimal = Decimal(value)
    
    @property
    def sign(self):
        """获取符号"""
        return -1 if self._decimal < 0 else 1
    
    @property
    def integer(self):
        """获取整数部分"""
        return str(abs(int(self._decimal)))
    
    @property
    def decimal(self):
        """获取小数部分"""
        decimal_str = str(self._decimal)
        if '.' in decimal_str:
            return decimal_str.split('.')[1].rstrip('0')
        return ''
    
    def __repr__(self):
        """返回数字的字符串表示，智能处理循环小数"""
        # 检查是否是显式的循环小数
        if self._is_repeating and self._repeating_part:
            # 显式循环小数，保持原始格式
            return self._original_str
        
        # 检查是否是整数
        if self._decimal == int(self._decimal):
            return str(int(self._decimal))
        
        # 转换为字符串
        num_str = str(self._decimal)
        
        # 智能检测循环小数
        decimal_part = num_str.split('.')[1] if '.' in num_str else ''
        
        # 检查是否有循环节（简单实现）
        if len(decimal_part) > 6:  # 只有小数部分较长时才检查
            # 尝试检测循环节
            detected_repeating = self._detect_repeating_part(decimal_part)
            if detected_repeating:
                # 找到循环节，返回智能表示
                integer_part = num_str.split('.')[0]
                # 找到循环节开始的位置
                start_pos = decimal_part.find(detected_repeating)
                if start_pos == 0:
                    # 循环节从第一位开始
                    return f"{integer_part}.({detected_repeating})..."
                else:
                    # 循环节在小数部分中间开始
                    non_repeating = decimal_part[:start_pos]
                    return f"{integer_part}.{non_repeating}({detected_repeating})..."
        
        # 普通小数，直接返回
        return num_str
    
    def _detect_repeating_part(self, s):
        """检测字符串中的循环节
        
        Args:
            s: 小数部分字符串
            
        Returns:
            str: 循环节，如果没有则返回空字符串
        """
        # 只检测长度大于1的字符串
        if len(s) < 6:  # 需要足够长的字符串才能检测循环节
            return ''
        
        # 尝试不同长度的循环节
        for i in range(1, min(10, len(s) // 2) + 1):  # 限制循环节最大长度为10
            # 从字符串末尾开始检查，因为循环小数的末尾应该是完整的循环节
            for j in range(len(s) - 2 * i, len(s) - i):
                pattern = s[j:j+i]
                # 检查是否重复出现
                if s.endswith(pattern * 2):
                    return pattern
        
        # 检查是否所有字符都相同
        if len(set(s[-10:])) == 1:  # 检查最后10个字符是否相同
            return s[-1]
        
        return ''
    
    def __add__(self, other):
        """高精度加法，使用Decimal库"""
        if not isinstance(other, EW_Number):
            return NotImplemented
        
        result_decimal = self._decimal + other._decimal
        return EW_Number(result_decimal)
    
    def __sub__(self, other):
        """高精度减法，使用Decimal库"""
        if not isinstance(other, EW_Number):
            return NotImplemented
        
        result_decimal = self._decimal - other._decimal
        return EW_Number(result_decimal)
    
    def __mul__(self, other):
        """高精度乘法，使用Decimal库"""
        if not isinstance(other, EW_Number):
            return NotImplemented
        
        result_decimal = self._decimal * other._decimal
        return EW_Number(result_decimal)
    
    def __truediv__(self, other):
        """高精度除法，使用Decimal库"""
        if not isinstance(other, EW_Number):
            return NotImplemented
        
        if other._decimal == 0:
            raise ZeroDivisionError("Division by zero")
        
        result_decimal = self._decimal / other._decimal
        return EW_Number(result_decimal)
    
    def __eq__(self, other):
        """相等比较"""
        if not isinstance(other, EW_Number):
            return NotImplemented
        
        return EW_Boolean(self._decimal == other._decimal)
    
    def __lt__(self, other):
        """小于比较"""
        if not isinstance(other, EW_Number):
            return NotImplemented
        
        return EW_Boolean(self._decimal < other._decimal)
    
    def __gt__(self, other):
        """大于比较"""
        if not isinstance(other, EW_Number):
            return NotImplemented
        
        return EW_Boolean(self._decimal > other._decimal)
    
    def __le__(self, other):
        """小于等于比较"""
        if not isinstance(other, EW_Number):
            return NotImplemented
        
        return EW_Boolean(self._decimal <= other._decimal)
    
    def __ge__(self, other):
        """大于等于比较"""
        if not isinstance(other, EW_Number):
            return NotImplemented
        
        return EW_Boolean(self._decimal >= other._decimal)
    
    def __hash__(self):
        """哈希方法，使EW_Number对象可哈希"""
        return hash(self._decimal)
    
    def _isint(self) -> bool:
        """检查是否为整数"""
        return self._decimal == int(self._decimal)
    
    def __pow__(self, other):
        """高精度幂运算，使用Decimal库"""
        if not isinstance(other, EW_Number):
            return NotImplemented
        
        if not other._isint():
            raise ValueError("Power must be an integer")
        
        exponent = int(other._decimal)
        result_decimal = self._decimal ** exponent
        return EW_Number(result_decimal)
    
    def copy(self):
        """创建副本"""
        return EW_Number(self._decimal)

class EW_String(EW_Type):
    def __init__(self, value, without_quote=True):
        clog(f'EW_String init: value: {value}, without_quote: {without_quote}')
        if without_quote:
            clog(f"Removed quotes from string: {value}")
            self.value = value[1:-1]  # 舍弃左右的引号
            clog(f'After, string: {self.value}')
        else:
            self.value = value
            clog(f"String: {self.value}")

    def __add__(self, other):
        if isinstance(other, EW_String):
            return EW_String(self.value + other.value, without_quote=False)
        else:
            return NotImplemented
    def __mul__(self, other):
        if isinstance(other, EW_Number) and other._isint():
            return EW_String(self.value * int(other.value), without_quote=False)
        else:
            return NotImplemented
    
    def __rmul__(self, other):
        if isinstance(other, EW_Number) and other._isint():
            return EW_String(self.value * int(other.value), without_quote=False)
        else:
            return NotImplemented
    
    def __repr__(self):
        return f'{self.value}'
    
    def __eq__(self, other):
        if isinstance(other, EW_String):
            return self.value == other.value
        elif isinstance(other, str):
            return self.value == other
        else:
            return NotImplemented
    
    def __ne__(self, other):
        return not self.__eq__(other)
    
    def __hash__(self):
        return hash((self.value, type(self)))


class EW_Boolean(EW_Type):
    def __repr__(self):
        return "true" if self.value else "false"
    
    def __bool__(self):
        return bool(self.value)
    
    def __eq__(self, other):
        return EW_Boolean(self.value == other.value)

    def __ne__(self, other):
        return EW_Boolean(self.value != other.value)

class EW_Function:
    """函数类型"""
    
    def __init__(self, params: list[str], body: list[dict[str, Any]], env: Env, name: str = "do_func"):
        self.params = params
        self.body = body
        self.env = env
        self.name = name  # 存储函数名
    
    def __call__(self, *args):
        # 函数调用逻辑将在解释器中实现
        return self
    
    def __str__(self):
        return f"<function {self.name} at {hex(id(self))}>"
    
    def __repr__(self):
        return self.__str__()

class EW_MFunction:
    """记忆化函数类型"""
    
    def __init__(self, params: list[str], body: list[dict[str, Any]], env: Env, name: str = "mfunc"):
        self.params = params
        self.body = body
        self.env = env
        self.name = name  # 记忆化函数名称
        self._cache = {}  # 记忆化缓存
    
    def __call__(self, *args):
        # 函数调用逻辑将在解释器中实现
        return self
    
    def __str__(self):
        return f"<mfunction {self.name} at {hex(id(self))}>"
    
    def __repr__(self):
        return self.__str__()

class EW_Table(EW_Type):
    """Table数据类型，支持键值对存储和混合类型键"""
    
    def __init__(self, value=None):
        """初始化Table对象
        
        Args:
            value: 可选的初始键值对字典
        """
        # 使用字典存储键值对，确保键的类型安全
        self._data = {}
        
        # 如果提供了初始值，添加到Table中
        if value:
            for key, val in value.items():
                self._data[key] = val
    
    def __getitem__(self, key):
        """通过键获取值
        
        Args:
            key: 键，可以是字符串或数字
            
        Returns:
            对应的值
            
        Raises:
            KeyError: 如果键不存在
        """
        clog(f'Getting table[{[key, type(key).__name__]}]')
        clog(f'now table data: {ld_show([(k, type(k).__name__, v, type(v).__name__) for k, v in self._data.items()])}')
        return self._data[key]
    
    def __setitem__(self, key, value):
        """设置键值对
        
        Args:
            key: 键，可以是字符串或数字
            value: 值
        """
        self._data[key] = value
    
    def __repr__(self):
        """返回Table的字符串表示"""
        items = []
        for key, value in self._data.items():
            if isinstance(key, str):
                # 字符串键添加引号
                items.append(f'"{key}": {value}')
            else:
                # 数字键直接显示
                items.append(f'{key}: {value}')
        return f'{{{", ".join(items)}}}'

class EW_List(EW_Type):
    def __init__(self, invalue=None):
        self.value = []
        if invalue:
            for item in invalue:
                self.value.append(item)
    
    def __repr__(self):
        return '[' + ', '.join([str(i) for i in self.value]) + ']'

if __name__ == "__main__":
    # 获取当前文件所在目录的父目录（即项目根目录）
    import os, sys
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)  # 项目根目录

    # 将pack目录添加到系统路径
    core_dir = os.path.join(parent_dir, 'pack')
    sys.path.insert(0, core_dir)

    import EW_list as es
    print(
        es.packall['push'](
            EW_List(
                [
                    EW_Number(1),
                    EW_Number(2)
                ]
            ), 
            EW_Number(1)
        )
    )
