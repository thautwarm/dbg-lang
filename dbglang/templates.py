from sqlalchemy import (create_engine, Integer, String,
                        DateTime, ForeignKey, Sequence,
                        SmallInteger, Enum, Date, Table)
from sqlalchemy import Column as _Column
from sqlalchemy.orm import scoped_session, sessionmaker, Session as _Session
from sqlalchemy.ext.declarative import declarative_base
from typing import Dict, Set, Any, List, Callable, Tuple, Type, Optional, Generic, TypeVar, Sequence as Seq, Union, \
    Generator
from abc import abstractmethod
from collections import defaultdict

T = TypeVar('T')


class Config:
    database_url: str
    database_connect_options: dict
    ##{config}##


class Session(_Session, scoped_session):

    @abstractmethod
    def query(self, *fields) -> 'Query':
        raise NotImplemented



class ITable:
    query: 'Query[ITable]'
    
class Query(Generic[T]):

    @abstractmethod
    def __iter__(self) -> 'Generator[T, None, None]':
        raise NotImplemented

    @abstractmethod
    def slice(self, start: int, stop: int):
        """
        Computes the "slice" of the :class:`.Query` represented by
        the given indices and returns the resulting :class:`.Query`.

        The start and stop indices behave like the argument to Python's
        built-in :func:`range` function. This method provides an
        alternative to using ``LIMIT``/``OFFSET`` to get a slice of the
        query.

        For example, ::

            session.query(User).order_by(User.id).slice(1, 3)

        renders as

        .. sourcecode:: sql

           SELECT users.id AS users_id,
                  users.name AS users_name
           FROM users ORDER BY users.id
           LIMIT ? OFFSET ?
           (2, 1)

        .. seealso::

           :meth:`.Query.limit`

           :meth:`.Query.offset`
        """
        raise NotImplemented

    @abstractmethod
    def first(self) -> 'Optional[T]':
        """
        apply the given filtering criterion to a copy
        of this :class:`.Query`, using SQL expressions.

        e.g.::

            session.query(MyClass).filter(MyClass.name == 'some name')

        Multiple criteria may be specified as comma separated; the effect
        is that they will be joined together using the :func:`.and_`
        function::

            session.query(MyClass).\
                filter(MyClass.name == 'some name', MyClass.id > 5)

        The criterion is any SQL expression object applicable to the
        WHERE clause of a select.   String expressions are coerced
        into SQL expression constructs via the :func:`.text` construct.

        .. seealso::

            :meth:`.Query.filter_by` - filter on keyword expressions.
        """
        raise NotImplemented

    @abstractmethod
    def filter(self, *criterion) -> 'Query[T]':
        """
        apply the given filtering criterion to a copy
    of this :class:`.Query`, using SQL expressions.

    e.g.::

        session.query(MyClass).filter(MyClass.name == 'some name')

    Multiple criteria may be specified as comma separated; the effect
    is that they will be joined together using the :func:`.and_`
    function::

        session.query(MyClass).\
            filter(MyClass.name == 'some name', MyClass.id > 5)

    The criterion is any SQL expression object applicable to the
    WHERE clause of a select.   String expressions are coerced
    into SQL expression constructs via the :func:`.text` construct.

    .. seealso::

        :meth:`.Query.filter_by` - filter on keyword expressions.
        """
        raise NotImplemented

    @abstractmethod
    def filter_by(self, **kwargs) -> 'Query[T]':
        """
        apply the given filtering criterion to a copy
    of this :class:`.Query`, using keyword expressions.

    e.g.::

        session.query(MyClass).filter_by(name = 'some name')

    Multiple criteria may be specified as comma separated; the effect
    is that they will be joined together using the :func:`.and_`
    function::

        session.query(MyClass).\
            filter_by(name = 'some name', id = 5)

    The keyword expressions are extracted from the primary
    entity of the query, or the last entity that was the
    target of a call to :meth:`.Query.join`.

    .. seealso::

        :meth:`.Query.filter` - filter on SQL expressions.
        """
        raise NotImplemented

    @abstractmethod
    def all(self) -> 'List[T]':
        raise NotImplemented

    @abstractmethod
    def order_by(self, *criterion) -> 'Query[T]':
        """
        apply one or more ORDER BY criterion to the query and return
        the newly resulting ``Query``

        All existing ORDER BY settings can be suppressed by
        passing ``None`` - this will suppress any ORDER BY configured
        on mappers as well.

        Alternatively, passing False will reset ORDER BY and additionally
        re-allow default mapper.order_by to take place.   Note mapper.order_by
        is deprecated.
        """
        raise NotImplemented

    @abstractmethod
    def count(self) -> int:
        """
        Return a count of rows this Query would return.

        This generates the SQL for this Query as follows::

            SELECT count(1) AS count_1 FROM (
                SELECT <rest of query follows...>
            ) AS anon_1

        .. versionchanged:: 0.7
            The above scheme is newly refined as of 0.7b3.

        For fine grained control over specific columns
        to count, to skip the usage of a subquery or
        otherwise control of the FROM clause,
        or to use other aggregate functions,
        use :attr:`~sqlalchemy.sql.expression.func`
        expressions in conjunction
        with :meth:`~.Session.query`, i.e.::

            from sqlalchemy import func

            # count User records, without
            # using a subquery.
            session.query(func.count(User.id))

            # return count of user "id" grouped
            # by "name"
            session.query(func.count(User.id)).\
                    group_by(User.name)

            from sqlalchemy import distinct

            # count distinct "name" values
            session.query(func.count(distinct(User.name)))
        """

    @abstractmethod
    def select_from(self, *from_obj: 'table name'):
        """
        Set the FROM clause of this :class:`.Query` explicitly.

        :meth:`.Query.select_from` is often used in conjunction with
        :meth:`.Query.join` in order to control which entity is selected
        from on the "left" side of the join.

        The entity or selectable object here effectively replaces the
        "left edge" of any calls to :meth:`~.Query.join`, when no
        joinpoint is otherwise established - usually, the default "join
        point" is the leftmost entity in the :class:`~.Query` object's
        list of entities to be selected.

        A typical example::

            q = session.query(Address).select_from(User).\
                join(User.addresses).\
                filter(User.name == 'ed')

        Which produces SQL equivalent to::

            SELECT address.* FROM user
            JOIN address ON user.id=address.user_id
            WHERE user.name = :name_1

        :param \*from_obj: collection of one or more entities to apply
         to the FROM clause.  Entities can be mapped classes,
         :class:`.AliasedClass` objects, :class:`.Mapper` objects
         as well as core :class:`.FromClause` elements like subqueries.

        .. versionchanged:: 0.9
            This method no longer applies the given FROM object
            to be the selectable from which matching entities
            select from; the :meth:`.select_entity_from` method
            now accomplishes this.  See that method for a description
            of this behavior.

        .. seealso::

            :meth:`~.Query.join`

            :meth:`.Query.select_entity_from`
        """
        raise NotImplemented

    @abstractmethod
    def limit(self, n: int) -> 'Query[T]':
        """Apply a ``LIMIT`` to the query and return the newly resulting ``Query``."""
        raise NotImplemented

    @abstractmethod
    def offset(self, offset: int):
        """Apply an ``OFFSET`` to the query and return the newly resulting ``Query``."""
        raise NotImplemented


##{custom_lib}##


def filter_from_table(table, cond):
    return getattr(table, 'query').filter(cond)


engine = create_engine(Config.database_url,
                       convert_unicode=True,
                       **Config.database_connect_options)

db_session: Session = scoped_session(
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

def normal_delete_relations(*relations):
    for each in relations:
        db_session.delete(each)


class Column:
    def __new__(cls, t, *args, **kwargs):
        if 'sqlalchemy' not in t.__module__:
            t = Enum(t)
        return _Column(t, *args, **kwargs)


##{table_def}##

Base.metadata.create_all(bind=engine)

##{methods}##
