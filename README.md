# Binalyzer Command Line Interface (CLI)

## Documentation

Documentation is available from [binalyzer.readthedocs.io].

[binalyzer.readthedocs.io]: https://binalyzer.readthedocs.io/en/latest/

## Get in touch

- Report bugs, suggest features or view the source code [on GitHub].
- For contributions refer to [the contributors guide].

[on GitHub]: https://github.com/denisvasilik/binalyzer

## Continuous Integration (CI)

This repository contains a `.travis.yml` and a `ci` folder which both are used
for CI.

### Pre-Commit Hooks

This repository provides `pre-commit` and `pre-push` hooks. They are installed
using the following commands:

```console
~$ pre-commit install -t pre-commit
~$ pre-commit install -t pre-push
```

The following command runs the hooks and checks all files.

```console
~$ pre-commit run --all-files --hook-stage push
```

# License

Licensed under the MIT license ([LICENSE-MIT] or http://opensource.org/licenses/MIT).

[the contributors guide]: CONTRIBUTING.md
[LICENSE-MIT]: LICENSE.rst
