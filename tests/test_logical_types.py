from avrodantic import schemas

from datetime import date, datetime, timedelta
from uuid import UUID

from hypothesis import given, strategies as st


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
