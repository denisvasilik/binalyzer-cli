import os
import click

import hexdump

from binalyzer import (
    Binalyzer,
    Template,
    ResolvableValue,
    XMLTemplateParser,
    utils,
    __version__,
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


BASED_INT = BasedIntParamType()


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


@click.group()
@click.version_option(__version__)
@click.pass_context
def cli(ctx):
    pass


@cli.command()
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
    _binalyzer = Binalyzer()
    _binalyzer.template = template
    _binalyzer.stream = file

    if output:
        output.write(template.value)
    else:
        hexdump.hexdump(template.value, template.offset.value)


@cli.command()
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
    _binalyzer = Binalyzer()
    _binalyzer.template = template_path.root
    _binalyzer.stream = file

    if output:
        output.write(template_path.value)
    else:
        hexdump.hexdump(template_path.value, template_path.offset.value)

    return 0


def dump_all(template):
    stream = template.binding_context.stream
    stream.seek(0)
    data = stream.read()
    content = ""
    for x in ["{0:02X}".format(x) for x in data]:
        content += f'"{x}", '
    return content[:-2]


def visitTemplate(template, fn):
    value = '{ "data": ['
    value += dump_all(template)
    value += '], "template": { '
    value += fn(template)
    value = visitTemplates(template.children, fn, value)
    return value + "} }"


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


@cli.command()
@click.argument("file", type=ExpandedFile("rb"))
@click.argument("template_file", type=ExpandedFile("r"), required=False)
def json(file, template_file):
    binalyzer = Binalyzer()
    binalyzer.stream = file
    binalyzer.template = Template(id="root")

    if template_file:
        template = XMLTemplateParser(template_file.read()).parse()
        binalyzer.template = template.root

    print(visitTemplate(binalyzer.template, to_json))
