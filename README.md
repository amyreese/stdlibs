# stdlibs

Simple list of top-level packages in Python's stdlib

[![license](https://img.shields.io/pypi/l/stdlibs.svg)](https://github.com/omnilib/stdlibs/blob/master/LICENSE)
[![version](https://img.shields.io/pypi/v/stdlibs.svg)](https://pypi.org/project/stdlibs)
[![changelog](https://img.shields.io/badge/change-log-blue)](https://stdlibs.omnilib.dev/en/latest/changelog.html)
[![documentation](https://readthedocs.org/projects/stdlibs/badge/?version=latest)](https://stdlibs.omnilib.dev)

This package provides a static listing of all known modules in the Python standard
library, with separate lists available for each major release dating back to Python 2.3.
It also includes combined lists of all module names that were ever available in any
3.x release, any 2.x release, or both.

Note: On Python versions 3.10 or newer, a list of module names for the active runtime
is available `sys.stdlib_module_names`. This package exists to provide an historical
record for use with static analysis and other tooling.

This package only includes listings for CPython releases. If other runtimes would be
useful, open an issue and start a discussion on how best that can be accomodated.


Install
-------

You can install it from PyPI:

```shell-session
$ pip install stdlibs
```


Usage
-----

The recommended usage is to reference `stdlibs.module_names` — the top-level
names that are valid in some version of Python 3.x on some platform.  This is a
superset of top-level names you may have, and a superset of those in
`sys.stdlib_module_names`.

```pycon
>>> from stdlibs import module_names
>>> print("os" in module_names)
True
>>> print("peg_parser" in module_names)  # 3.9+
True

```

If you need a specific version, those are available as other modules:

```pycon
>>> from stdlibs.py36 import module_names as module_names_py36
>>> print("os" in module_names_py36)
True
>>> print("peg_parser" in module_names_py36)
False

```

If you intend to process more than one version, you may find the string api
easier:

```pycon
>>> from stdlibs import stdlib_module_names, KNOWN_VERSIONS
>>> [v for v in KNOWN_VERSIONS if "dataclasses" in stdlib_module_names(v)]
['3.7', '3.8', '3.9', '3.10', '3.11']
>>>
>>> sorted(stdlib_module_names("3.7") - stdlib_module_names("3.6"))
['_abc', '_contextvars', '_py_abc', '_queue', '_uuid', '_xxtestfuzz', 'contextvars', 'dataclasses']
>>>
>>> from moreorless.click import unified_diff
>>> prev = None
>>> buf = []
>>> for v in KNOWN_VERSIONS:
...     cur = ''.join([f"{name}\n" for name in sorted(stdlib_module_names(v))])
...     if prev:
...         buf.append(unified_diff(prev, cur, f"new-in-{v}"))
...     prev = cur
>>> print(''.join(''.join(buf).splitlines(True)[:10]), end='')
--- a/new-in-2.4
+++ b/new-in-2.4
@@ -19,7 +19,6 @@
 DocXMLRPCServer
 ERRNO
 EasyDialogs
-FCNTL
 FILE
 FL
 FileDialog

```

Regenerating
------------

Add or update the list of releases and download URLs in `stdlibs/fetch.py`, then
execute the `stdlibs.fetch` module:

```shell-session
$ make distclean virtualenv
$ source .venv/bin/activate
(.venv) $ python -m stdlibs.fetch
```


License
-------

stdlibs is copyright [Amethyst Reese](https://noswap.com), and licensed under
the MIT license.  I am providing code in this repository to you under an open
source license.  This is my personal repository; the license you receive to
my code is from me and not from my employer. See the `LICENSE` file for details.

