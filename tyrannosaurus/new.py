from __future__ import annotations

import logging
import shutil
from pathlib import Path
from subprocess import check_call
from typing import Union, Sequence

import typer

from tyrannosaurus.context import _LiteralParser, _Context
from tyrannosaurus.helpers import (
    _License,
    _Env,
    _InitTomlHelper,
)

logger = logging.getLogger(__package__)
cli = typer.Typer()


class New:
    def __init__(
        self, name: str, license_name: Union[str, _License], username: str, authors: Sequence[str]
    ):
        if isinstance(license_name, str):
            license_name = _License[license_name.lower()]
        self.name = name
        self.license_name = license_name
        self.username = username
        self.authors = authors

    def create(self, path: Path) -> None:
        name = self.name
        self._checkout(path)
        context = _Context(path)
        path = context.path
        toml_path = path / "pyproject.toml"
        parser = _LiteralParser(name, "0.1.0", self.username, self.authors)
        # remove tyrannosaurus-specific files
        # TODO permissionerror
        # os.chmod(str(path/'.git'), stat.S_IWRITE)
        # shutil.rmtree(str(path/'.git'))
        check_call(["rm", "-rf", str(path / ".git")])
        shutil.rmtree(str(path / "docs"))
        shutil.rmtree(str(path / "recipes"))
        # fix toml settings
        lines = toml_path.read_text(encoding="utf8").splitlines()
        env = _Env(user=self.username, authors=self.authors)
        new_lines = _InitTomlHelper(name, env.authors, self.license_name, env.user).fix(lines)
        new_lines = [
            line
            for line in new_lines
            if not line.startswith("grayskull") and not line.startswith("pur")
        ]
        toml_path.write_text("\n".join(new_lines), encoding="utf8")
        # copy license
        license_file = (
            path / "tyrannosaurus" / "resources" / ("license_" + self.license_name.name + ".txt")
        )
        if license_file.exists():
            text = parser.parse(license_file.read_text(encoding="utf8"))
            Path(path / "LICENSE.txt").write_text(text, encoding="utf8")
        # copy resources, overwriting
        for source in (path / "tyrannosaurus" / "resources").iterdir():
            if not Path(source).is_file():
                continue
            resource = Path(source).name
            if not resource.startswith("license_"):
                dest = path / Path(*str(resource).split("$"))
                if dest.name.startswith("-"):
                    dest = Path(*reversed(dest.parents), "." + dest.name[1:])
                dest.parent.mkdir(parents=True, exist_ok=True)
                text = parser.parse(source.read_text(encoding="utf8"))
                dest.write_text(text, encoding="utf8")
        # rename some files
        Path(path / name).mkdir()
        Path(context.path / "recipes" / name).mkdir(parents=True)
        (path / "tyrannosaurus" / "__init__.py").rename(Path(path / name / "__init__.py"))
        shutil.rmtree(str(path / "tyrannosaurus"))

    def _checkout(self, path: Path):
        if path.exists():
            raise FileExistsError("Path {} already exists".format(path))
        path.parent.mkdir(exist_ok=True, parents=True)
        logger.info("Running git clone...")
        check_call(
            ["git", "clone", "https://github.com/dmyersturnbull/tyrannosaurus.git", str(path)]
        )
        logger.info("Got git checkout. Fixing...")


__all__ = ["New"]
