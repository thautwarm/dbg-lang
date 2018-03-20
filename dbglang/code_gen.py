from .table_info_gen import DBP
from .parse import parse
from typing import Dict
from .auto_db_test_maker import TestGenerateSession
import re

Indent = '    '
Indentn = '\n' + Indent


def render_column(v: dict) -> str:
    ret = [v['__type__']]
    del v['__type__']

    if '__foreign__' in v:
        ret.append(v['__foreign__'])
        del v['__foreign__']
    elif '__sequence__' in v:
        ret.append(v['__sequence__'])
        del v['__sequence__']

    # kwargs
    for a, b in v.items():
        ret.append(f'{a}={b}')

    return ', '.join(ret)


def relationship(reference_type_name: str, from_field: str, ref_field: str, use_list=True):
    relation_table = None

    @property
    def reference(self):
        nonlocal relation_table
        if not relation_table:
            relation_table = eval(reference_type_name)

        res = relation_table.query.filter(getattr(relation_table, ref_field) == getattr(self, from_field))
        if not use_list:
            return res.frist()
        return res

    return reference


relation_delete_spec = ("@DeleteManager.Between({ManageType}, {DeleteType})\n"
                        "def delete_{delete_type}_from_{manage_type}(*relations) -> Optional[Seq[Tuple[Optional[dict], Optional[dict]]]]:\n"
                        "{codes}\n")

entity_delete_spec = ("@DeleteManager.For({EntityType})\n"
                      "def delete_{entity_type}(entity) -> {RetType}:\n"
                      "{codes}\n")


class Analyzer:

    def __init__(self, dbp: DBP, *conf: str, **custom_libs):
        self.dbp = dbp
        self.config_codes = conf
        self.custom_libs = custom_libs

    def generate_table(self, table_name, table: dict) -> str:

        res = ("class {TableName}(Base, ITable):\n"
               "{Indent}__tablename__ = '{table_name}'\n\n"
               "{Indent}# primary keys\n{Indent}{primaries}\n\n"
               "{Indent}# fields\n{Indent}{fields}\n\n"
               "{Indent}# relationship\n{Indent}{relations}\n\n"
               "{Indent}# repr\n{Indent}def __repr__(self):\n{Indent}{Indent}return {repr}\n").format(

            Indent=Indent,

            TableName=table_name,

            table_name='_'.join(map(str.lower, re.findall('[A-Z][a-z_]*', table_name))),

            primaries=Indentn.join(f'{field_name} = Column({render_column(v)})' for field_name, v in

                                   table['primary'].items()),
            fields=Indentn.join(f'{field_name} = Column({render_column(v)})' for field_name, v in
                                table['field'].items()),

            relations=Indentn.join(table['relation']),

            repr=table['repr'])

        return res

    def make_relation_delete(self, manage_type: str, delete_type: str):
        delete_field_of_relation = self.dbp.RelationSpecForDestruction[manage_type].get(delete_type)

        if not delete_field_of_relation:
            codes = (f"{Indent}normal_delete_relations(*relations)\n"
                     f"{Indent}return None")
        else:
            codes = (f"{Indent}if not relations:\n"
                     f"{Indent*2}return ()\n"
                     f"{Indent}def __each__(e) -> Tuple[Optional[dict], Optional[dict]]:\n"
                     f"{Indent*2}temp = e.{delete_field_of_relation}\n"
                     f"{Indent*2}l = delete_{manage_type.lower()}_{delete_type.lower()}(e)\n"
                     f"{Indent*2}r = delete_{delete_type.lower()}(temp)\n"
                     f"{Indent*2}return l, r\n"
                     "\n\n"
                     f"{Indent}return tuple(__each__(each) for each in relations)\n")

        return relation_delete_spec.format(ManageType=manage_type, DeleteType=delete_type,
                                           manage_type=manage_type.lower(), delete_type=delete_type.lower(),
                                           codes=codes)

    def make_entity_delete(self, entity_type: str):
        relations_to_delete = self.dbp.RelationSpec[entity_type]

        if not relations_to_delete:
            codes = f"{Indent}{entity_type}.query.filter_by(id=entity.id) if hasattr(entity, 'id') else db_session.delete(entity)\n"
            ret_type = 'None'
        else:
            lower_case_entity_type_name = entity_type.lower()
            key_list = []

            for each in relations_to_delete:
                relations = f'entity.{self.dbp.RefTable[entity_type][each.capitalize()]}'
                elem = f"'{each}': delete_{each}_from_{lower_case_entity_type_name}(*{relations})"
                key_list.append(elem)
            content=f',\n{Indent*3}'.join(key_list)
            codes = (f'{Indent}ret = {{{content}}}\n'
                     f"{Indent}{entity_type}.query.filter_by(id=entity.id) if hasattr(entity, 'id') else db_session.delete(entity)\n"
                     f'{Indent}return ret')
            ret_type = 'Optional[Dict]'

        return entity_delete_spec.format(codes=codes,
                                         RetType=ret_type,
                                         EntityType=entity_type,
                                         entity_type='_'.join(map(str.lower, re.findall('[A-Z][a-z_]*', entity_type))))

    def generate(self, out_file: str):

        import os

        def generate_data(table_name: str, spec: Dict[str, dict]):
            session = TestGenerateSession()
            sample_num = 500

            def format_attr(attr_name, attr_type):
                return f'{attr_name}={session.generate_inst_for_type(attr_type)}'

            def format_attrs(_spec):
                return f', \n{Indent*3}'.join([format_attr(attr_name, more_info['__type__']) for attr_name, more_info in
                                               _spec['primary'].items()] +
                                              [format_attr(attr_name, more_info['__type__']) for attr_name, more_info in
                                               _spec['field'].items()])

            return "{}List = [\n{}{}]".format(table_name,
                                              Indent * 3,
                                              f',\n{Indent*3}'
                                              .join([f'{table_name}({format_attrs(spec)})'
                                                     for _ in range(sample_num)]))

        with open(os.path.splitext(out_file)[0] + '.test_samples.py', 'w') as f:
            f.write('from random import randint\n'
                    'from datetime import datetime, timedelta\n' +
                    '\n'.join(generate_data(k, v) for k, v in self.dbp.tables.items()))

        table_def_codes = '\n'.join(self.generate_table(k, v) for k, v in self.dbp.tables.items())

        entity_delete_codes = '\n'.join(self.make_entity_delete(k) for k in self.dbp.tables)

        relation_delete_codes = '\n'.join(
            self.make_relation_delete(k, v.capitalize()) for k, vs in self.dbp.RelationSpec.items() for v in vs)

        with open(os.path.join(os.path.split(__file__)[0], 'templates.py')) as f:
            templates = f.read()

        codes = templates.replace('##{config}##', ''.join(self.config_codes)
                                  ).replace('##{table_def}##', table_def_codes
                                            ).replace('##{methods}##', f'{entity_delete_codes}\n{relation_delete_codes}'
                                                      ).replace('##{custom_lib}##', '\n'.join(
            f'from {_from} import {_import}' for _import, _from in self.custom_libs.items()))

        def rec(v, symbol):
            return key_to_eval(v, symbol=symbol) if isinstance(v, dict) else f'"{v}"' if not symbol and isinstance(v,
                                                                                                                   str) else v

        def key_to_eval(dic: dict, symbol=False) -> str:
            dic = dict(dic)
            return '{{{}}}'.format(", ".join(f'{k}: {rec(v, symbol)}' for k, v in dic.items()))

        for_inspection = ("\nRefTable = {}\n".format(key_to_eval(self.dbp.RefTable)),
                          "RelationSpec = {}\n".format(key_to_eval(self.dbp.RelationSpec)),
                          "RelationSpecForDestruction = {}\n".format(key_to_eval(self.dbp.RelationSpecForDestruction)),
                          'LRType = {}\n'.format(key_to_eval(self.dbp.LRType, symbol=True)),
                          'LRRef = {}\n'.format(key_to_eval(self.dbp.LRRef)),
                          'FieldSpec = {}\n'.format(key_to_eval(self.dbp.FieldSpec)))

        with open(out_file, 'w') as f:
            f.write(codes + '\n'.join(for_inspection))
