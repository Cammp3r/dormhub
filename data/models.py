from peewee import (
    CharField,
    ForeignKeyField,
    IntegerField,
    Model,
    PostgresqlDatabase,
    DateField,
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
