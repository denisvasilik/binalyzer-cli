import os
import click

from binalyzer import XMLTemplateParser


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
        with open(os.path.expanduser(args[1]), "r") as template_file:
            template = XMLTemplateParser(template_file.read()).parse()
            return self._autocomplete(template, incomplete)

    def _autocomplete(self, template, incomplete):
        template_path = str.split(incomplete, ".")
        prefix = ".".join(i for i in template_path[:-1])
        if prefix:
            prefix += "."
        if template.id == template_path[0]:
            templates = self._find_templates_by_incomplete(template, template_path[1:])
            return [prefix + s.id for s in templates]
        else:
            return [template.id]

    def _find_templates_by_incomplete(self, template, template_path):
        if len(template_path) == 1:
            return self._get_suggestion(template, template_path[0])
        else:
            for template_child in template.children:
                if template_path[0] == template_child.id:
                    return self._find_templates_by_incomplete(
                        template_child, template_path[1:]
                    )
            else:
                return []

    def _get_suggestion(self, template, incomplete):
        return [
            template_child
            for template_child in template.children
            if incomplete in template_child.id
        ]


class TemplateParamType(click.ParamType):
    name = "template"

    def convert(self, value, param, ctx):
        template_file = ctx.params["template_file"]
        template = XMLTemplateParser(template_file.read()).parse()
        template_path = str.split(value, ".")
        return self._find_template(template, template_path[1:])

    def _find_template(self, template, template_path):
        if len(template_path) == 0:
            return template
        else:
            for child in template.children:
                if template_path[0] == child.id:
                    return self._find_template(child, template_path[1:])
        return None


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

        if not version_option is None:
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
