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
    relative_path = CharField(unique=True)
    output_path = CharField(unique=True, null=True)
    st_mtime = DateTimeField()

    is_content_updated = BooleanField(default=False)
    is_render_updated = BooleanField(default=False)
    is_generated = BooleanField(default=False)

    content = ForeignKeyField(Content, related_name='document', null=True)
    render = ForeignKeyField(Render, related_name='document', null=True)

    updated = DateTimeField()  # when this model was modified

    class Meta:
        database = db

    @classmethod
    def add(cls, path, relative_path, st_mtime):
        try:
            doc = cls.select().where(Document.path == path).get()
            updated = doc.st_mtime == st_mtime

            doc.relative_path = relative_path
            doc.is_content_updated = updated
            doc.is_render_updated = doc.is_render_updated and updated
            doc.st_mtime = st_mtime
            doc.updated = datetime.datetime.now()
            doc.save()
            return False
        except cls.DoesNotExist:
            LOGGER.debug('Adding file %s', path)
            doc = cls.create(
                path=path,
                relative_path=relative_path,
                st_mtime=st_mtime,
                updated=datetime.datetime.now(),
                uptodate=False,
            )
            return True

    @classmethod
    def remove_older_than(cls, date):
        return cls.delete().where(cls.updated < date).execute()

    @classmethod
    def count_content_outofdate(cls):
        return cls.select().where(cls.is_content_updated == False).count()

    @classmethod
    def get_content_outdated(cls):
        return cls.select().where(cls.is_content_updated == False)

    @classmethod
    def count_render_outofdate(cls):
        return cls.select().where(cls.is_render_updated == False).count()

    @classmethod
    def get_render_outdated(cls):
        return cls.select().where(cls.is_render_updated == False)

    @classmethod
    def get_by_path_or_none(cls, path):
        try:
            return cls.select().where(cls.path == path).get()
        except cls.DoesNotExist:
            return None

    def add_property(self, key, value):
        try:
            prop = Property.select().where(Property.document == self, Property.key == key).get()
            prop.value = value
        except Property.DoesNotExist:
            prop = Property.create(document=self, key=key, value=value)
        prop.save()


class Property(Model):
    document = ForeignKeyField(Document, related_name='properties')
    key = CharField(max_length=32)
    value = CharField()

    class Meta:
        database = db


def initialize():
    db.connect()
    db.create_tables([Content, Render, Document, Property], safe=True)
