# math

import os
import sys

# 获取当前文件所在目录的父目录（即项目根目录）
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)  # 项目根目录

# 将core目录添加到系统路径
core_dir = os.path.join(parent_dir, 'core')
sys.path.insert(0, core_dir)

from Type import EW_Number, EW_Boolean
from Error import raise_err, EW_RUNTIME_ERROR

packall = {}

def pack_register(thing):
    global packall
    packall[thing.__name__] = thing

@pack_register
def add(a: EW_Number, b: EW_Number) -> EW_Number:
    """加法运算"""
    return a + b

@pack_register
def subtract(a: EW_Number, b: EW_Number) -> EW_Number:
    """减法运算"""
    return a - b

@pack_register
def multiply(a: EW_Number, b: EW_Number) -> EW_Number:
    """乘法运算"""
    return a * b

@pack_register
def divide(a: EW_Number, b: EW_Number) -> EW_Number:
    """除法运算"""
    if b._decimal == 0:
        raise_err(EW_RUNTIME_ERROR, 'Division by zero')
    return a / b

@pack_register
def sqrt(a: EW_Number) -> EW_Number:
    """平方根运算"""
    if a._decimal < 0:
        raise_err(EW_RUNTIME_ERROR, 'Square root of negative number')
    return EW_Number(str(a._decimal.sqrt()))

@pack_register
def pow(a: EW_Number, b: EW_Number) -> EW_Number:
    """幂运算"""
    return a ** b

@pack_register
def abs(a: EW_Number) -> EW_Number:
    """绝对值运算"""
    return EW_Number(str(abs(a._decimal)))

@pack_register
def floor(a: EW_Number) -> EW_Number:
    """向下取整"""
    return EW_Number(str(a._decimal.to_integral_value(rounding='ROUND_FLOOR')))

@pack_register
def ceil(a: EW_Number) -> EW_Number:
    """向上取整"""
    return EW_Number(str(a._decimal.to_integral_value(rounding='ROUND_CEILING')))

@pack_register
def round(a: EW_Number, digits: EW_Number = None) -> EW_Number:
    """四舍五入"""
    if digits is None:
        return EW_Number(str(round(a._decimal)))
    else:
        return EW_Number(str(round(a._decimal, int(digits._decimal))))

@pack_register
def max(a: EW_Number, b: EW_Number) -> EW_Number:
    """取最大值"""
    return a if a._decimal > b._decimal else b

@pack_register
def min(a: EW_Number, b: EW_Number) -> EW_Number:
    """取最小值"""
    return a if a._decimal < b._decimal else b

@pack_register
def is_nan(a: EW_Number) -> EW_Boolean:
    """检查是否为NaN"""
    return EW_Boolean(a._decimal.is_nan())

@pack_register
def is_infinite(a: EW_Number) -> EW_Boolean:
    """检查是否为无穷大"""
    return EW_Boolean(a._decimal.is_infinite())
