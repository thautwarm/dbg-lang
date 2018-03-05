from Ruikowa.ErrorFamily import handle_error
from Ruikowa.ObjectRegex.MetaInfo import MetaInfo
from Ruikowa.ObjectRegex.ASTDef import Ast
from .dbp import Stmts, token


def parse(input_filename) -> Ast:
    with open(input_filename) as f:
        s = f.read()
    parser = handle_error(Stmts)
    tokens = token(s)
    meta = MetaInfo()
    stmts = parser(tokens, meta=meta, partial=False)
    return stmts
