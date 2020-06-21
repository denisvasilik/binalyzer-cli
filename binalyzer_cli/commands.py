import os
import click
import hexdump

from binalyzer import (
    Binalyzer,
    Template,
    ResolvableValue,
    XMLTemplateParser,
    SimpleTemplateProvider,
    BufferedIODataProvider,
    __version__,
)

from .cli import (
    BasedIntParamType,
    TemplateParamType,
    ExpandedFile,
    TemplateAutoCompletion,
)

BASED_INT = BasedIntParamType()

@click.command()
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


@click.command()
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
    template_provider = DefaultSimpleTemplateProvider(template_path.root)
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


@click.command()
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
