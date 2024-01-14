#!/usr/bin/env python3

import os
import string
import textwrap

def build(template, page_path):
    new_arg = True
    key = None
    value_buf = []
    template_vars = {}

    with open(page_path, "r") as f:
        for i, line in enumerate(f):
            line = line.rstrip()
            if new_arg:
                assert line != "---", f"unexpected break on line {i + 1}"
                key = line
                new_arg = False
            else:
                if line == "---":
                    template_vars[key] = "\n".join(value_buf)
                    new_arg = True
                    value_buf = []
                else:
                    value_buf.append(line)
        template_vars[key] = "\n".join(value_buf)

    template_vars["content"] = textwrap.indent(template_vars["content"], "    " * 6)

    return template.substitute(template_vars)

def main():
    script_path = os.path.realpath(__file__)
    templating_dir = os.path.dirname(script_path)
    with open(os.path.join(templating_dir, "_template.html"), "r") as f:
        template = string.Template(f.read())
    for fname in os.listdir(templating_dir):
        if fname.endswith(".html") and not fname.startswith("_"):
            html = build(template, os.path.join(templating_dir, fname))
            with open(os.path.join(templating_dir, "..", fname), "w") as f:
                f.write(html)

if __name__ == "__main__":
    main()