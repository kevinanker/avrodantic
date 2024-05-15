from typing import Literal, Callable, Any, Self

from datetime import date, timedelta, datetime

from avrodantic.helper import concat_imports


class DefaultValue:
    def __init__(self, value: Any) -> None:
        self.value = value


class Schema:
    imports = {}

    @property
    def typing(self) -> str:
        raise NotImplementedError()

    def value_to_code(self, value: str) -> str:
        return value


class NamedType(Schema):
    def __init__(self, name: str) -> None:
        self.name = name

    def to_pydantic(self) -> str:
        raise NotImplementedError()

    @property
    def typing(self) -> str:
        return "".join([s.capitalize() for s in self.name.split(".")])


class Record(NamedType):
    IMPORTS = {"pydantic": ["BaseModel"]}

    class Field:
        def __init__(
            self,
            name: str,
            type: Schema,
            doc: str | None = None,
            default: DefaultValue | None = None,
            aliases: list[str] | None = None,
            order: Literal["ascending", "descending", "ignore"] = "ascending",
        ) -> None:
            self.__name = name
            self.__type = type
            self.__doc = doc
            self.__default = default
            self.__aliases = aliases
            self.__order = order
            self.imports = type.imports

        @classmethod
        def from_avro(cls, avro: dict, named_schemas: dict[str, Schema], parser: Callable[[], Schema]) -> Self:
            return cls(
                name=avro.get("name"),
                type=parser(avro["type"], named_schemas),
                doc=avro.get("doc"),
                default=DefaultValue(value=avro["default"]) if "default" in avro else None,
                aliases=avro.get("aliases"),
                order=avro.get("order"),
            )

        def to_pydantic(self) -> str:
            out = f"{self.__name}: {self.__type.typing}"
            if self.__default is not None:
                out += f" = {self.__type.value_to_code(self.__default.value)}"
            return out

    def __init__(
        self,
        name: str,
        namespace: str | None = None,
        doc: str | None = None,
        aliases: list[str] | None = None,
        fields: list[Field] = [],
    ) -> None:
        self.name = name
        self.namespace = namespace
        self.doc = doc
        self.aliases = aliases
        self.fields = fields
        self.imports = concat_imports([self.IMPORTS] + [field.imports for field in fields])

    @classmethod
    def from_avro(cls, avro: dict, named_schemas: dict[str, Schema], parser: Callable) -> Self:
        avro_fields = avro.get("fields", [])
        fields = [cls.Field.from_avro(field, named_schemas, parser=parser) for field in avro_fields]
        return cls(
            name=avro.get("name"),
            namespace=avro.get("namespace"),
            doc=avro.get("namespace"),
            aliases=avro.get("aliases"),
            fields=fields,
        )

    def to_pydantic(self) -> str:
        out = f"class {self.typing}(BaseModel):"
        if self.doc is not None:
            out += f'\n    """{self.doc}"""\n'
        for field in self.fields:
            out += f"\n    {field.to_pydantic()}"
        return out


class Enum(NamedType):
    imports = {"enum": ["StrEnum"]}

    def __init__(
        self,
        name: str,
        namespace: str | None = None,
        doc: str | None = None,
        aliases: list[str] | None = None,
        symbols: list[str] = [],
        default: str | None = None,
    ) -> None:
        self.name = name
        self.namespace = namespace
        self.doc = doc
        self.aliases = aliases
        self.symbols = symbols
        self.default = default

    @classmethod
    def from_avro(cls, avro: dict) -> Self:
        return cls(
            name=avro.get("name"),
            namespace=avro.get("namespace"),
            doc=avro.get("doc"),
            aliases=avro.get("aliases"),
            symbols=avro.get("symbols"),
            default=avro.get("default"),
        )

    def value_to_code(self, value: str) -> str:
        return f"{self.typing}.{value}"

    def to_pydantic(self) -> str:
        out = f"class {self.typing}(StrEnum):"
        if self.doc is not None:
            out += f'\n    """{self.doc}"""\n'
        for symbol in self.symbols:
            out += f'\n    {symbol} = "{symbol}"'
        if self.default is not None:
            out += f'\n\n    @classmethod\n    def _missing_(cls, value):\n        """Default value"""\n        return cls.{self.default}'
        return out


class Fixed(NamedType):
    imports = {"pydantic": ["conbytes"]}

    def __init__(
        self,
        name: str,
        size: int,
        namespace: str | None = None,
        doc: str | None = None,
        aliases: list[str] | None = None,
    ) -> None:
        self.name = name
        self.size = size
        self.namespace = namespace
        self.doc = doc
        self.aliases = aliases

    @classmethod
    def from_avro(cls, avro: dict) -> Self:
        return cls(
            name=avro.get("name"),
            size=avro.get("size"),
            namespace=avro.get("namespace"),
            doc=avro.get("doc"),
            aliases=avro.get("aliases"),
        )

    def to_pydantic(self) -> str:
        return f"{self.typing}: type[bytes] = conbytes(min_length={self.size}, max_length={self.size})"


class Array(Schema):
    def __init__(self, items: type[Schema], default: list[type[Schema]] = []) -> None:
        self.items = items
        self.default = default
        self.imports = items.imports

    @classmethod
    def from_avro(cls, avro: dict, named_schemas: dict[str, Schema], parser: Callable) -> Self:
        return cls(items=parser(avro["items"], named_schemas), default=avro.get("default"))

    @property
    def typing(self) -> str:
        return f"list[{self.items.typing}]"


class Map(Schema):
    def __init__(self, values: type[Schema], default: dict[str, type[Schema]] = {}) -> None:
        self.values = values
        self.default = default
        self.imports = values.imports

    @classmethod
    def from_avro(cls, avro: dict, named_schemas: dict[str, Schema], parser: Callable) -> Self:
        return cls(values=parser(avro["values"], named_schemas), default=avro.get("default"))

    @property
    def typing(self) -> str:
        return "dict[" + f"str, {self.values.typing}" + "]"


class Union(list[Schema], Schema):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.imports = concat_imports([schema.imports for schema in self])

    @property
    def typing(self) -> str:
        return " | ".join([s.typing for s in self])

    @classmethod
    def from_avro(cls, avro: dict, named_schemas: dict[str, Schema], parser: Callable) -> Self:
        return cls([parser(schema, named_schemas) for schema in avro])

    def value_to_code(self, value: str) -> str:
        return self[0].value_to_code(value)


# Primitive types


class PrimitiveType(Schema):
    primitive_type = ""


class Null(PrimitiveType):
    primitive_type = "null"

    @property
    def typing(self) -> Literal["None"]:
        return "None"

    def value_to_code(self, value) -> Literal["None"]:
        return "None"


class Boolean(PrimitiveType):
    primitive_type = "boolean"

    @property
    def typing(self) -> Literal["bool"]:
        return "bool"

    def value_to_code(self, value: bool) -> str:
        return str(value).capitalize()


class Int(PrimitiveType):
    primitive_type = "int"

    @property
    def typing(self) -> Literal["int"]:
        return "int"


class Long(PrimitiveType):
    primitive_type = "long"

    @property
    def typing(self) -> Literal["int"]:
        return "int"


class Float(PrimitiveType):
    primitive_type = "float"

    @property
    def typing(self) -> Literal["float"]:
        return "float"


class Double(PrimitiveType):
    primitive_type = "double"

    @property
    def typing(self) -> Literal["float"]:
        return "float"


class Bytes(PrimitiveType):
    primitive_type = "bytes"

    @property
    def typing(self) -> Literal["bytes"]:
        return "bytes"


class String(PrimitiveType):
    primitive_type = "string"

    @property
    def typing(self) -> Literal["str"]:
        return "str"

    def value_to_code(self, value: str) -> str:
        return f'"{value}"'


# Logical types


class LogicalType(Schema):
    logical_type = None
    types = []

    @classmethod
    def __validate_avro(cls, avro: dict):
        logical_type = avro.get("logicalType")
        if cls.logical_type != logical_type:
            raise ValueError(f"Wrong logicalType, must be '{cls.logical_type}' not '{logical_type}'.")
        avro_type = avro.get("type")
        if avro_type not in cls.types:
            raise ValueError(f"Wrong type, must be in {cls.types} not '{avro_type}'.")

    @classmethod
    def from_avro(cls, avro: dict) -> Self:
        cls.__validate_avro(avro)
        return cls()


class Decimal(LogicalType):
    logical_type = "decimal"
    types = ["bytes"]

    def __init__(self, precision: int, scale: int = 0) -> None:
        self.precision = precision
        self.scale = scale

    @classmethod
    def __validate_avro(cls, avro: dict):
        logical_type = avro.get("logicalType")
        if cls.logical_type != logical_type:
            raise ValueError(f"Wrong logicalType, must be '{cls.logical_type}' not '{logical_type}'.")
        avro_type = avro.get("type")
        if avro_type not in cls.types:
            raise ValueError(f"Wrong type, must be in {cls.types} not '{avro_type}'.")

    @classmethod
    def from_avro(cls, avro: dict) -> Self:
        cls.__validate_avro(avro)
        return cls(precision=avro.get("precision"), scale=avro.get("scale", 0))

    @property
    def typing(self) -> Literal["float"]:
        return "float"


class UUID(LogicalType):
    logical_type = "uuid"
    types = ["string"]
    imports = {"uuid": ["UUID"]}

    @property
    def typing(self) -> Literal["UUID"]:
        return "UUID"

    def value_to_code(self, value: str) -> str:
        return f'UUID("{value}")'


class Date(LogicalType):
    """The date logical type represents a date within the calendar,
    with no reference to a particular time zone or time of day.

    A date logical type annotates an Avro int, where the int stores
    the number of days from the unix epoch, 1 January 1970 (ISO calendar).
    """

    logical_type = "date"
    types = ["int"]
    imports = {"datetime": ["date"]}

    @property
    def typing(self) -> Literal["date"]:
        return "date"

    def value_to_code(self, value: int) -> str:
        d = date(1970, 1, 1) + timedelta(days=value)
        return f"date({d.year}, {d.month}, {d.day})"


class TimeMillis(LogicalType):
    """The time-millis logical type represents a time of day, with no reference to
    a particular calendar, time zone or date, with a precision of one millisecond.

    A time-millis logical type annotates an Avro int, where the int stores the
    number of milliseconds after midnight, 00:00:00.000.
    """

    logical_type = "time-millis"
    types = ["int"]
    imports = {"datetime": ["time"]}

    @property
    def typing(self) -> Literal["time"]:
        return "time"

    def value_to_code(self, value: int) -> str:
        t = (datetime.min + timedelta(milliseconds=value)).time()
        return f"time({t.hour}, {t.minute}, {t.second}, {t.microsecond})"


class TimeMicros(LogicalType):
    logical_type = "time-micros"
    types = ["long"]
    imports = {"datetime": ["time"]}

    @property
    def typing(self) -> Literal["time"]:
        return "time"

    def value_to_code(self, value: int) -> str:
        t = (datetime.min + timedelta(microseconds=value)).time()
        return f"time({t.hour}, {t.minute}, {t.second}, {t.microsecond})"


class TimestampMillis(LogicalType):
    logical_type = "timestamp-millis"
    types = ["long"]
    imports = {"pydantic": ["AwareDatetime"], "datetime": ["datetime", "timezone"]}

    @property
    def typing(self) -> Literal["AwareDatetime"]:
        return "AwareDatetime"

    def value_to_code(self, value: int) -> str:
        dt = datetime(1970, 1, 1) + timedelta(milliseconds=value)
        return f"datetime({dt.year}, {dt.month}, {dt.day}, {dt.hour}, {dt.minute}, {dt.second}, {dt.microsecond}, timezone.utc)"


class TimestampMicros(LogicalType):
    logical_type = "timestamp-micros"
    types = ["long"]
    imports = {"pydantic": ["AwareDatetime"], "datetime": ["datetime", "timezone"]}

    @property
    def typing(self) -> Literal["AwareDatetime"]:
        return "AwareDatetime"

    def value_to_code(self, value: int) -> str:
        dt = datetime(1970, 1, 1) + timedelta(microseconds=value)
        return f"datetime({dt.year}, {dt.month}, {dt.day}, {dt.hour}, {dt.minute}, {dt.second}, {dt.microsecond}, timezone.utc)"


class LocalTimestampMillis(LogicalType):
    logical_type = "local-timestamp-millis"
    types = ["long"]
    imports = {"pydantic": ["NaiveDatetime"], "datetime": ["datetime"]}

    @property
    def typing(self) -> Literal["NaiveDatetime"]:
        return "NaiveDatetime"

    def value_to_code(self, value: int) -> str:
        dt = datetime(1970, 1, 1) + timedelta(milliseconds=value)
        return f"datetime({dt.year}, {dt.month}, {dt.day}, {dt.hour}, {dt.minute}, {dt.second}, {dt.microsecond})"


class LocalTimestampMicros(LogicalType):
    logical_type = "local-timestamp-micros"
    types = ["long"]
    imports = {"pydantic": ["NaiveDatetime"], "datetime": ["datetime"]}

    @property
    def typing(self) -> Literal["NaiveDatetime"]:
        return "NaiveDatetime"

    def value_to_code(self, value: int) -> str:
        dt = datetime(1970, 1, 1) + timedelta(microseconds=value)
        return f"datetime({dt.year}, {dt.month}, {dt.day}, {dt.hour}, {dt.minute}, {dt.second}, {dt.microsecond})"


PRIMITIVE_TYPES = {t.primitive_type: t() for t in PrimitiveType.__subclasses__()}
LOGICAL_TYPES = {t.logical_type: t for t in LogicalType.__subclasses__()}
