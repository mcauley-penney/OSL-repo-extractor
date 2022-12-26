### Gotchas
#### Set up and environment
1. Execution yields ModuleImportError: No Module Named 'Symbol'

    Symbol.py [was removed in 3.10 and later](https://github.com/python/cpython/issues/85111). You should first try `pip install --upgrade pip setuptools`. If this does not work, you must downgrade Python to before 3.10. [See here](https://stackoverflow.com/a/70837055) for more info.
