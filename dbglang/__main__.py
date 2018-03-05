from .dbg_compiler import compile
import sys


def main():
    compile(*sys.argv[1:])


if __name__ == '__main__':
    main()
