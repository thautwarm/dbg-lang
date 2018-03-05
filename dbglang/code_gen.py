from .table_info_gen import DBP
from .parse import parse
from typing import Dict
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


relation_delete_spec = ("@DeleteManager.Between({ManageType}, {DeleteType})\n"
                        "def delete_{delete_type}_from_{manage_type}(*relations) -> Optional[Seq[Tuple[Optional[dict], Optional[dict]]]]:\n"
                        "{codes}\n")

entity_delete_spec = ("@DeleteManager.For({EntityType})\n"
                      "def delete_{entity_type}(entity) -> Optional[dict]:\n"
                      "{codes}\n")


class Analyzer:

    def __init__(self, dbp: DBP, *conf: str, **custom_libs):
        self.dbp = dbp
        self.config_codes = conf
        self.custom_libs = custom_libs

    def generate_table(self, table_name, table: dict) -> str:
        res = ("class {TableName}(Base):\n"
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

            relations=Indentn.join(f'{field_name}: "{t}" = {v}' for field_name, (t, v) in table['relation'].items()),

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
                     f"{Indent}def __each__(e) -> Tuple[dict, dict]:\n"
                     f"{Indent*2}r = delete_{delete_type.lower()}(e.{delete_field_of_relation})\n"
                     f"{Indent*2}l = delete_{manage_type.lower()}_{delete_type.lower()}(e)\n"
                     f"{Indent*2}return l, r\n"
                     "\n\n"
                     f"{Indent}return tuple(__each__(each) for each in relations)\n")

        return relation_delete_spec.format(ManageType=manage_type, DeleteType=delete_type,
                                           manage_type=manage_type.lower(), delete_type=delete_type.lower(),
                                           codes=codes)

    def make_entity_delete(self, entity_type: str):
        relations_to_delete = self.dbp.RelationSpec[entity_type]

        if not relations_to_delete:
            codes = (f"{Indent}normal_delete_entity(entity)\n"
                     f"{Indent}return None\n")
        else:
            lower_case_entity_type_name = entity_type.lower()
            key_list = []

            for each in relations_to_delete:
                relations = f'entity.{self.dbp.RefTable[entity_type][each.capitalize()]}'
                elem = f"'{each}': delete_{each}_from_{lower_case_entity_type_name}(*{relations})"
                key_list.append(elem)

            codes = ('{Indent}ret = {{{content}}}\n'
                     '{Indent}normal_delete_entity(entity)\n'
                     '{Indent}return ret').format(Indent=Indent, content=f',\n{Indent*3}'.join(key_list))

        return entity_delete_spec.format(codes=codes,
                                         EntityType=entity_type,
                                         entity_type='_'.join(map(str.lower, re.findall('[A-Z][a-z_]*', entity_type))))

    def generate(self, out_file: str):

        import os
        table_def_codes = '\n'.join(self.generate_table(k, v) for k, v in self.dbp.tables.items())

        entity_delete_codes = '\n'.join(self.make_entity_delete(k) for k in self.dbp.tables)

        relation_delete_codes = '\n'.join(
            self.make_relation_delete(k, v.capitalize()) for k, vs in self.dbp.RelationSpec.items() for v in vs)

        with open(os.path.join(os.path.split(__file__)[0], 'templates.py')) as f:
            templates = f.read()

        codes = templates.replace('##{config}##', ''.join(self.config_codes)
                        ).replace('##{table_def}##', table_def_codes
                        ).replace('##{methods}##', f'{entity_delete_codes}\n{relation_delete_codes}'
                        ).replace('##{custom_lib}##', '\n'.join(f'from {_from} import {_import}' for _import, _from in self.custom_libs.items()))

        with open(out_file, 'w') as f:
            f.write(codes)