"""
    binalyzer_cli.commands
    ~~~~~~~~~~~~~~~~~~~~~~

    This module implements commands provided by Binalyzer's command line
    interface.

    :copyright: 2021 Denis Vasilík
    :license: MIT, see LICENSE for details.
"""

import os
import click
import hexdump

from binalyzer import (
    Binalyzer,
    Template,
    ValueProperty,
    XMLTemplateParser,
    TemplateProvider,
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
        raise RuntimeError(
            "The given end offset is smaller than the start offset.")

    if end_offset and end_offset > (start_offset + size):
        end_offset = start_offset + size

    if end_offset:
        size = end_offset - start_offset

    template = Template()
    template.offset = start_offset
    template.size = size
    binalyzer = Binalyzer(template, file)
    binalyzer.template = template

    if output:
        output.write(template.value)
    else:
        hexdump.hexdump(template.value, template.offset)


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
    binalyzer = Binalyzer(template_path.root, file)
    binalyzer.template = template_path.root

    if output:
        output.write(template_path.value)
    else:
        hexdump.hexdump(template_path.value, template_path.offset)

    return 0


def dump_all(template):
    data = template.binding_context.data
    data.seek(0)
    data = data.read()
    content = ""
    for x in ["{0:02X}".format(x) for x in data]:
        content += f'"{x}", '
    return content[:-2]


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
            line += " " + dumpstr[8 * 3:]
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
