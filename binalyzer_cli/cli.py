import os
import click

import hexdump

from binalyzer import (
    Binalyzer,
    Template,
    SimpleTemplateProvider,
    ResolvableValue,
    XMLTemplateParser,
    __version__,
    BufferedIODataProvider,
)


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


<<<<<<< HEAD
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
=======
@click.group()
@click.version_option(__version__)
@click.pass_context
def binalyzer(ctx):
    pass


@binalyzer.command()
@click.argument("file", type=ExpandedFile("rb"))
@click.option("--start-offset", default="0", type=BASED_INT)
@click.option("--end-offset", default="0", type=BASED_INT)
@click.option("--output", default=None, type=ExpandedFile("wb"))
def dump(file, start_offset, end_offset, output):
    """Dump file content using optional start and end positions.
    """
    file.seek(0, 2)
    size = file.tell()

    if end_offset and end_offset < start_offset:
        raise RuntimeError("The given end offset is smaller than the start offset.")

    if end_offset and end_offset > (start_offset + size):
        end_offset = start_offset + size

    if end_offset:
        size = end_offset - start_offset

    template = Template()
    template.offset = ResolvableValue(start_offset)
    template.size = ResolvableValue(size)
    template_provider = SimpleTemplateProvider(template)
    data_provider = BufferedIODataProvider(file)
    binalyzer = Binalyzer(template_provider, data_provider)
    binalyzer.template = template

    if output:
        output.write(template.value)
    else:
        hexdump.hexdump(template.value, template.offset.value)


@binalyzer.command()
@click.argument("file", type=ExpandedFile("rb"))
@click.argument("template_file", type=ExpandedFile("r"))
@click.argument(
    "template_path",
    type=TemplateParamType(),
    autocompletion=TemplateAutoCompletion().autocompletion,
)
@click.option("--output", default=None, type=ExpandedFile("wb"))
def template(file, template_file, template_path, output):
    """Dump file content using a template.
    """
    template_provider = SimpleTemplateProvider(template_path.root)
    data_provider = BufferedIODataProvider(file)
    binalyzer = Binalyzer(template_provider, data_provider)
    binalyzer.template = template_path.root

    if output:
        output.write(template_path.value)
    else:
        hexdump.hexdump(template_path.value, template_path.offset.value)

    return 0


def dump_all(template):
    data = template.binding_context.data
    data.seek(0)
    data = data.read()
    content = ""
    for x in ["{0:02X}".format(x) for x in data]:
        content += f'"{x}", '
    return content[:-2]
>>>>>>> 092cd5aa5841499bd0a0ee39eddfc323227c5f75

        if not version_option is None:
            params.append(version_option)

        click.Group.__init__(self, params=params, **extra)
        self._loaded_plugin_commands = False

<<<<<<< HEAD
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
=======

def visitTemplates(templates, fn, value):
    if not len(templates):
        return value
    value += ', "children": [{'
    for child in templates:
        value += fn(child)
        value = visitTemplates(child.children, fn, value)
        value += " }, {"
    value = value[:-3]
    value += "] "
    return value


def to_json(template):
    maxLineCharacter = 16
    startLine = int(template.offset.value / maxLineCharacter)
    startCharacter = int(template.offset.value % maxLineCharacter) * 3
    endLine = int((template.offset.value + template.size.value) / maxLineCharacter)
    endCharacter = (
        int((template.offset.value + template.size.value) % maxLineCharacter) * 3
    )

    content = ""
    for x in ["{0:02X}".format(x) for x in template.value]:
        content += f'"{x}", '
    content = content[:-2]

    return (
        '"id": "'
        + template.id
        + '", "offset": '
        + str(template.offset.value)
        + ', "size": '
        + str(template.size.value)
        + ', "start": { "line": '
        + str(startLine)
        + ', "character": '
        + str(startCharacter)
        + ' }, "end": { "line": '
        + str(endLine)
        + ', "character": '
        + str(endCharacter)
        + ' }, "data": ['
        + content
        + "]"
    )


@binalyzer.command()
@click.argument("file", type=ExpandedFile("rb"))
@click.argument("template_file", type=ExpandedFile("r"), required=False)
def json(file, template_file):
    template = Template(id="root")
    template_provider = SimpleTemplateProvider(template)
    data_provider = BufferedIODataProvider(file)
    binalyzer = Binalyzer(template_provider, data_provider)
    binalyzer.template = template

    if template_file:
        template = XMLTemplateParser(template_file.read()).parse()
        binalyzer.template = template.root

    print(visitTemplate(binalyzer.template, to_json))


def customized_hexdump(data, offset, result="print"):
    """
  Transform binary data to the hex dump text format:
  00000000: 00 00 00 00 00 00 00 00  00 00 00 00 00 00 00 00  ................
    [x] data argument as a binary string
    [x] data argument as a file like object
  Returns result depending on the `result` argument:
    'print'     - prints line by line
    'return'    - returns single string
    'generator' - returns generator that produces lines
  """
    if hexdump.PY3K and type(data) == str:
        raise TypeError("Abstract unicode data (expected bytes sequence)")

    gen = hexdump.dumpgen(data, offset)
    if result == "generator":
        return gen
    elif result == "return":
        return "\n".join(gen)
    elif result == "print":
        for line in gen:
            print(line)
    else:
        raise ValueError("Unknown value of `result` argument")


def customized_dumpgen(data, offset):
    """
  Generator that produces strings:
  '00000000: 00 00 00 00 00 00 00 00  00 00 00 00 00 00 00 00  ................'
  """
    generator = hexdump.genchunks(data, 16)
    for addr, d in enumerate(generator):
        # 00000000:
        line = "%08X: " % ((addr * 16) + offset)
        # 00 00 00 00 00 00 00 00  00 00 00 00 00 00 00 00
        dumpstr = hexdump.dump(d)
        line += dumpstr[: 8 * 3]
        if len(d) > 8:  # insert separator if needed
            line += " " + dumpstr[8 * 3 :]
        # ................
        # calculate indentation, which may be different for the last line
        pad = 2
        if len(d) < 16:
            pad += 3 * (16 - len(d))
        if len(d) <= 8:
            pad += 1
        line += " " * pad

        for byte in d:
            # printable ASCII range 0x20 to 0x7E
            if not hexdump.PY3K:
                byte = ord(byte)
            if 0x20 <= byte <= 0x7E:
                line += chr(byte)
            else:
                line += "."
        yield line


hexdump.__dict__["hexdump"] = customized_hexdump
hexdump.__dict__["dumpgen"] = customized_dumpgen
>>>>>>> 092cd5aa5841499bd0a0ee39eddfc323227c5f75
