from Ruikowa.ObjectRegex.Node import Ref, AstParser, SeqParser, LiteralParser, CharParser, MetaInfo, DependentAstParser

try:
    from .etoken import token
except:
    from etoken import token
import re

namespace = globals()
recurSearcher = set()
PrimaryDefList = AstParser([Ref('FieldDef'), SeqParser([LiteralParser(',', name='\',\''), Ref('FieldDef')])],
                           name='PrimaryDefList', toIgnore=[{}, {','}])
FieldDefList = AstParser([SeqParser([Ref('FieldDef'), SeqParser([LiteralParser('\n', name='\'\n\'')])]),
                          SeqParser([LiteralParser('\n', name='\'\n\'')])], name='FieldDefList', toIgnore=[{}, {'\n'}])
TableDef = AstParser(
    [Ref('Symbol'), LiteralParser('(', name='\'(\''), Ref('PrimaryDefList'), LiteralParser(')', name='\')\''),
     SeqParser([LiteralParser('\n', name='\'\n\'')]), LiteralParser('{', name='\'{\''),
     SeqParser([LiteralParser('\n', name='\'\n\'')]), Ref('FieldDefList'),
     SeqParser([Ref('ReprDef'), SeqParser([LiteralParser('\n', name='\'\n\'')])], atmost=1),
     LiteralParser('}', name='\'}\'')], name='TableDef', toIgnore=[{}, {'{', '}', '(', ')', '\n'}])
FieldDef = AstParser([Ref('Symbol'), LiteralParser(':', name='\':\''), Ref('Type')], name='FieldDef',
                     toIgnore=[{}, {':'}])
Type = AstParser([Ref('Symbol'), SeqParser([Ref('Option')]),
                  SeqParser([LiteralParser('=', name='\'=\''), Ref('Default')], atmost=1)], name='Type',
                 toIgnore=[{}, {'='}])
Option = AstParser([LiteralParser('?', name='\'?\'')], [LiteralParser('!', name='\'!\'')],
                   [LiteralParser('~', name='\'~\'')], name='Option')
Default = AstParser([SeqParser([LiteralParser('.+', name='\'.+\'', isRegex=True)], atleast=1)], name='Default')
ReprDef = AstParser([LiteralParser('repr', name='\'repr\''), DependentAstParser(
    [LiteralParser('{', name='\'{\''), SeqParser([LiteralParser('\n', name='\'\n\'')]), Ref('SymbolList'),
     SeqParser([LiteralParser('\n', name='\'\n\'')]), LiteralParser('}', name='\'}\'')],
    [LiteralParser('=', name='\'=\''), LiteralParser('all', name='\'all\'')])], name='ReprDef',
                    toIgnore=[{}, {'=', '{', '}', 'all', 'repr', '\n'}])
SymbolList = AstParser([Ref('Symbol'), SeqParser([LiteralParser(',', name='\',\''), Ref('Symbol')])], name='SymbolList',
                       toIgnore=[{}, {','}])
Comment = AstParser([LiteralParser('#', name='\'#\''), Ref('Default')], name='Comment')
Symbol = AstParser([LiteralParser('[a-zA-Z][a-zA-Z_]*', name='\'[a-zA-Z][a-zA-Z_]*\'', isRegex=True)], name='Symbol')
WeightedSymbol = AstParser([Ref('Symbol'), SeqParser([LiteralParser('^', name='\'^\'')])], name='WeightedSymbol')
Relation = AstParser(
    [Ref('WeightedSymbol'), Ref('Left'), LiteralParser('-', name='\'-\''), Ref('Right'), Ref('WeightedSymbol'),
     SeqParser([LiteralParser('\n', name='\'\n\'')]), LiteralParser('{', name='\'{\''),
     SeqParser([LiteralParser('\n', name='\'\n\'')]), SeqParser([Ref('FieldDefList')], atmost=1),
     LiteralParser('}', name='\'}\'')], name='Relation', toIgnore=[{}, {'-', '}', '{', '\n'}])
Left = AstParser([SeqParser([LiteralParser('<', name='\'<\'')], atleast=1, atmost=2)], name='Left')
Right = AstParser([SeqParser([LiteralParser('>', name='\'>\'')], atleast=1, atmost=2)], name='Right')
Stmts = AstParser(
    [SeqParser([DependentAstParser([LiteralParser('\n', name='\'\n\'')], [Ref('Relation')], [Ref('TableDef')])])],
    name='Stmts', toIgnore=[{}, {'\n'}])
PrimaryDefList.compile(namespace, recurSearcher)
FieldDefList.compile(namespace, recurSearcher)
TableDef.compile(namespace, recurSearcher)
FieldDef.compile(namespace, recurSearcher)
Type.compile(namespace, recurSearcher)
Option.compile(namespace, recurSearcher)
Default.compile(namespace, recurSearcher)
ReprDef.compile(namespace, recurSearcher)
SymbolList.compile(namespace, recurSearcher)
Comment.compile(namespace, recurSearcher)
Symbol.compile(namespace, recurSearcher)
WeightedSymbol.compile(namespace, recurSearcher)
Relation.compile(namespace, recurSearcher)
Left.compile(namespace, recurSearcher)
Right.compile(namespace, recurSearcher)
Stmts.compile(namespace, recurSearcher)
