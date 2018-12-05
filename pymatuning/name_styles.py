import re


class NamingStyle:
    # It may seem counterintuitive that single naming style
    # has multiple "accepted" forms of regular expressions,
    # but we need to special-case stuff like dunder names
    # in method names.
    CLASS_NAME_RGX = None  # type: Pattern[str]
    MOD_NAME_RGX = None  # type: Pattern[str]
    CONST_NAME_RGX = None  # type: Pattern[str]
    COMP_VAR_RGX = None  # type: Pattern[str]
    DEFAULT_NAME_RGX = None  # type: Pattern[str]
    CLASS_ATTRIBUTE_RGX = None  # type: Pattern[str]

    @classmethod
    def get_regex(cls, name_type):
        return {
            "module": cls.MOD_NAME_RGX,
            "const": cls.CONST_NAME_RGX,
            "class": cls.CLASS_NAME_RGX,
            "function": cls.DEFAULT_NAME_RGX,
            "method": cls.DEFAULT_NAME_RGX,
            "attr": cls.DEFAULT_NAME_RGX,
            "argument": cls.DEFAULT_NAME_RGX,
            "variable": cls.DEFAULT_NAME_RGX,
            "class_attribute": cls.CLASS_ATTRIBUTE_RGX,
            "inlinevar": cls.COMP_VAR_RGX,
        }[name_type]


class SnakeCaseStyle(NamingStyle):
    """Regex rules for snake_case naming style."""

    CLASS_NAME_RGX = re.compile("[a-z_][a-z0-9_]+$")
    MOD_NAME_RGX = re.compile("([a-z_][a-z0-9_]*)$")
    CONST_NAME_RGX = re.compile("(([a-z_][a-z0-9_]*)|(__.*__))$")
    COMP_VAR_RGX = re.compile("[a-z_][a-z0-9_]*$")
    DEFAULT_NAME_RGX = re.compile(
        "(([a-z_][a-z0-9_]{2,})|(_[a-z0-9_]*)|(__[a-z][a-z0-9_]+__))$"
    )
    CLASS_ATTRIBUTE_RGX = re.compile(r"(([a-z_][a-z0-9_]{2,}|(__.*__)))$")


class CamelCaseStyle(NamingStyle):
    """Regex rules for camelCase naming style."""

    CLASS_NAME_RGX = re.compile("[a-z_][a-zA-Z0-9]+$")
    MOD_NAME_RGX = re.compile("([a-z_][a-zA-Z0-9]*)$")
    CONST_NAME_RGX = re.compile("(([a-z_][A-Za-z0-9]*)|(__.*__))$")
    COMP_VAR_RGX = re.compile("[a-z_][A-Za-z0-9]*$")
    DEFAULT_NAME_RGX = re.compile("(([a-z_][a-zA-Z0-9]{2,})|(__[a-z][a-zA-Z0-9_]+__))$")
    CLASS_ATTRIBUTE_RGX = re.compile(r"([a-z_][A-Za-z0-9]{2,}|(__.*__))$")


class PascalCaseStyle(NamingStyle):
    """Regex rules for PascalCase naming style."""

    CLASS_NAME_RGX = re.compile("[A-Z_][a-zA-Z0-9]+$")
    MOD_NAME_RGX = re.compile("[A-Z_][a-zA-Z0-9]+$")
    CONST_NAME_RGX = re.compile("(([A-Z_][A-Za-z0-9]*)|(__.*__))$")
    COMP_VAR_RGX = re.compile("[A-Z_][a-zA-Z0-9]+$")
    DEFAULT_NAME_RGX = re.compile("[A-Z_][a-zA-Z0-9]{2,}$|(__[a-z][a-zA-Z0-9_]+__)$")
    CLASS_ATTRIBUTE_RGX = re.compile("[A-Z_][a-zA-Z0-9]{2,}$")


class UpperCaseStyle(NamingStyle):
    """Regex rules for UPPER_CASE naming style."""

    CLASS_NAME_RGX = re.compile("[A-Z_][A-Z0-9_]+$")
    MOD_NAME_RGX = re.compile("[A-Z_][A-Z0-9_]+$")
    CONST_NAME_RGX = re.compile("(([A-Z_][A-Z0-9_]*)|(__.*__))$")
    COMP_VAR_RGX = re.compile("[A-Z_][A-Z0-9_]+$")
    DEFAULT_NAME_RGX = re.compile("([A-Z_][A-Z0-9_]{2,})|(__[a-z][a-zA-Z0-9_]+__)$")
    CLASS_ATTRIBUTE_RGX = re.compile("[A-Z_][A-Z0-9_]{2,}$")


class AnyStyle(NamingStyle):
    @classmethod
    def get_regex(cls, name_type):
        return re.compile(".*")


NAMING_STYLES = {
    "snake_case": SnakeCaseStyle,
    "camelCase": CamelCaseStyle,
    "PascalCase": PascalCaseStyle,
    "UPPER_CASE": UpperCaseStyle,
    "any": AnyStyle,
}
