# Development Guidelines

Binalyzer spans accross several GitHub repositories. This project uses
[Google's Repo tool][repo] to work with multiple repositories. The following
sections describe how to setup a development workspace.

* [binalyzer]
* [binalyzer-core]
* [binalyzer-cli]
* [binalyzer-template-provider]
* [binalyzer-data-provider]
* [binalyzer-rest]
* [binalyzer-lsp]
* [binalyzer-docker]
* [binalyzer-wasm]

## Install Repo Tool

Use the following instructions to install the Repo tool.

    ~$ mkdir ~/bin
    ~$ PATH=~/bin:$PATH
    ~$ curl https://storage.googleapis.com/git-repo-downloads/repo > ~/bin/repo
    ~$ chmod a+x ~/bin/repo

Further information regarding the Repo tool can be found [here][repo].

## Clone repositories

After having installed the Repo tool, all project related repositories can be
synced.

    ~git$ mkdir binalyzer && cd binalyzer
    ~git/binalyzer$ repo init -u https://github.com/denisvasilik/binalyzer
    ~git/binalyzer$ repo sync

Now, the workspace is ready for development.

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

## Continuous Test (CT)

Continuous testing is provided by [Travis] (for unit tests and style checks
on Linux).

[Travis]: https://travis-ci.org/denisvasilik/binalyzer
[repo]:https://gerrit.googlesource.com/git-repo/+/refs/heads/master/README.md
[binalyzer]: https://github.com/denisvasilik/binalyzer
[binalyzer-core]: https://github.com/denisvasilik/binalyzer-core
[binalyzer-cli]: https://github.com/denisvasilik/binalyzer-cli
[binalyzer-template-provider]: https://github.com/denisvasilik/binalyzer-template-provider
[binalyzer-data-provider]: https://github.com/denisvasilik/binalyzer-data-provider
[binalyzer-rest]: https://github.com/denisvasilik/binalyzer-rest
[binalyzer-lsp]: https://github.com/denisvasilik/binalyzer-lsp
[binalyzer-docker]: https://github.com/denisvasilik/binalyzer-docker
[binalyzer-wasm]: https://github.com/denisvasilik/binalyzer-wasm