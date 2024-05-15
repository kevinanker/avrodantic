import fastavro.schema

from typing import Iterable

from avrodantic.helper import concat_imports

from avrodantic.schemas import (
    PRIMITIVE_TYPES,
    LOGICAL_TYPES,
    Union,
    Record,
    Enum,
    Array,
    Map,
    Fixed,
    Schema,
    NamedType,
)


def parse_from_avro(avro: str | dict | list, named_schemas: dict[str, Schema]) -> Schema:
    # parse named or primitive schemas
    if isinstance(avro, str):
        if avro in named_schemas:
            return named_schemas[avro]
        elif avro in PRIMITIVE_TYPES:
            return PRIMITIVE_TYPES[avro]
        else:
            raise ValueError(f"Unknown schema: '{avro}' is not primitive and not defined.")

    # parse complex schemas
    elif isinstance(avro, dict):
        avro_type = avro["type"]
        if isinstance(avro_type, list):
            return Union.from_avro(avro_type, named_schemas, parser=parse_from_avro)
        if isinstance(avro_type, str):
            if avro_type == "record":
                return Record.from_avro(avro, named_schemas, parser=parse_from_avro)
            elif avro_type == "enum":
                return Enum.from_avro(avro)
            elif avro_type == "array":
                return Array.from_avro(avro, named_schemas, parser=parse_from_avro)
            elif avro_type == "map":
                return Map.from_avro(avro, named_schemas, parser=parse_from_avro)
            elif avro_type == "fixed":
                return Fixed.from_avro(avro)
            elif avro_type in PRIMITIVE_TYPES and "logicalType" in avro:
                logical_type = avro["logicalType"]
                try:
                    return LOGICAL_TYPES[logical_type].from_avro(avro)
                except KeyError:
                    raise ValueError(f"Unknown logical type: '{logical_type}' is not supported.")
        return parse_from_avro(avro_type, named_schemas)

    # parse union (list) of schemas
    elif isinstance(avro, list):
        return Union.from_avro(avro, named_schemas, parser=parse_from_avro)


def __create_pydantic_code(schemas: list[NamedType], imports: dict[str, str]) -> str:
    printable = ""
    # imports
    for key in sorted(imports.keys()):
        printable += f"from {key} import {", ".join(sorted(imports[key]))}\n"
    printable += "\n\n"
    # classes
    printable += "\n\n\n".join([s.to_pydantic() for s in schemas])
    printable += "\n"
    return printable


def __parse_avro(schema_path: str) -> Iterable[NamedType]:
    schema = fastavro.schema.load_schema(schema_path)
    fa_parsed_schema = fastavro.schema.parse_schema(schema)
    fa_named_schemas: dict = fa_parsed_schema.get("__named_schemas")

    named_schemas: dict[str, Schema] = {}
    for name, schema in reversed(fa_named_schemas.items()):
        named_schemas |= {name: parse_from_avro(schema, named_schemas)}

    return named_schemas.values()


def avro_to_pydantic(avro_file: str, pydantic_file: str | None = None) -> str:
    schemas = __parse_avro(schema_path=avro_file)
    imports = concat_imports([schema.imports for schema in schemas])
    code = __create_pydantic_code(schemas=schemas, imports=imports)

    if pydantic_file is None:
        return code
    else:
        # save the result in a file
        with open(pydantic_file, mode="+w") as f:
            f.write(code)
