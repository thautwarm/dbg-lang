"""
从ast生成对应的tables列表
"""
from collections import defaultdict
from typing import Dict, Set, List, Optional, Union, Tuple
from Ruikowa.ObjectRegex.ASTDef import Ast
from .type_map import type_map

Indent = '    '
Indentn = '\n' + Indent


def repr_for(name, *fields):
    field_list = ', '.join([f'{field}:{{self.{field}}}' for field in fields])
    return 'f"{name}{{{{ {field_list} }}}}"'.format(name=name, field_list=field_list)


class DBP:
    """
    解析一个dbp文件
    """

    def __init__(self):
        self.tables = {}
        # 所有表定义的spec
        # 结构为 {
        #   'primary': {
        #               'id':{'Type': <类型名>,  'Foreign': <外键定义, optional>, 'primary_key': <bool>, 'nullable': <bool> },
        #               ...
        #               },
        #    'field': {
        #               <同primary，但每个field没有`Foreign`和`primary_key`>
        #              },
        #    'relation': {
        #                   <relation名字>: (<relation类型> , <relation定义>),
        #                   ...
        #                 }
        #    'repr': <__repr__返回的表达式>
        # }

        self.RelationSpec: Dict[str,Set[str]] = defaultdict(set)
        # 全关系表 eg. User => ['course', 'group', ...]

        self.RefTable: Dict[str, Dict[str, Optional[str]]] = defaultdict(lambda: defaultdict(lambda: None))
        # 根据两个表A, B 得到 A -> B 的联结关系名
        # 例如: RefTable[User, Group] == 'ref_groups'

        self.RelationSpecForDestruction = defaultdict(dict)
        # 根据表名， 得到一组tuple, 每个tuple由一个关系和这个关系中需要删除的对象的名字。
        # 例如 RelationSpecForDestruction[User][Sign] = 'sign'( user - sign 一对多且 user对signs有所有权

        self.LRType: Dict[str, Dict[str, str]] = defaultdict(dict)
        # 根据左右表名，得到中间表名

        self.LRRef: Dict[str, Dict[str, str]] = self.RefTable
        # 根据左右表名，得到从左查右的关系名

        self.current_table_name: str = None
        # 当前处理胡table_name




    def ast_for_stmts(self, stmts: Union[str, Ast]) -> None:
        for stmt in stmts:
            if stmt is '\n':
                continue
            self.ast_for_stmt(stmt)

    def ast_for_stmt(self, stmt: Ast) -> None:
        if stmt.name == 'Relation':
            self.ast_for_relation(stmt)
        else:
            self.ast_for_table_def(stmt)

    def ast_for_repr(self, repr_def: Ast) -> Optional[str]:
        if len(repr_def) is 0:
            return None
        return repr_for(self.current_table_name, *[each[0] for each in repr_def[0]])

    def ast_for_field_def_list(self, field_def_list: Ast, repr_def: Optional[Ast] = None) -> Tuple[Dict, Optional[str]]:
        assert field_def_list.name in ('PrimaryDefList', 'FieldDefList')
        ret = dict(self.ast_for_field_def(each) for each in field_def_list)

        repr = None
        if repr_def:
            repr = self.ast_for_repr(repr_def)
        return ret, repr

    def ast_for_table_def(self, table_def: Ast) -> None:
        symbol, primary_def_list, *tail = table_def
        table_name = self.current_table_name = symbol[0]

        primaries, _ = self.ast_for_field_def_list(primary_def_list)

        for each in tuple(primaries.keys()):
            primaries[each]['primary_key'] = True

        fields, repr = self.ast_for_field_def_list(*tail)

        if not repr:
            repr = repr_for(table_name, *primaries.keys(), *fields.keys())

        self.tables[table_name] = {
            'primary': primaries,
            'field': fields,
            'repr': repr,
            'relation': {}}

    def ast_for_field_def(self, field_def: Ast) -> Tuple[str, dict]:
        (field_name,), type = field_def
        return field_name, self.ast_for_type(type)

    def ast_for_type(self, type: Ast) -> dict:
        table_name = self.current_table_name

        if type[-1].name != 'Default':
            type_name, *options = type
            type_name = type_map(type_name[0])
            ret = {'__type__': type_name}
        else:
            type_name, *options, default = type
            type_name = type_map(type_name[0])
            ret = {'__type__': type_name, 'default': ''.join(default)}

        options = ''.join([o[0] for o in options])

        if '!' in options:
            ret['unique'] = True

        if '?' not in options:
            ret['nullable'] = False

        if '~' in options:
            ret['__sequence__'] = f"Sequence('{table_name.lower()}_id_seq')"

        return ret

    def ast_for_relation(self, relation_def: Ast) -> None:
        left_weighted_symbol, left_ref_level, right_ref_level, right_weighted_symbol, field_def_list = relation_def

        (upper_case_left_name,), *l_weights = left_weighted_symbol
        (upper_case_right_name,), *r_weights = right_weighted_symbol

        l_weights = len(l_weights)  # 关系里左类的权重，当左类 > 右类，则左对右具有所有权(删除所有引用右的左，则删除右)
        r_weights = len(r_weights)  # 关系里右类的权重

        left_ref_level = len(left_ref_level)  # 1 or 2 => 一 或 多
        right_ref_level = len(right_ref_level)  # 1 or 2 => 一 或 多
        # eg. (left_ref_level, right_ref_level) == (1, 2) 表示 一对多关系

        lower_case_left_name = upper_case_left_name.lower()

        lower_case_right_name = upper_case_right_name.lower()

        fields, _ = self.ast_for_field_def_list(field_def_list)

        primaries = {lower_case_left_name + '_id':
                         dict(primary_key=True,
                              __type__='Integer',
                              __foreign__=f'ForeignKey("{lower_case_left_name}.id")'),
                     lower_case_right_name + '_id':
                         dict(primary_key=True,
                              __type__='Integer',
                              __foreign__=f'ForeignKey("{lower_case_right_name}.id")')}

        upper_case_table_name = f'{upper_case_left_name}{upper_case_right_name}'

        repr = repr_for(upper_case_table_name, *primaries.keys(), *fields.keys())

        self.tables[upper_case_table_name] = {'primary': primaries,
                                              'field': fields,
                                              'repr': repr,
                                              'relation': {}}

        """
        单数依然用-s结尾，表示列表。
        """

        name_of_left = f'{lower_case_left_name}s'
        name_of_right = f'{lower_case_right_name}s'

        name_to_ref_left = f'ref_{name_of_left}'
        name_to_ref_right = f'ref_{name_of_right}'

        self.RelationSpec[upper_case_left_name].add(lower_case_right_name)
        self.RelationSpec[upper_case_right_name].add(lower_case_left_name)

        self.LRType[upper_case_left_name][upper_case_right_name] = f'{upper_case_left_name}{upper_case_right_name}'
        self.LRType[upper_case_right_name][upper_case_left_name] = f'{upper_case_left_name}{upper_case_right_name}'

        self.RefTable[upper_case_left_name][upper_case_right_name] = name_to_ref_right
        self.RefTable[upper_case_right_name][upper_case_left_name] = name_to_ref_left

        self.tables[upper_case_table_name]['relation'].update(
            {
                lower_case_right_name: (f"{upper_case_right_name}",  # type
                                        f"relationship('{upper_case_right_name}', "
                                        f"back_populates='{name_to_ref_left}', uselist=False)"),
                lower_case_left_name: (f'{upper_case_left_name}',  # type
                                       f"relationship('{upper_case_left_name}', "
                                       f"back_populates='{name_to_ref_right}', uselist=False)")
            })

        self.tables[upper_case_left_name]['relation'][
            name_to_ref_right] = (f"List[{upper_case_left_name}{upper_case_right_name}]",  # type
                                  f"relationship('{upper_case_left_name}{upper_case_right_name}', "
                                  f"back_populates='{lower_case_left_name}')")

        self.tables[upper_case_right_name]['relation'][
            name_to_ref_left] = (f"List[{upper_case_left_name}{upper_case_right_name}]",  # type
                                 f"relationship('{upper_case_left_name}{upper_case_right_name}', "
                                 f"back_populates='{lower_case_right_name}')")

        if l_weights is 0 and r_weights is 0:
            """互相之间无所有权关系
            """
            return

        if l_weights >= r_weights:
            """所有权归左
            """
            self.RelationSpecForDestruction[upper_case_left_name][upper_case_right_name] = lower_case_right_name

        if l_weights <= r_weights:
            self.RelationSpecForDestruction[upper_case_right_name][upper_case_left_name] = lower_case_left_name
