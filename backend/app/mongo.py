"""MongoDB transactional unit of work for the application's bounded query API.

SQLAlchemy model metadata remains the shared schema; no SQL engine is used for
MongoDB. Only the explicit expressions below are supported. Unknown expressions
fail closed. This lets assessment/auth services retain one business-logic path.
"""

import copy
import re
import time
from functools import lru_cache

from pymongo import MongoClient, ReturnDocument
from pymongo.read_concern import ReadConcern
from pymongo.write_concern import WriteConcern
from sqlalchemy import UniqueConstraint
from sqlalchemy.sql import operators
from sqlalchemy.sql.dml import Delete, Update
from sqlalchemy.sql.elements import BindParameter, BooleanClauseList, False_, Null, True_

from .config import settings


@lru_cache
def client():
    return MongoClient(
        settings().database_url,
        serverSelectionTimeoutMS=10000,
        connectTimeoutMS=10000,
        appname="PrepFaang",
        retryWrites=True,
    )


def database():
    return client()[settings().database_name]


def collection_name(model):
    return settings().user_collection if model.__tablename__ == "users" else model.__tablename__


def model_for(table):
    from .db import Base

    return next(m.class_ for m in Base.registry.mappers if m.local_table.name == table.name)


def literal(value):
    if isinstance(value, BindParameter):
        return value.value
    if isinstance(value, True_):
        return True
    if isinstance(value, False_):
        return False
    if isinstance(value, Null):
        return None
    raise ValueError("Unsupported query value")


def predicate(expression):
    if isinstance(expression, BooleanClauseList):
        operation = (
            "$and" if expression.operator is operators.and_ else "$or" if expression.operator is operators.or_ else None
        )
        if not operation:
            raise ValueError("Unsupported boolean expression")
        return {operation: [predicate(c) for c in expression.clauses]}
    op, key, value = expression.operator, expression.left.name, literal(expression.right)
    mapping = {
        operators.eq: "$eq",
        operators.ne: "$ne",
        operators.gt: "$gt",
        operators.ge: "$gte",
        operators.lt: "$lt",
        operators.le: "$lte",
        operators.in_op: "$in",
        operators.not_in_op: "$nin",
        operators.is_: "$eq",
        operators.is_not: "$ne",
    }
    if op in mapping:
        return {key: {mapping[op]: value}}
    if op in (operators.ilike_op, operators.like_op):
        regex = "^" + "".join(".*" if c == "%" else "." if c == "_" else re.escape(c) for c in value) + "$"
        return {key: {"$regex": regex, "$options": "i" if op is operators.ilike_op else ""}}
    raise ValueError("Unsupported MongoDB query operator")


def where(statement):
    clauses = [predicate(c) for c in statement._where_criteria]
    return {"$and": clauses} if clauses else {}


class Results:
    def __init__(self, values=(), rowcount=0):
        self.values, self.rowcount = list(values), rowcount

    def __iter__(self):
        return iter(self.values)

    def all(self):
        return self.values

    def scalar_one(self):
        if len(self.values) != 1:
            raise ValueError("Expected one result")
        return self.values[0]


class MongoSession:
    supports_deferred_ids = True

    def __init__(self):
        self.session = None
        self.identity = {}
        self.original = {}
        self.pending = []

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.rollback()
        if self.session:
            self.session.end_session()

    def transaction(self):
        if self.session is None:
            self.session = client().start_session()
        if not self.session.in_transaction:
            self.session.start_transaction(read_concern=ReadConcern("snapshot"), write_concern=WriteConcern("majority"))
        return self.session

    def collection(self, model):
        return database()[collection_name(model)]

    @staticmethod
    def key(row):
        primary = list(type(row).__table__.primary_key.columns)[0].name
        return type(row), getattr(row, primary)

    @staticmethod
    def values(row):
        return {c.name: copy.deepcopy(getattr(row, c.name)) for c in type(row).__table__.columns}

    def materialize(self, model, document):
        if document is None:
            return None
        values = {c.name: document.get(c.name) for c in model.__table__.columns}
        key = (model, document[list(model.__table__.primary_key.columns)[0].name])
        if key not in self.identity:
            self.identity[key] = model(**values)
            self.original[key] = copy.deepcopy(values)
        return self.identity[key]

    def add(self, row):
        for column in type(row).__table__.columns:
            if getattr(row, column.name) is None and column.default is not None:
                default = column.default
                setattr(row, column.name, default.arg(None) if default.is_callable else copy.deepcopy(default.arg))
        if all(existing is not row for existing in self.pending) and self.key(row) not in self.identity:
            self.pending.append(row)

    def flush(self):
        grouped = {}
        for row in self.pending:
            values = self.values(row)
            primary = list(type(row).__table__.primary_key.columns)[0].name
            grouped.setdefault(type(row), []).append({"_id": values[primary], **values})
            key = self.key(row)
            self.identity[key], self.original[key] = row, copy.deepcopy(values)
        for model, documents in grouped.items():
            self.collection(model).insert_many(documents, session=self.transaction())
        self.pending.clear()
        for key, row in list(self.identity.items()):
            values = self.values(row)
            changes = {name: value for name, value in values.items() if value != self.original[key].get(name)}
            if changes:
                if "updated_at" in values:
                    row.updated_at = time.time()
                    changes["updated_at"] = row.updated_at
                self.collection(type(row)).update_one({"_id": key[1]}, {"$set": changes}, session=self.transaction())
                self.original[key] = self.values(row)

    def get(self, model, key):
        self.flush()
        if (model, key) in self.identity:
            return self.identity[(model, key)]
        return self.materialize(model, self.collection(model).find_one({"_id": key}, session=self.transaction()))

    def scalars(self, statement):
        self.flush()
        if statement._setup_joins:
            raise ValueError("Use explicit repository lookups instead of joins in MongoDB")
        desc = statement.column_descriptions[0]
        model, expr = desc["entity"], desc["expr"]
        query = where(statement)
        sort = [
            (getattr(o, "element", o).name, -1 if getattr(o, "modifier", None) is operators.desc_op else 1)
            for o in statement._order_by_clauses
        ]
        if statement._for_update_arg is not None:
            document = self.collection(model).find_one_and_update(
                query,
                {"$inc": {"_lock": 1}},
                return_document=ReturnDocument.AFTER,
                session=self.transaction(),
                **({"sort": sort} if sort else {}),
            )
            documents = [document] if document else []
        else:
            cursor = self.collection(model).find(query, session=self.transaction())
            if sort:
                cursor = cursor.sort(sort)
            if statement._offset_clause is not None:
                cursor = cursor.skip(statement._offset_clause.value)
            if statement._limit_clause is not None:
                cursor = cursor.limit(statement._limit_clause.value)
            documents = list(cursor)
        values = [self.materialize(model, doc) if expr is model else doc.get(expr.key) for doc in documents]
        if statement._distinct:
            values = list(dict.fromkeys(values))
        return Results(values)

    def scalar(self, statement):
        values = self.scalars(statement).all()
        return values[0] if values else None

    def execute(self, statement):
        self.flush()
        model = model_for(statement.table)
        collection, query = self.collection(model), where(statement)
        if isinstance(statement, Delete):
            documents = list(collection.find(query, {"_id": 1}, session=self.transaction()))
            result = collection.delete_many(query, session=self.transaction())
            for doc in documents:
                key = (model, doc["_id"])
                self.identity.pop(key, None)
                self.original.pop(key, None)
            return Results(rowcount=result.deleted_count)
        if not isinstance(statement, Update):
            raise ValueError("Unsupported MongoDB operation")
        sets, increments = {}, {}
        for key, value in statement._values.items():
            key = key if isinstance(key, str) else key.name
            if getattr(value, "operator", None) is operators.add:
                if value.left.name != key:
                    raise ValueError("Only same-field increments are supported")
                increments[key] = literal(value.right)
            else:
                sets[key] = literal(value)
        operation = {**({"$set": sets} if sets else {}), **({"$inc": increments} if increments else {})}
        documents = list(collection.find(query, {"_id": 1}, session=self.transaction()))
        result = collection.update_many(query, operation, session=self.transaction())
        returned = []
        for doc in documents:
            fresh = collection.find_one({"_id": doc["_id"]}, session=self.transaction())
            key = (model, doc["_id"])
            if key in self.identity:
                for column in model.__table__.columns:
                    setattr(self.identity[key], column.name, copy.deepcopy(fresh.get(column.name)))
                self.original[key] = self.values(self.identity[key])
            if statement._returning:
                returned.append(fresh.get(statement._returning[0].name))
        return Results(returned, result.matched_count)

    def delete(self, row):
        self.flush()
        key = self.key(row)
        self.collection(type(row)).delete_one({"_id": key[1]}, session=self.transaction())
        self.identity.pop(key, None)
        self.original.pop(key, None)

    def refresh(self, row):
        document = self.collection(type(row)).find_one({"_id": self.key(row)[1]}, session=self.transaction())
        for column in type(row).__table__.columns:
            setattr(row, column.name, copy.deepcopy(document.get(column.name)))
        self.original[self.key(row)] = self.values(row)

    def commit(self):
        self.flush()
        if self.session and self.session.in_transaction:
            self.session.commit_transaction()

    def rollback(self):
        if self.session and self.session.in_transaction:
            self.session.abort_transaction()
        self.identity.clear()
        self.original.clear()
        self.pending.clear()


def ensure_indexes():
    from . import models  # noqa: F401
    from .db import Base

    for mapper in Base.registry.mappers:
        model, table = mapper.class_, mapper.local_table
        collection = database()[collection_name(model)]
        # Create collections outside transactions before first use.
        if collection.name not in database().list_collection_names():
            database().create_collection(collection.name)
        for column in table.columns:
            if column.unique or column.index:
                collection.create_index(column.name, unique=bool(column.unique), sparse=True)
        for constraint in table.constraints:
            if isinstance(constraint, UniqueConstraint) and len(constraint.columns) > 1:
                collection.create_index([(c.name, 1) for c in constraint.columns], unique=True)
        for index in table.indexes:
            if len(index.columns) > 1:
                collection.create_index([(c.name, 1) for c in index.columns], unique=index.unique)


if __name__ == "__main__":
    ensure_indexes()
    print("MongoDB collections and indexes are ready.")
