from pathlib import Path

import typer
from rich.progress import track

from avrodantic.parser import avro_to_pydantic

app = typer.Typer(no_args_is_help=True, add_completion=False)


@app.command()
def parse(avro: Path, pydantic: Path, overwrite: bool = False, prefix: str = "", suffix: str = ""):
    # check pydantic path (must be existing directory)
    if not pydantic.exists():
        raise ValueError(f"{pydantic} does not exist.")
    if not pydantic.is_dir():
        raise ValueError(f"{pydantic} is not a directory.")

    # build iteratable avro files
    if avro.is_dir():
        avro_files = [file for file in avro.glob("*.avsc") if file.is_file()]
    elif avro.is_file():
        avro_files = [avro]
    else:
        raise ValueError(f"{avro} is not a file or folder.")

    # create pydantic file names and raise overwrite error
    if pydantic.exists() and pydantic.is_dir():
        pydantic_files: dict[Path, Path] = {f: Path(pydantic, prefix + f.stem + suffix + ".py") for f in avro_files}
        if not overwrite:
            for f in pydantic_files.values():
                if f.exists():
                    raise PermissionError(f"{f} does already exists. Use --overwrite.")

    # parse avro files one by one and save them as pydantic files
    for avro_file in track(avro_files, description="Processing..."):
        code = avro_to_pydantic(avro_path=avro_file)
        with open(pydantic_files[avro_file], mode="w") as f:
            f.write(code)


if __name__ == "__main__":
    app()
