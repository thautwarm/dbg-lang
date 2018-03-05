from .dbg_compiler import compile
import sys


def main(*args):
    compile(*args)


if __name__ == '__main__':
    main(*sys.argv[1:])
