from datetime import date, datetime, time, timedelta, timezone
from uuid import UUID

from avrodantic import schemas
from hypothesis import given
from hypothesis import strategies as st


@given(st.uuids())
def test_UUID_value_to_code(uuid):
    schema = schemas.UUID()
    result = schema.value_to_code(value=uuid)

    assert isinstance(result, str)
    assert result.startswith("UUID")

    obj: UUID = eval(result)
    assert isinstance(obj, UUID)
    assert obj == uuid


@given(st.integers(min_value=-500_000, max_value=500_000))
def test_Date_value_to_code(days):
    schema = schemas.Date()
    result = schema.value_to_code(value=days)

    assert isinstance(result, str)
    assert result.startswith("date")

    obj: date = eval(result)
    assert isinstance(obj, date)
    assert obj == date(1970, 1, 1) + timedelta(days=days)


@given(st.integers(min_value=0, max_value=24 * 60 * 60 * 1_000 - 1))
def test_TimeMillis_value_to_code(millis):
    schema = schemas.TimeMillis()
    result = schema.value_to_code(value=millis)

    assert isinstance(result, str)
    assert result.startswith("time")

    obj: time = eval(result)
    assert isinstance(obj, time)
    assert datetime.combine(date(1970, 1, 1), obj) == datetime(1970, 1, 1) + timedelta(milliseconds=millis)


@given(st.integers(min_value=0, max_value=24 * 60 * 60 * 1_000_000 - 1))
def test_TimeMicros_value_to_code(micros):
    schema = schemas.TimeMicros()
    result = schema.value_to_code(value=micros)

    assert isinstance(result, str)
    assert result.startswith("time")

    obj: time = eval(result)
    assert isinstance(obj, time)
    assert datetime.combine(date(1970, 1, 1), obj) == datetime(1970, 1, 1) + timedelta(microseconds=micros)


@given(st.integers(min_value=-2_000_000_000_000, max_value=2_000_000_000_000))
def test_TimestampMillis_value_to_code(millis):
    schema = schemas.TimestampMillis()
    result = schema.value_to_code(value=millis)

    assert isinstance(result, str)
    assert result.startswith("datetime")

    obj: datetime = eval(result)
    assert isinstance(obj, datetime)
    assert obj == datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(milliseconds=millis)


@given(st.integers(min_value=-2_000_000_000_000_000, max_value=2_000_000_000_000_000))
def test_TimestampMicros_value_to_code(micros):
    schema = schemas.TimestampMicros()
    result = schema.value_to_code(value=micros)

    assert isinstance(result, str)
    assert result.startswith("datetime")

    obj: datetime = eval(result)
    assert isinstance(obj, datetime)
    assert obj == datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(microseconds=micros)


@given(st.integers(min_value=-2_000_000_000_000, max_value=2_000_000_000_000))
def test_LocalTimestampMillis_value_to_code(millis):
    schema = schemas.LocalTimestampMillis()
    result = schema.value_to_code(value=millis)

    assert isinstance(result, str)
    assert result.startswith("datetime")

    obj: datetime = eval(result)
    assert isinstance(obj, datetime)
    assert obj == datetime(1970, 1, 1) + timedelta(milliseconds=millis)


@given(st.integers(min_value=-2_000_000_000_000_000, max_value=2_000_000_000_000_000))
def test_LocalTimestampMicros_value_to_code(micros):
    schema = schemas.LocalTimestampMicros()
    result = schema.value_to_code(value=micros)

    assert isinstance(result, str)
    assert result.startswith("datetime")

    obj: datetime = eval(result)
    assert isinstance(obj, datetime)
    assert obj == datetime(1970, 1, 1) + timedelta(microseconds=micros)
