from sqlalchemy import (create_engine, Integer, String,
                        DateTime, ForeignKey, Sequence,
                        SmallInteger, Enum, Date, Table)
from sqlalchemy import Column as _Column
from sqlalchemy.orm import scoped_session, sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from typing import Dict, Set, Any, List, Callable, Tuple, Type, Optional, Sequence as Seq


from customs import *


class Config:
    database_url: str
    database_connect_options: dict



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
    ref_items: "List[UserItem]" = relationship('UserItem', back_populates='user')
    ref_courses: "List[UserCourse]" = relationship('UserCourse', back_populates='user')
    ref_somes: "List[UserSome]" = relationship('UserSome', back_populates='user')

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
    ref_users: "List[UserItem]" = relationship('UserItem', back_populates='item')

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
    ref_users: "List[UserCourse]" = relationship('UserCourse', back_populates='course')

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
    ref_users: "List[UserSome]" = relationship('UserSome', back_populates='some')

    # repr
    def __repr__(self):
        return f"Some{{ id:{self.id}, name:{self.name} }}"

class UserItem(Base):
    __tablename__ = 'user_item'

    # primary keys
    user_id = Column(Integer, ForeignKey("user.id"), primary_key=True)
    item_id = Column(Integer, ForeignKey("item.id"), primary_key=True)

    # fields
    some = Column(String(50))

    # relationship
    item: "Item" = relationship('Item', back_populates='ref_users', uselist=False)
    user: "User" = relationship('User', back_populates='ref_items', uselist=False)

    # repr
    def __repr__(self):
        return f"UserItem{{ user_id:{self.user_id}, item_id:{self.item_id}, some:{self.some} }}"

class UserCourse(Base):
    __tablename__ = 'user_course'

    # primary keys
    user_id = Column(Integer, ForeignKey("user.id"), primary_key=True)
    course_id = Column(Integer, ForeignKey("course.id"), primary_key=True)

    # fields


    # relationship
    course: "Course" = relationship('Course', back_populates='ref_users', uselist=False)
    user: "User" = relationship('User', back_populates='ref_courses', uselist=False)

    # repr
    def __repr__(self):
        return f"UserCourse{{ user_id:{self.user_id}, course_id:{self.course_id} }}"

class UserSome(Base):
    __tablename__ = 'user_some'

    # primary keys
    user_id = Column(Integer, ForeignKey("user.id"), primary_key=True)
    some_id = Column(Integer, ForeignKey("some.id"), primary_key=True)

    # fields


    # relationship
    some: "Some" = relationship('Some', back_populates='ref_users', uselist=False)
    user: "User" = relationship('User', back_populates='ref_somes', uselist=False)

    # repr
    def __repr__(self):
        return f"UserSome{{ user_id:{self.user_id}, some_id:{self.some_id} }}"


@DeleteManager.For(User)
def delete_user(entity) -> Optional[dict]:
    ret = {'item': delete_item_from_user(*entity.ref_items),
            'course': delete_course_from_user(*entity.ref_courses),
            'some': delete_some_from_user(*entity.ref_somes)}
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
        r = delete_item(e.item)
        l = delete_user_item(e)
        return l, r


    return tuple(__each__(each) for each in relations)


@DeleteManager.Between(User, Course)
def delete_course_from_user(*relations) -> Optional[Seq[Tuple[Optional[dict], Optional[dict]]]]:
    normal_delete_relations(*relations)
    return None

@DeleteManager.Between(User, Some)
def delete_some_from_user(*relations) -> Optional[Seq[Tuple[Optional[dict], Optional[dict]]]]:
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

