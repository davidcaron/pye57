import CppHeaderParser
from CppHeaderParser import CppVariable, CppClass, CppMethod, CppEnum
from typing import List, Dict


def gen_variables(variables: List[CppVariable]):
    out = []
    for var in variables:
        string = 'm.attr("{name}") = {name};'
        name = var["name"]
        if "using" in var["type"]:
            continue
        out.append(string.format(name=name))
    return out


def pybind_overload(method):
    overload_call = "py::overload_cast<{types}>("
    overload_call = overload_call.format(
        types=gen_args_types(method["parameters"]),
    )
    overload_close = ")"
    if method["const"]:
        overload_close = ", py::const_)"
    return overload_call, overload_close


def gen_method(class_name, method: CppMethod, needs_overload=False):
    string = 'cls_{class_name}.def("{name}", {overload_call}&{class_name}::{name}{overload_close}{args});'
    args = ""
    if method["parameters"]:
        args = ", " + gen_args_names(method["parameters"])

    overload_call, overload_close = "", ""
    if needs_overload:
        overload_call, overload_close = pybind_overload(method)

    formatted = string.format(
        class_name=class_name,
        name=method["name"],
        args=args,
        overload_call=overload_call,
        overload_close=overload_close,
    )
    return formatted


def gen_args_types(params: List):
    args_types = []
    for p in params:
        const = "" if not p["constant"] else "const "
        ref = "" if not p["reference"] else " &"
        type_ = p["type"] if p.get("enum") else p["raw_type"]
        ptr = "" if not p["pointer"] else " *"
        args_types.append(const + type_ + ref + ptr)
    return ", ".join(args_types)


def gen_args_names(params: List):
    string = '"{name}"_a{default}'
    args_names = []
    for p in params:
        default = ""
        if p.get("defaultValue"):
            default = "=" + p["defaultValue"].replace(" ", "")
        args_names.append(string.format(name=p["name"], default=default))
    return ", ".join(args_names)


def gen_constructor(class_name, method: CppMethod):
    string = 'cls_{class_name}.def(py::init<{args_types}>(){args_names});'
    args_names = gen_args_names(method["parameters"])
    formatted = string.format(
        class_name=class_name,
        args_types=gen_args_types(method["parameters"]),
        args_names=", " + args_names if args_names else "",
    )
    return formatted


def gen_classes(classes: Dict[str, CppClass]):
    out = []
    for name, class_ in classes.items():
        string = 'py::class_<{name}> cls_{name}(m, "{name}");'
        out.append(string.format(name=name))
        method_names = [m["name"] for m in class_["methods"]["public"]]
        for method in class_["methods"]["public"]:
            if "operator" in method["name"]:
                continue
            if method["constructor"]:
                if name in ["Node", "E57Exception"]:
                    continue
                out.append(gen_constructor(name, method))
            elif method["destructor"]:
                continue
            elif method["name"] in ("dump", "report"):
                continue
            else:
                needs_overload = method_names.count(method["name"]) >= 2
                out.append(gen_method(name, method, needs_overload=needs_overload))
        out.append("")
    out.append("")

    return out


def gen_enums(enums: List[CppEnum]):
    out = []
    for e in enums:
        enum_lines = ['py::enum_<{name}>(m, "{name}")']
        for value in e["values"]:
            enum_lines.append('    .value("%s", {name}::%s)' % (value["name"], value["name"]))
        enum_lines.append("    .export_values();")
        for line in enum_lines:
            out.append(line.format(name=e["name"]))
    return out


def generate_lines(lines, indent=""):
    line_break = "\n" + indent
    return indent + line_break.join(lines)


def main(path):
    base_indent = "    "
    header = CppHeaderParser.CppHeader(path)
    variables = gen_variables(header.variables)
    enums = gen_enums(header.enums)
    classes = gen_classes(header.classes)
    print(generate_lines(variables + enums + classes, base_indent))


if __name__ == '__main__':
    path = "../libE57Format/include/E57Foundation.h"
    class_order = ["Node",
                   "StructureNode",
                   "VectorNode",
                   "SourceDestBuffer",
                   "CompressedVectorNode",
                   "CompressedVectorReader",
                   "CompressedVectorWriter",
                   "IntegerNode",
                   "ScaledIntegerNode",
                   "FloatNode",
                   "StringNode",
                   "BlobNode",
                   "ImageFile",
                   "E57Exception",
                   "E57Utilities",
                   ]
    main(path)
