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


class DataStore(Model):
    plugin = CharField()
    kind = CharField()
    key = CharField()
    value = CharField()

    class Meta:
        database = db


class Document(Model):
    path = CharField(unique=True)
    relative_path = CharField(unique=True)
    output_path = CharField(unique=True, null=True)
    st_mtime = DateTimeField()

    is_body_updated = BooleanField(default=False)
    is_render_updated = BooleanField(default=False)

    summary = TextField(null=True)
    body = TextField(null=True)
    render = TextField(null=True)
    template = CharField(null=True)

    updated = DateTimeField()  # when this model was modified

    class Meta:
        database = db

    @classmethod
    def add(cls, path, relative_path, st_mtime):
        try:
            doc = cls.select().where(Document.path == path).get()

            doc.relative_path = relative_path
            if doc.st_mtime != st_mtime:
                doc.is_body_updated = False
                doc.is_render_updated = False
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
    def count_body_outdated(cls):
        return cls.get_body_outdated().count()

    @classmethod
    def get_body_outdated(cls):
        return cls.select().where(cls.is_body_updated == False or cls.body == None)

    @classmethod
    def count_render_outdated(cls):
        return cls.get_render_outdated().count()

    @classmethod
    def get_render_outdated(cls):
        return cls.select().where(cls.is_render_updated == False)

    @classmethod
    def get_by_path_or_none(cls, path):
        try:
            return cls.select().where(cls.path == path).get()
        except cls.DoesNotExist:
            return None

    @classmethod
    def dump_all(cls):
        for d in cls.select():
            d.dump()

    def dump(self):
        print(
            '{relative_path} {is_body_updated} {is_render_updated}'
            .format(**self._data)
        )

    def add_property(self, key, value):
        try:
            prop = Property.select().where(Property.document == self, Property.key == key).get()
            prop.value = value
        except Property.DoesNotExist:
            prop = Property.create(document=self, key=key, value=value)
        prop.save()

    def get_properties_as_dict(self):
        def inner():
            for prop in self.properties:
                yield prop.key, prop.value
        return dict(inner())


class Property(Model):
    document = ForeignKeyField(Document, related_name='properties')
    key = CharField(max_length=32)
    value = CharField()

    class Meta:
        database = db


def initialize():
    db.connect()
    db.create_tables([Document, Property, DataStore], safe=True)
