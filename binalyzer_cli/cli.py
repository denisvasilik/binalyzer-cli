"""
    binalyzer_cli.cli
    ~~~~~~~~~~~~~~~~~

    This module implements Binalyzer's command line interface.

    :copyright: 2021 Denis Vasilík
    :license: MIT, see LICENSE for details.
"""

import os
import click
import importlib
import hexdump
import pkg_resources

from anytree import Resolver
from anytree.resolver import ResolverError
from anytree.search import findall

from binalyzer import (
    Binalyzer,
    Template,
    TemplateProvider,
    ValueProperty,
    XMLTemplateParser,
    __version__,
    BufferedIODataProvider,
)

_BINALYZER_PACKAGES = [
    "binalyzer",
    "binalyzer_core",
    "binalyzer_cli",
    "binalyzer_data_provider",
    "binalyzer_template_provider",
    "binalyzer_rest",
    "binalyzer_wasm"
]


def print_version(ctx, _param, value):
    if not value or ctx.resilient_parsing:
        return

    for package_name in _BINALYZER_PACKAGES:
        try_print_version_info(package_name, ctx)

    extension_packages = []
    for ep in pkg_resources.iter_entry_points("binalyzer.commands"):
        if not package_name in _BINALYZER_PACKAGES:
            package_name = ep.module_name.split(".")[0]
            extension_packages.append(package_name)

    for package_name in extension_packages:
        try_print_version_info(package_name, ctx)

    ctx.exit()


def try_print_version_info(package_name, ctx):
    click.echo(try_get_version_info(package_name), color=ctx.color)


def try_get_version_info(package_name):
    try:
        package = importlib.import_module(package_name)
        if package.__version__:
            return "{:s} ({:s})".format(package_name, package.__version__)
        else:
            return "{:s} ({:s})".format(package_name, package.__commit__[:7])
    except ImportError:
        return "{:s} not installed".format(package_name)


class BasedIntParamType(click.ParamType):
    """Custom parameter type that accepts hex and octal numbers in addition to
    normal integers, and converts them into regular integers.

    Taken from:

    https://click.palletsprojects.com/en/7.x/parameters/#implementing-custom-types
    """

    name = "integer"

    def convert(self, value, param, ctx):
        try:
            if value[:2].lower() == "0x":
                return int(value[2:], 16)
            elif value[:1] == "0":
                return int(value, 8)
            return int(value, 10)
        except TypeError:
            self.fail(
                "expected string for int() conversion, got "
                f"{value!r} of type {type(value).__name__}",
                param,
                ctx,
            )
        except ValueError:
            self.fail(f"{value!r} is not a valid integer", param, ctx)


class TemplateAutoCompletion(object):
    def autocompletion(self, ctx, args, incomplete):
        with open(os.path.expanduser(args[2]), "r") as template_file:
            template = XMLTemplateParser(template_file.read()).parse()
            return self._autocomplete(template, incomplete)

    def _autocomplete(self, template, incomplete):
        template_path = str.split(incomplete, ".")
        prefix = ".".join(i for i in template_path[:-1])
        if prefix:
            prefix += "."
        if template.name == template_path[0]:
            templates = self._find_templates_by_incomplete(
                template, template_path[1:])
            return [prefix + s.name for s in templates]
        else:
            return [template.name]

    def _find_templates_by_incomplete(self, template, template_path):
        if len(template_path) == 1:
            return self._get_suggestion(template, template_path[0])
        else:
            for template_child in template.children:
                if template_path[0] == template_child.name:
                    return self._find_templates_by_incomplete(
                        template_child, template_path[1:]
                    )
            else:
                return []

    def _get_suggestion(self, template, incomplete):
        retval = findall(
            template, lambda template_child: incomplete in template_child.name)
        return retval


class TemplateParamType(click.ParamType):
    name = "template"

    def convert(self, value, param, ctx):
        template_file = ctx.params["template_file"]
        template_string = template_file.read()
        template = XMLTemplateParser(template_string).parse()
        template_path = "/" + value.replace(".", "/")
        return Resolver('name').get(template, template_path)


class ExpandedFile(click.File):
    def convert(self, value, *args, **kwargs):
        value = os.path.expanduser(value)
        return super(ExpandedFile, self).convert(value, *args, **kwargs)


class BinalyzerGroup(click.Group):
    def __init__(
        self,
        add_default_commands=True,
        create_app=None,
        version_option=None,
        load_dotenv=True,
        set_debug_flag=True,
        **extra,
    ):
        params = list(extra.pop("params", None) or ())

        if version_option is None:
            version_option = click.Option(
                ["--version"],
                help="Show the Binalyzer version",
                expose_value=False,
                callback=print_version,
                is_flag=True,
                is_eager=True,
            )

        params.append(version_option)

        click.Group.__init__(self, params=params, **extra)
        self._loaded_plugin_commands = False

    def _load_plugin_commands(self):
        if self._loaded_plugin_commands:
            return
        try:
            import pkg_resources
        except ImportError:
            self._loaded_plugin_commands = True
            return

        for ep in pkg_resources.iter_entry_points("binalyzer.commands"):
            self.add_command(ep.load(), ep.name)
        self._loaded_plugin_commands = True

    def get_command(self, ctx, name):
        self._load_plugin_commands()

        # Load built-in commands
        return click.Group.get_command(self, ctx, name)

    def list_commands(self, ctx):
        self._load_plugin_commands()
        rv = set(click.Group.list_commands(self, ctx))
        return sorted(rv)

    def main(self, *args, **kwargs):
        # Set a global flag that indicates that we were invoked from the
        # command line interface. This is detected by Binalyzer.run to make the
        # call into a no-op. This is necessary to avoid ugly errors when the
        # script that is loaded here also attempts to start a server.
        os.environ["BINALYZER_RUN_FROM_CLI"] = "true"

        kwargs.setdefault("auto_envvar_prefix", "BINALYZER")
        return super(BinalyzerGroup, self).main(*args, **kwargs)
