from peewee import (
    CharField,
    DateField,
    ForeignKeyField,
    IntegerField,
    Model,
    PostgresqlDatabase,
    TextField,
    TimestampField,
)

from db import get_database_settings


database = PostgresqlDatabase(None)


def connect_database():
    settings = get_database_settings()
    database.init(
        settings["database"],
        host=settings["host"],
        port=settings["port"],
        user=settings["user"],
        password=settings["password"],
    )
    database.connect(reuse_if_open=True)
    return database


class BaseModel(Model):
    class Meta:
        database = database


class Student(BaseModel):
    student_id = IntegerField(primary_key=True, column_name="student_id")

    class Meta:
        table_name = "students"


class Dorm(BaseModel):
    dorm_id = IntegerField(primary_key=True, column_name="dorm_id")
    dorm_number = IntegerField()
    address = CharField(max_length=150)

    class Meta:
        table_name = "dorms"


class User(BaseModel):
    user_id = IntegerField(primary_key=True, column_name="user_id")
    first_name = CharField(max_length=50)
    last_name = CharField(max_length=50)
    email = CharField(max_length=150)
    date_of_birth = DateField(null=True)
    registration_date = DateField(null=True)
    status = CharField(max_length=20)
    dorm = ForeignKeyField(
        Dorm,
        column_name="dorm_id",
        backref="users",
        null=True,
        lazy_load=False,
    )

    class Meta:
        table_name = "users"


class Announcement(BaseModel):
    id = IntegerField(primary_key=True)
    dorm = ForeignKeyField(Dorm, column_name="dorm_id", lazy_load=False)
    author = ForeignKeyField(User, column_name="author_id", lazy_load=False)
    title = CharField(max_length=150)
    body = TextField()
    created_at = TimestampField(utc=True)

    class Meta:
        table_name = "announcements"


class Vacancy(BaseModel):
    vacancy_id = IntegerField(primary_key=True, column_name="vacancy_id")
    company_name = CharField(max_length=100)
    job_name = CharField(max_length=100)

    class Meta:
        table_name = "vacancies"


class Application(BaseModel):
    application_id = IntegerField(primary_key=True, column_name="application_id")
    student = ForeignKeyField(
        Student,
        column_name="student_id",
        backref="applications",
        lazy_load=False,
    )
    vacancy = ForeignKeyField(
        Vacancy,
        column_name="vacancy_id",
        backref="applications",
        lazy_load=False,
    )
    application_date = DateField(column_name="application_date")
    status = CharField(max_length=20)

    class Meta:
        table_name = "applications"


def close_database():
    if not database.is_closed():
        database.close()
