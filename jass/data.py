import os
import logging
import datetime
from peewee import (
    SqliteDatabase,
    Model,
    BooleanField,
    CharField,
    TextField,
    DateTimeField,
    ForeignKeyField,
)


LOGGER = logging.getLogger(__name__)

db = SqliteDatabase('.jass.db')


class Content(Model):
    data = TextField()

    class Meta:
        database = db


class Render(Model):
    data = TextField()

    class Meta:
        database = db


class Document(Model):
    path = CharField(unique=True)
    st_mtime = DateTimeField()

    is_content_updated = BooleanField(default=False)
    is_render_updated = BooleanField(default=False)

    content = ForeignKeyField(Content, related_name='document', null=True)
    render = ForeignKeyField(Render, related_name='document', null=True)

    updated = DateTimeField()  # when this model was modified

    class Meta:
        database = db

    @classmethod
    def add(cls, path, st_mtime):
        try:
            doc = cls.select().where(Document.path == path).get()
            outofdate = doc.st_mtime != st_mtime
            doc.is_content_updated = doc.is_content_updated or outofdate
            doc.is_render_updated = doc.is_render_updated or outofdate
            doc.st_mtime = st_mtime
            doc.updated = datetime.datetime.now()
            doc.save()
            return False
        except cls.DoesNotExist:
            LOGGER.debug('Adding file %s', path)
            doc = cls.create(
                path=path,
                st_mtime=st_mtime,
                updated=datetime.datetime.now(),
                uptodate=False,
            )
            doc.save()
            return True

    @classmethod
    def remove_older_than(cls, date):
        return cls.delete().where(cls.updated < date).execute()

    @classmethod
    def count_content_outofdate(cls):
        return cls.select().where(cls.is_content_updated == False).count()


class Property(Model):
    document = ForeignKeyField(Document, related_name='property')
    key = CharField(max_length=32)
    value = CharField()

    class Meta:
        database = db


def initialize():
    db.connect()
    db.create_tables([Content, Render, Document, Property], safe=True)
