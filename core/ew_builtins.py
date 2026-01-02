from core.Type import *
from core.Error import clog
from typing import TypeVar

class EW_builtins:
    def __init__(self, func):
        self.func = func
    
    def __call__(self, *args):
        clog(f'{self.func.__name__} args: {args}')
        return self.func(*args)
    
    def __repr__(self):
        return f'<built-ins function {self.func.__name__}>'

ew_builtins = {}

def reg_builtin(name=None):
    def decorator(func):
        global ew_builtins
        nfun = EW_builtins(func)
        if name is not None:
            nfun.func.__name__ = name
        else:
            nfun.func.__name__ = func.__name__
        ew_builtins[nfun.func.__name__] = nfun
        return nfun
    return decorator

@reg_builtin('print')
def printf(*x):
    print(*x)

@reg_builtin()
def license():
    return EW_String('''MIT License''', without_quote=False)

@reg_builtin()
def help():
    return EW_String('''Developing Version does not have help information.''', without_quote=False)

@reg_builtin()
def copyright():
    return EW_String('Exwide Interpreter (c) 2025 CGrakeski', without_quote=False)

@reg_builtin('type')
def typeof(x):
    return type(x).__name__

@reg_builtin('exit')
def ew_exit():
    exit()

@reg_builtin('input')
def ew_input() -> EW_String:
    inputs = input()
    return EW_String(inputs, without_quote=False)

T = TypeVar('T', bound = EW_Type)
from copy import deepcopy

@reg_builtin('copy')
def ew_copy(x: T) -> T:
    return deepcopy(x)

if __name__ == '__main__':
    print(ew_builtins)
    printf(EW_String('\'Hello World\''))
    print(
        typeof(EW_String('Hello World'))
    )
    print(ew_builtins['input']())
    print('Done')
    print(ew_builtins['copy'](EW_Boolean(True)))