from avrodantic import schemas

from hypothesis import given, strategies as st

from avrodantic.parser import parse_from_avro


PRIMITIVE_TYPES = ["null", "boolean", "int", "long", "float", "double", "bytes", "string"]


@st.composite
def st_avro_primitive(draw):
    return draw(st.sampled_from(PRIMITIVE_TYPES))


@st.composite
def st_avro_logical_decimal(draw):
    type = draw(st.just("bytes"))
    precision = draw(st.integers())
    scale = draw(st.integers())
    return {"type": type, "logicalType": "decimal", "precision": precision, "scale": scale}


@st.composite
def st_avro_logical_uuid(draw):
    return draw(st.just({"type": "string", "logicalType": "uuid"}))


@st.composite
def st_avro_logical_date(draw):
    return draw(st.just({"type": "int", "logicalType": "date"}))


@st.composite
def st_avro_logical_time_millis(draw):
    return draw(st.just({"type": "int", "logicalType": "time-millis"}))


@st.composite
def st_avro_logical_time_micros(draw):
    return draw(st.just({"type": "long", "logicalType": "time-micros"}))


@st.composite
def st_avro_logical_timestamp_millis(draw):
    return draw(st.just({"type": "long", "logicalType": "timestamp-millis"}))


@st.composite
def st_avro_logical_timestamp_micros(draw):
    return draw(st.just({"type": "long", "logicalType": "timestamp-micros"}))


@st.composite
def st_avro_logical_local_timestamp_millis(draw):
    return draw(st.just({"type": "long", "logicalType": "local-timestamp-millis"}))


@st.composite
def st_avro_logical_local_timestamp_micros(draw):
    return draw(st.just({"type": "long", "logicalType": "local-timestamp-micros"}))


@st.composite
def st_avro_logical(draw):
    return draw(
        st.one_of(
            [
                st_avro_logical_decimal(),
                st_avro_logical_uuid(),
                st_avro_logical_date(),
                st_avro_logical_time_millis(),
                st_avro_logical_time_micros(),
                st_avro_logical_timestamp_millis(),
                st_avro_logical_timestamp_micros(),
                st_avro_logical_local_timestamp_millis(),
                st_avro_logical_local_timestamp_micros(),
            ]
        )
    )


@st.composite
def st_avro_record_field(draw, recursions: int = 3):
    name = draw(st.text())
    type = draw(st_avro_type(recursions=recursions))
    doc = draw(st.text())
    aliases = draw(st.text())
    default = None
    order = draw(st.sampled_from(["ascending", "descending", "ignore"]))
    return {"name": name, "type": type, "doc": doc, "default": default, "aliases": aliases, "order": order}


@st.composite
def st_avro_record(draw, max_fields: int = 5, recursions: int = 3):
    name = draw(st.text())
    namespace = draw(st.text())
    doc = draw(st.text())
    aliases = draw(st.text())
    fields = draw(st.lists(st_avro_record_field(recursions=recursions), max_size=max_fields))
    return {"type": "record", "name": name, "namespace": namespace, "doc": doc, "aliases": aliases, "fields": fields}


@st.composite
def st_avro_enum(draw):
    name = draw(st.text())
    symbols = draw(st.lists(st.text()))
    namespace = draw(st.text())
    doc = draw(st.text())
    aliases = draw(st.text())
    default = draw(st.sampled_from(symbols)) if len(symbols) > 0 else None
    return {
        "type": "enum",
        "name": name,
        "symbols": symbols,
        "namespace": namespace,
        "doc": doc,
        "aliases": aliases,
        "default": default,
    }


@st.composite
def st_avro_fixed(draw):
    name = draw(st.text())
    size = draw(st.integers())
    namespace = draw(st.text())
    doc = draw(st.text())
    aliases = draw(st.text())
    return {"type": "fixed", "name": name, "size": size, "namespace": namespace, "doc": doc, "aliases": aliases}


@st.composite
def st_avro_array(draw, recursions: int = 3):
    type = draw(st_avro_type(recursions=recursions))
    return {"type": "array", "items": type}


@st.composite
def st_avro_map(draw, recursions: int = 3):
    type = draw(st_avro_type(recursions=recursions))
    return {"type": "map", "values": type}


@st.composite
def st_avro_union(draw, max_types: int = 3, recursions: int = 3):
    return draw(st.lists(st_avro_type(recursions=recursions), max_size=max_types))


@st.composite
def st_avro_type(draw, recursions: int = 3):
    return draw(
        st.deferred(
            lambda: st.one_of(
                [
                    st_avro_primitive(),
                    st_avro_logical(),
                    st_avro_record(recursions=recursions - 1),
                    st_avro_enum(),
                    st_avro_fixed(),
                    st_avro_array(recursions=recursions - 1),
                    st_avro_map(recursions=recursions - 1),
                    st_avro_union(recursions=recursions - 1),
                ]
                if recursions > 0
                else [
                    st_avro_primitive(),
                    st_avro_logical(),
                    st_avro_enum(),
                    st_avro_fixed(),
                ]
            )
        )
    )


@given(st_avro_primitive())
def test_Primitive_from_avro(avro):
    result = parse_from_avro(avro, {})
    assert isinstance(result, schemas.PrimitiveType)


@given(st_avro_logical())
def test_Logical_from_avro(avro):
    result = parse_from_avro(avro, {})
    assert isinstance(result, schemas.LogicalType)


@given(st_avro_enum())
def test_Enum_from_avro(avro):
    result = parse_from_avro(avro, {})
    assert isinstance(result, schemas.Enum)


@given(st_avro_fixed())
def test_Fixed_from_avro(avro):
    result = parse_from_avro(avro, {})
    assert isinstance(result, schemas.Fixed)


@given(st_avro_record(max_fields=100, recursions=1))
def test_Record_from_avro_flat(avro):
    result = parse_from_avro(avro, {})
    assert isinstance(result, schemas.Record)


@given(st_avro_record(max_fields=3, recursions=10))
def test_Record_from_avro_deep(avro):
    result = parse_from_avro(avro, {})
    assert isinstance(result, schemas.Record)


@given(st_avro_record(max_fields=10, recursions=3))
def test_Record_from_avro_balanced(avro):
    result = parse_from_avro(avro, {})
    assert isinstance(result, schemas.Record)


@given(st_avro_record_field(recursions=1))
def test_Field_from_avro(avro):
    result = schemas.Record.Field.from_avro(avro, {}, parse_from_avro)
    assert isinstance(result, schemas.Record.Field)


@given(st_avro_array(recursions=1))
def test_Array_from_avro(avro):
    result = parse_from_avro(avro, {})
    assert isinstance(result, schemas.Array)


@given(st_avro_map(recursions=1))
def test_Map_from_avro(avro):
    result = parse_from_avro(avro, {})
    assert isinstance(result, schemas.Map)


@given(st_avro_union(max_types=10, recursions=1))
def test_Union_from_avro_flat(avro):
    result = parse_from_avro(avro, {})
    assert isinstance(result, schemas.Union)


@given(st_avro_union(max_types=2, recursions=10))
def test_Union_from_avro_deep(avro):
    result = parse_from_avro(avro, {})
    assert isinstance(result, schemas.Union)


@given(st_avro_union(max_types=4, recursions=3))
def test_Union_from_avro_balanced(avro):
    result = parse_from_avro(avro, {})
    assert isinstance(result, schemas.Union)


@given(st_avro_type(recursions=1))
def test_parse_from_avro(avro):
    result = parse_from_avro(avro, {})
    assert isinstance(result, schemas.Schema)
