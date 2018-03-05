from .parse import parse
from .table_info_gen import DBP
from .code_gen import Analyzer


def compile(*args):
    if 'import' in args:
        idx = args.index('import')
        imports = args[idx + 1:]
        imports = dict(map(str.strip, kv.split('from')) for kv in imports)
        args = args[:idx]
    else:
        imports = {}
    input_file, out_file, *tail = args

    stmts = parse(input_file)

    handler = DBP()

    handler.ast_for_stmts(stmts)

    if tail:

        conf = tail
    else:

        conf = ()

    Analyzer(handler, *conf, **imports).generate(out_file)
