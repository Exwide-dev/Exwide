from Type import *
from Error import clog

class EW_builtins:
    def __init__(self, func):
        self.func = func
    
    def __call__(self, *args):
        clog(f'{self.func.__name__} args: {args}')
        return self.func(*args)
    
    def __repr__(self):
        return f'<built-ins function {self.func.__name__}>'

'''def reg_builtin(func):
    return EW_builtins(func)'''

'''ew_builtins = {
    'print': printf,
    'license': license,
    'help': help,
    'copyright': copyright(),
    'type': typeof,
}'''

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
    return '''MIT 许可证'''

@reg_builtin()
def help():
    return '''
    帮助信息
    '''

@reg_builtin()
def copyright():
    return EW_String('Exwide 解释器 © 2025 CGrakeski')

@reg_builtin('type')
def typeof(x):
    return type(x).__name__

@reg_builtin('exit')
def ew_exit():
    exit()

if __name__ == '__main__':
    print(ew_builtins)
    printf([EW_String('Hello World')])
    print(
        typeof(EW_String('Hello World'))
    )