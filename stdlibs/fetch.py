# Copyright 2022 Amethyst Reese
# Licensed under the MIT license

import re
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Set

import libcst as cst
import libcst.matchers as m

BASE_DIR = (Path.cwd() / Path(__file__)).parent
KNOWN_FILE = BASE_DIR / "known.py"
DOCS_DIR = BASE_DIR.parent / "docs"
API_FILE = DOCS_DIR / "api.rst"

RELEASES = {
    "2.3": "https://www.python.org/ftp/python/2.3.7/Python-2.3.7.tgz",
    "2.4": "https://www.python.org/ftp/python/2.4.6/Python-2.4.6.tgz",
    "2.5": "https://www.python.org/ftp/python/2.5.6/Python-2.5.6.tgz",
    "2.6": "https://www.python.org/ftp/python/2.6.9/Python-2.6.9.tgz",
    "2.7": "https://www.python.org/ftp/python/2.7.18/Python-2.7.18.tgz",
    "3.0": "https://www.python.org/ftp/python/3.0.1/Python-3.0.1.tgz",
    "3.1": "https://www.python.org/ftp/python/3.1.5/Python-3.1.5.tgz",
    "3.2": "https://www.python.org/ftp/python/3.2.6/Python-3.2.6.tgz",
    "3.3": "https://www.python.org/ftp/python/3.3.7/Python-3.3.7.tgz",
    "3.4": "https://www.python.org/ftp/python/3.4.10/Python-3.4.10.tgz",
    "3.5": "https://www.python.org/ftp/python/3.5.10/Python-3.5.10.tgz",
    "3.6": "https://www.python.org/ftp/python/3.6.13/Python-3.6.13.tgz",
    "3.7": "https://www.python.org/ftp/python/3.7.10/Python-3.7.10.tgz",
    "3.8": "https://www.python.org/ftp/python/3.8.8/Python-3.8.8.tgz",
    "3.9": "https://www.python.org/ftp/python/3.9.5/Python-3.9.5.tgz",
    "3.10": "https://www.python.org/ftp/python/3.10.2/Python-3.10.2.tgz",
    "3.11": "https://www.python.org/ftp/python/3.11.0/Python-3.11.0b1.tgz",
}

MODULE_DEF_RE = re.compile(r"PyModuleDef .*? = \{\s*[^,]*,\s*([^,}]+)[,}]")
MULTILINE_COMMENT_RE = re.compile(r"/\*.*?\*/")
PY2_INITMODULE_RE = re.compile(r".Py_InitModule\d?\(\s*(?!\))(.*?),")
INITTAB_SELECTOR_RE = re.compile(
    r"(?:struct _(?:frozen|module_alias) .*?|_PyImport_\w+)\[\] = \{([\w\W]+?)\n\};"
)
INITTAB_RE = re.compile(r'{"([^"]+)", ')

# lib2to3 outputs code that doesn't parse, so just omit these lines
PY2_LINES_TO_OMIT = [
    "join(F, fw + '.framework', H)",
    "for fw in 'Tcl', 'Tk'",
    "for fw in ('Tcl', 'Tk')",
    "for H in 'Headers', 'Versions/Current/PrivateHeaders'",
]


with open(__file__) as f:
    MY_COPYRIGHT_HEADER = ""
    while True:
        _line = f.readline()
        if not _line.strip():
            break
        MY_COPYRIGHT_HEADER += _line

GENERATED_TMPL = (
    MY_COPYRIGHT_HEADER
    + '''\

# Generated by stdlibs/fetch.py

from typing import FrozenSet

module_names: FrozenSet[str] = frozenset(
    [
{lines}    ]
)
"""
Known stdlib modules for Python {version}.
"""
'''
)

KNOWN_TMPL = (
    MY_COPYRIGHT_HEADER
    + '''\

# Generated by stdlibs/fetch.py

from typing import List

KNOWN_VERSIONS: List[str] = [
{lines}]
"""All supported Python major releases"""
'''
)

API_ANCHOR = ".. GENERATED\n"
API_TMPL = """
.. module:: stdlibs.{module}

.. autodata:: module_names
    :no-value:
"""


def write_tmpl(module: str, version: str, data: Set[str]) -> None:
    lines = "".join(f'        "{s}",\n' for s in sorted(data))
    (BASE_DIR / f"{module}.py").write_text(
        GENERATED_TMPL.format(lines=lines, version=version)
    )


def regen_all() -> None:
    all2: Set[str] = set()
    all3: Set[str] = set()
    for v in RELEASES:
        names = regen(v)
        if v.startswith("2"):
            all2 |= names
        elif v.startswith("3"):
            all3 |= names
        else:
            raise ValueError("What is this brave new future you live in")

    write_tmpl("py2", "2.x", all2)
    write_tmpl("py3", "3.x", all3)
    write_tmpl("py", "3.x and 2.x", all2 | all3)

    lines = "".join(f'    "{s}",\n' for s in RELEASES)
    KNOWN_FILE.write_text(KNOWN_TMPL.format(lines=lines))
    print("known.py done")

    api_text = API_FILE.read_text()
    api_text, anchor, _ = api_text.partition(API_ANCHOR)
    api_text += anchor

    api_text += API_TMPL.format(module="py3")
    api_text += API_TMPL.format(module="py2")
    api_text += API_TMPL.format(module="py")

    for v in list(RELEASES)[::-1]:
        module = f"py{v.replace('.','')}"
        api_text += API_TMPL.format(module=module)

    API_FILE.write_text(api_text)
    print("api.rst done")

    print("done")


def regen(version: str) -> Set[str]:
    base_path = Path(".cache", RELEASES[version].split("/")[-1].rsplit(".", 1)[0])
    setup_path = base_path / "setup.py"

    if not base_path.exists():
        Path(".cache").mkdir(exist_ok=True)
        subprocess.check_call(["wget", "-c", RELEASES[version]], cwd=".cache")
        subprocess.check_call(
            ["tar", "-xvzf", RELEASES[version].split("/")[-1]], cwd=".cache"
        )
        if version.startswith("2"):
            (base_path / "fixed").mkdir(exist_ok=True)
            subprocess.check_call(
                [
                    sys.executable,
                    "-m",
                    "lib2to3",
                    "-n",
                    "-w",
                    "-o",
                    str(base_path / "fixed"),
                    str(base_path / "setup.py"),
                ]
            )

            # TODO if the extraction succeeded but now this fails, we can end up
            # with a corrupt copy.
            setup_path = base_path / "fixed" / "setup.py"
            lines = setup_path.read_text().splitlines(True)
            lines = [line for line in lines if line.strip() not in PY2_LINES_TO_OMIT]
            setup_path.write_text("".join(lines))
    elif version.startswith("2"):
        setup_path = base_path / "fixed" / "setup.py"

    module = try_parse(setup_path)
    ev = ExtensionVisitor()
    module.visit(ev)

    # Python files
    names = ev.extension_names[:]
    for p in (base_path / "Lib").glob("*"):
        if p.name.startswith(("plat-", "lib-")):
            # 2.x platform dirs, or tk support
            for path in p.iterdir():
                # lib-tk/test on 2.7
                if path.name in ("test",):
                    continue
                # TODO plat-mac/lib-scriptpackages
                if path.is_dir() and not path.name.startswith("lib-"):
                    names.append(path.name)
                elif path.name.endswith(".py"):
                    name = path.with_suffix("").name
                    names.append(name)
        else:
            name = p.with_suffix("").name
            name = name.split(".")[0]  # __phello__.foo
            if name not in ("__pycache__", "site-packages", "test"):
                names.append(name)

    for subdir in (
        "Python",  # builtin
        "Modules",  # other extensions, some of which are built-in :/
        "PC",  # windows
    ):
        for p in (base_path / subdir).glob("*.c"):
            try:
                data = p.read_text()
            except UnicodeDecodeError:
                data = p.read_text(encoding="latin-1")

            match = MODULE_DEF_RE.search(data) or PY2_INITMODULE_RE.search(data)
            if match:
                s = MULTILINE_COMMENT_RE.sub("", match.group(1)).strip()
                if s.startswith(".m_name"):
                    s = s.split("=")[1].strip()

                if s.startswith('"') and s.endswith('"'):
                    names.append(s.strip('"'))
                elif p.name in ("_warnings.c", "_sre.c", "pyexpat.c", "_bsddb.c"):
                    names.append(p.with_suffix("").name)
                elif p.name in ("socketmodule.c", "posixmodule.c"):
                    names.append(p.name.split("module")[0])
                else:
                    print(f"Unknown module for {s} in {p}, skipped")

    # Some names are listed differently/better here; cjkcodecs and _io/io
    for path in (
        base_path / "PC" / "config.c",
        base_path / "PC" / "os2vacpp" / "config.c",
        base_path / "Python" / "frozen.c",
    ):
        if not path.exists():
            continue
        found = False
        for block in INITTAB_SELECTOR_RE.findall(path.read_text()):
            found = True
            for match in INITTAB_RE.finditer(block):
                if match.group(1) == "__main__":
                    continue
                names.append(match.group(1).split(".")[0])
        if not found:
            print(f"Missing inittab in {path}")

    write_tmpl(f"py{version.replace('.', '')}", version, set(names))
    print(f"{version} done.")
    return set(names)


class ExtensionVisitor(cst.CSTVisitor):
    def __init__(self) -> None:
        self.extension_names: List[str] = []

    def visit_Call(self, node: cst.Call) -> None:
        # print(node)
        d = m.extract(
            node,
            m.Call(
                func=m.OneOf(m.Name("Extension"), m.Name("addMacExtension")),
                args=(
                    m.Arg(value=m.SaveMatchedNode(m.SimpleString(), "extension_name")),
                    m.ZeroOrMore(m.DoNotCare()),
                ),
            ),
        )
        if d:
            assert isinstance(d["extension_name"], cst.SimpleString)
            self.extension_names.append(d["extension_name"].evaluated_value)

    def visit_Assign(self, node: cst.Assign) -> None:
        d = m.extract(
            node,
            m.Assign(
                targets=(m.AssignTarget(target=m.Name("CARBON_EXTS")),),
                value=m.SaveMatchedNode(m.List(), "list"),
            ),
        )
        if d:
            assert isinstance(d["list"], cst.List)
            for item in d["list"].elements:
                if isinstance(item.value, cst.SimpleString):
                    self.extension_names.append(item.value.evaluated_value)


# This is from usort
def try_parse(path: Path, data: Optional[bytes] = None) -> cst.Module:
    """
    Attempts to parse the file with all syntax versions known by LibCST.

    If parsing fails on all supported grammar versions, then raises the parser error
    from the first/newest version attempted.
    """
    if data is None:
        data = path.read_bytes()

    parse_error: Optional[cst.ParserSyntaxError] = None

    for version in cst.KNOWN_PYTHON_VERSION_STRINGS[::-1]:
        try:
            mod = cst.parse_module(
                data, cst.PartialParserConfig(python_version=version)
            )
            return mod
        except cst.ParserSyntaxError as e:
            # keep the first error we see in case parsing fails on all versions
            if parse_error is None:
                parse_error = e

    # not caring about existing traceback here because it's not useful for parse
    # errors, and usort_path is already going to wrap it in a custom class
    raise parse_error or Exception("unknown parse failure")


if __name__ == "__main__":
    regen_all()
