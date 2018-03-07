from sqlalchemy import (create_engine, Integer, String,
                        DateTime, ForeignKey, Sequence,
                        SmallInteger, Enum, Date, Table)
from sqlalchemy import Column as _Column
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from typing import Dict, Set, Any, List, Callable, Tuple, Type, Optional, Sequence as Seq
from abc import abstractmethod
from collections import defaultdict


class Config:
    database_url: str
    database_connect_options: dict
    


from .customs import *


def filter_from_table(table, cond):
    return getattr(table, 'query').filter(cond)


engine = create_engine(Config.database_url,
                       convert_unicode=True,
                       **Config.database_connect_options)

db_session = scoped_session(
    sessionmaker(autocommit=False,
                 autoflush=False,
                 bind=engine))

Base = declarative_base()
Base.query = db_session.query_property()


class FuncForRelations:

    @abstractmethod
    def __call__(self, *relations) -> Optional[Seq[Tuple[Optional[dict], Optional[dict]]]]:
        pass


class FuncForEntity:

    @abstractmethod
    def __call__(self, entity) -> Optional[dict]:
        pass


class DeleteManager:
    pre_relation_delete_events: Dict[Type[Table], Dict[Type[Table], FuncForRelations]] = defaultdict(dict)
    pre_entity_delete_events: Dict[Type[Table], FuncForEntity] = {}

    @classmethod
    def get_relation_delete_fn(cls, from_type: type, delete_type: type) -> FuncForRelations:
        return cls.pre_relation_delete_events[from_type].get(delete_type)

    @classmethod
    def get_entity_delete_fn(cls, entity_type: type) -> FuncForEntity:
        return cls.pre_entity_delete_events[entity_type]

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


class User(Base):
    __tablename__ = 'user'

    # primary keys
    id = Column(Integer, Sequence('user_id_seq'), nullable=False, primary_key=True)

    # fields
    openid = Column(String(200))
    account = Column(String(50), unique=True, nullable=False)
    password = Column(String(50), nullable=False)
    permission = Column(Permission, nullable=False)
    sex = Column(Sex, default=Sex.unknown, nullable=False)
    nickname = Column(String(50))

    # relationship
    
    @property
    def ref_items(self) -> "List[UserItem]":
        return filter_from_table(UserItem, UserItem.user_id == self.id)

    
    @property
    def ref_courses(self) -> "List[UserCourse]":
        return filter_from_table(UserCourse, UserCourse.user_id == self.id)

    
    @property
    def ref_somes(self) -> "List[UserSome]":
        return filter_from_table(UserSome, UserSome.user_id == self.id)


    # repr
    def __repr__(self):
        return f"User{{ id:{self.id}, nickname:{self.nickname}, permission:{self.permission} }}"

class Item(Base):
    __tablename__ = 'item'

    # primary keys
    id = Column(Integer, Sequence('item_id_seq'), nullable=False, primary_key=True)

    # fields
    name = Column(String(50))
    cost = Column(Integer, nullable=False)

    # relationship
    
    @property
    def ref_users(self) -> "List[UserItem]":
        return filter_from_table(UserItem, UserItem.item_id == self.id)


    # repr
    def __repr__(self):
        return f"Item{{ id:{self.id}, name:{self.name}, cost:{self.cost} }}"

class Course(Base):
    __tablename__ = 'course'

    # primary keys
    id = Column(Integer, Sequence('course_id_seq'), nullable=False, primary_key=True)

    # fields
    location = Column(String(50))
    time_seq = Column(String(20), nullable=False)

    # relationship
    
    @property
    def ref_users(self) -> "List[UserCourse]":
        return filter_from_table(UserCourse, UserCourse.course_id == self.id)


    # repr
    def __repr__(self):
        return f"Course{{ id:{self.id}, location:{self.location}, time_seq:{self.time_seq} }}"

class Some(Base):
    __tablename__ = 'some'

    # primary keys
    id = Column(Integer, Sequence('some_id_seq'), nullable=False, primary_key=True)

    # fields
    name = Column(String(50), unique=True, nullable=False)

    # relationship
    
    @property
    def ref_users(self) -> "List[UserSome]":
        return filter_from_table(UserSome, UserSome.some_id == self.id)


    # repr
    def __repr__(self):
        return f"Some{{ id:{self.id}, name:{self.name} }}"

class UserItem(Base):
    __tablename__ = 'user_item'

    # primary keys
    user_id = Column(Integer, primary_key=True)
    item_id = Column(Integer, primary_key=True)

    # fields
    some = Column(String(50))

    # relationship
    
    @property
    def user(self) -> "Optional[User]":
        return filter_from_table(User, User.id == self.user_id).first()

    
    @property
    def item(self) -> "Optional[Item]":
        return filter_from_table(Item, Item.id == self.item_id).first()


    # repr
    def __repr__(self):
        return f"UserItem{{ user_id:{self.user_id}, item_id:{self.item_id}, some:{self.some} }}"

class UserCourse(Base):
    __tablename__ = 'user_course'

    # primary keys
    user_id = Column(Integer, primary_key=True)
    course_id = Column(Integer, primary_key=True)

    # fields
    

    # relationship
    
    @property
    def user(self) -> "Optional[User]":
        return filter_from_table(User, User.id == self.user_id).first()

    
    @property
    def course(self) -> "Optional[Course]":
        return filter_from_table(Course, Course.id == self.course_id).first()


    # repr
    def __repr__(self):
        return f"UserCourse{{ user_id:{self.user_id}, course_id:{self.course_id} }}"

class UserSome(Base):
    __tablename__ = 'user_some'

    # primary keys
    user_id = Column(Integer, primary_key=True)
    some_id = Column(Integer, primary_key=True)

    # fields
    

    # relationship
    
    @property
    def user(self) -> "Optional[User]":
        return filter_from_table(User, User.id == self.user_id).first()

    
    @property
    def some(self) -> "Optional[Some]":
        return filter_from_table(Some, Some.id == self.some_id).first()


    # repr
    def __repr__(self):
        return f"UserSome{{ user_id:{self.user_id}, some_id:{self.some_id} }}"


Base.metadata.create_all(bind=engine)

@DeleteManager.For(User)
def delete_user(entity) -> Optional[dict]:
    ret = {'item': delete_item_from_user(*entity.ref_items),
            'some': delete_some_from_user(*entity.ref_somes),
            'course': delete_course_from_user(*entity.ref_courses)}
    normal_delete_entity(entity)
    return ret

@DeleteManager.For(Item)
def delete_item(entity) -> Optional[dict]:
    ret = {'user': delete_user_from_item(*entity.ref_users)}
    normal_delete_entity(entity)
    return ret

@DeleteManager.For(Course)
def delete_course(entity) -> Optional[dict]:
    ret = {'user': delete_user_from_course(*entity.ref_users)}
    normal_delete_entity(entity)
    return ret

@DeleteManager.For(Some)
def delete_some(entity) -> Optional[dict]:
    ret = {'user': delete_user_from_some(*entity.ref_users)}
    normal_delete_entity(entity)
    return ret

@DeleteManager.For(UserItem)
def delete_user_item(entity) -> Optional[dict]:
    normal_delete_entity(entity)
    return None


@DeleteManager.For(UserCourse)
def delete_user_course(entity) -> Optional[dict]:
    normal_delete_entity(entity)
    return None


@DeleteManager.For(UserSome)
def delete_user_some(entity) -> Optional[dict]:
    normal_delete_entity(entity)
    return None


@DeleteManager.Between(User, Item)
def delete_item_from_user(*relations) -> Optional[Seq[Tuple[Optional[dict], Optional[dict]]]]:
    if not relations:
        return ()
    def __each__(e) -> Tuple[dict, dict]:
        temp = e.item
        l = delete_user_item(e)
        r = delete_item(temp)
        return l, r


    return tuple(__each__(each) for each in relations)


@DeleteManager.Between(User, Some)
def delete_some_from_user(*relations) -> Optional[Seq[Tuple[Optional[dict], Optional[dict]]]]:
    normal_delete_relations(*relations)
    return None

@DeleteManager.Between(User, Course)
def delete_course_from_user(*relations) -> Optional[Seq[Tuple[Optional[dict], Optional[dict]]]]:
    normal_delete_relations(*relations)
    return None

@DeleteManager.Between(Item, User)
def delete_user_from_item(*relations) -> Optional[Seq[Tuple[Optional[dict], Optional[dict]]]]:
    normal_delete_relations(*relations)
    return None

@DeleteManager.Between(Course, User)
def delete_user_from_course(*relations) -> Optional[Seq[Tuple[Optional[dict], Optional[dict]]]]:
    normal_delete_relations(*relations)
    return None

@DeleteManager.Between(Some, User)
def delete_user_from_some(*relations) -> Optional[Seq[Tuple[Optional[dict], Optional[dict]]]]:
    normal_delete_relations(*relations)
    return None


RefTable = {User: {Item: "ref_items", Course: "ref_courses", Some: "ref_somes"}, Item: {User: "ref_users"}, Course: {User: "ref_users"}, Some: {User: "ref_users"}}

RelationSpec = {User: {'item', 'some', 'course'}, Item: {'user'}, Course: {'user'}, Some: {'user'}, UserItem: set(), UserCourse: set(), UserSome: set()}

RelationSpecForDestruction = {User: {Item: "item"}, Item: {}, Course: {}, Some: {}}

LRType = {User: {Item: UserItem, Course: UserCourse, Some: UserSome}, Item: {User: UserItem}, Course: {User: UserCourse}, Some: {User: UserSome}}

LRRef = {User: {Item: "ref_items", Course: "ref_courses", Some: "ref_somes"}, Item: {User: "ref_users"}, Course: {User: "ref_users"}, Some: {User: "ref_users"}}

FieldSpec = {User: {'sex', 'nickname', 'openid', 'account', 'permission', 'id', 'password'}, Item: {'id', 'cost', 'name'}, Course: {'id', 'time_seq', 'location'}, Some: {'id', 'name'}}
