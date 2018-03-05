from sqlalchemy import (create_engine, Integer, String,
                        DateTime, ForeignKey, Sequence,
                        SmallInteger, Enum, Date, Table)
from sqlalchemy import Column as _Column
from sqlalchemy.orm import scoped_session, sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from typing import Dict, Set, Any, List, Callable, Tuple, Type, Optional, Sequence as Seq


##{custom_lib}##


class Config:
    database_url: str
    database_connect_options: dict
    ##{config}##


engine = create_engine(Config.database_url,
                       convert_unicode=True,
                       **Config.database_connect_options)

db_session = scoped_session(
    sessionmaker(autocommit=False,
                 autoflush=False,
                 bind=engine))

Base = declarative_base()
Base.query = db_session.query_property()


class DeleteManager:
    pre_relation_delete_events: Dict[Type[Table], Dict[Type[Table], Callable[[Table], None]]] = {}
    pre_entity_delete_events: Dict[Type[Table], Callable[[Table], None]] = {}

    @classmethod
    def get_delete_fn(cls, manage_obj, delete_obj) -> Optional[Callable[[Table], None]]:
        return DeleteManager.pre_relation_delete_events[type(manage_obj)].get(type(delete_obj))

    @classmethod
    def delete(cls, obj) -> None:
        return cls.get_delete_fn(obj)(obj)

    @staticmethod
    def Between(manage_type, delete_type: str):
        def wrap_fn(func):
            DeleteManager.pre_relation_delete_events[manage_type][delete_type] = func
            return func

        return wrap_fn

    @classmethod
    def For(cls, entity_type):
        def wrap(func):
            cls.pre_entity_delete_events[entity_type] = func
            return func

        return wrap


def normal_delete_entity(obj):
    db_session.delete(obj)


def normal_delete_relations(*relations):
    for each in relations:
        db_session.delete(each)



class Column:
    def __new__(cls, t, *args, **kwargs):
        if 'sqlalchemy' not in t.__module__:
            t = Enum(t)
        return _Column(t, *args, **kwargs)

##{table_def}##

##{methods}##
