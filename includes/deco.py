# deco
# 提供各种装饰器功能，如记忆化等

import os
import sys

from core.Type import EW_Function, EW_MFunction

packall = {}


def pack_register(thing):
    """注册装饰器到包中
    
    Args:
        thing: 要注册的装饰器函数
    """
    global packall
    packall[thing.__name__] = thing


@pack_register
def memoi(func):
    """记忆化装饰器
    
    将普通函数转换为记忆化函数，使用缓存存储计算结果
    
    Args:
        func: 要装饰的函数
    
    Returns:
        记忆化后的函数对象
    """
    if isinstance(func, EW_Function):
        # 如果是普通EW_Function，转换为EW_MFunction
        mfunc = EW_MFunction(
            func.params, 
            func.body, 
            func.env, 
            func.name
        )
        return mfunc
    elif isinstance(func, EW_MFunction):
        # 如果已经是记忆化函数，直接返回
        return func
    else:
        # 其他类型，返回原函数
        return func
