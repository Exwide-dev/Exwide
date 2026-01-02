from EW_repl import repl
from core.Parser import directly_run as run
import sys

if __name__ == '__main__':
    args = sys.argv[1:]
    if args == []:
        repl()
    elif len(args) == 1:
        try:
            with open(args[0], 'r', encoding='utf-8') as f:
                code = f.read() + '\n'
                run(code)
        except FileNotFoundError:
            print(f'File {args[0]} not found')
    else:
        print('Unexpected argument')