from pkgutil import iter_modules, walk_packages
from importlib import import_module
import importlib.util as imp
import ast
import itertools as it
import os.path as osp
import os


import networkx as nx

MODULE_SEPARATOR = '.'
CLASS_METHOD_SEPARATOR = '.'

AST_FUNCTION_CLASS = ast.FunctionDef
AST_CLASS_CLASS = ast.ClassDef
AST_VARIABLE_CLASS = ast.Assign
AST_ATTRIBUTE_CLASS = ast.Attribute

# names of decorators of methods in classes that make them "special",
# these include properties, classmethods, and staticmethods
SPECIAL_METHODS = ('property', 'classmethod', 'staticmethod',)


def _leaves(graph):
    return [x for x in graph.nodes() if graph.out_degree(x)==0 and graph.in_degree(x)==1]

def _roots(graph):
    return [x for x in graph.nodes() if graph.out_degree(x)>0 and graph.in_degree(x)==0]

def mod_basename(modpath):
    return modpath.split(MODULE_SEPARATOR)[-1]

def mod_rootname(modpath):
    return MODULE_SEPARATOR.join(modpath.split(MODULE_SEPARATOR)[:-1])

def import_module_from_filepath(mod_filepath):

    modname = osp.splitext(osp.basename(mod_filepath))[0]

    # then use importlib to get a module spec and load it
    spec = imp.spec_from_file_location(modname, mod_filepath)

    module = imp.module_from_spec(spec)

    spec.loader.exec_module(module)

    # then import all the submodules as well

    return module

def import_package_from_filepath(package_root_filepath):

    # also assume module name is the last thing in the path
    modname = osp.basename(package_root_filepath)

    import_module_from_filepath(osp.join(package_root_filepath, "__init__.py"))

    for name in os.listdir(package_root_filepath):
        path = osp.join(package_root_filepath, name)
        if path.endswith('.py'):
             import_module_from_filepath(path)

        elif osp.isdir(path):
            if "__init__.py" in os.listdir(path):
                import_package_from_filepath(path)

def list_file_submodules(package_filepath):
    """List all the submodule names for the given module file path."""

    # then get the module names, the trick is to make a list out of
    # the module filepath
    return list([subname for __, subname, _
                 in iter_modules([package_filepath])])

def list_submodules(package):
    """List all the submodule names one level below the given module."""

    return list_file_submodules(package.__path__)

def package_struct(package):

    root_modname = package.__name__

    # if the module is not a package do nothing, we check this by the
    # presence of the __path__ attribute which only packages have
    if not hasattr(package, "__path__"):
        return []

    # otherwise search it for submodules and make a list of them
    submod_list = []

    for _, submod_basename, ispkg in iter_modules(package.__path__):

        submod_name = "{}.{}".format(root_modname, submod_basename)

        submod = import_module(submod_name)

        # if this module is a package, we recursively search for more
        # modules and add those to the submodule list as a dictionary
        if ispkg:
            submod_list.append(package_tree(submod))

        # otherwise we just add the string basename for this non-package module
        # to the submodule list
        else:
            submod_list.append(submod_basename)

    return {mod_basename(root_modname) : submod_list}


def list_all_submodules(package):
    """ List all the modules in this package with their fully qualified names."""

    root_modname = package.__name__

    # if the module is not a package do nothing, we check this by the
    # presence of the __path__ attribute which only packages have
    if not hasattr(package, "__path__"):
        return [root_modname]

    submod_list = []

    for _, submod_basename, ispkg in iter_modules(package.__path__):

        submod_fqname = "{}.{}".format(root_modname, submod_basename)

        submod = import_module(submod_fqname)

        # if this module is a package, we recursively search for more
        # modules and add those to the submodule list as a dictionary
        if ispkg:
            submod_list.extend(list_all_submodules(submod))

        # otherwise we just add the string basename for this non-package module
        # to the submodule list
        else:
            submod_list.append(submod_fqname)

    # return all the modules as one flattened list
    return [root_modname] + submod_list

def package_tree(package):
    """Generate a NetworkX DiGraph representing the tree structure of the
    package modules. The node IDs are the fully qualified module names."""

    pt = nx.DiGraph()

    package_fqnames = list_all_submodules(package)
    # add all the nodes
    for mod_fqname in package_fqnames:
        pt.add_node(mod_fqname)

    # then make the edges, by just focusing on connections between the
    # base name and its supermodule
    for mod_fqname in package_fqnames:
        # avoid splitting the name of the root module
        if MODULE_SEPARATOR in mod_fqname:
            base = mod_basename(mod_fqname)
            root = mod_rootname(mod_fqname)
            pt.add_edge(root, mod_fqname)


    # now we can traverse this tree and get all the definitions for
    # each module and add them as attributes to the package tree
    for mod_fqname in nx.bfs_tree(pt, package.__name__):

        # first we need to load the module and then get it's module
        # definitions
        mod = import_module(mod_fqname)

        defs = module_definitions(mod)

        # then update that nodes attributes with the definitions
        pt.node[mod_fqname].update(defs)

    return pt

def load_module_ast(module):
    with open(module.__file__) as rf:
        st = ast.parse(rf.read())

    return st

def list_functions(st):

    function_names = []

    for thing in st.body:
        if type(thing) == AST_FUNCTION_CLASS:
            function_names.append(thing.name)

    return function_names

def list_classes(st):

    class_names = []

    for thing in st.body:
        if type(thing) == AST_CLASS_CLASS:
            class_names.append(thing.name)

    return class_names


def list_variables(st):

    variable_names = []

    for thing in st.body:
        if type(thing) == AST_VARIABLE_CLASS:
            # since we can set multiple variables at once with
            # unpacking we get all the names from the "targets"
            for name in thing.targets:
                variable_names.append(name.id)

    return variable_names

def module_definitions(module):

    st = load_module_ast(module)
    definitions = {}
    definitions['functions'] = list_functions(st)
    definitions['classes'] = list_classes(st)
    definitions['variables'] = list_variables(st)

    return definitions


def list_classdefs(st):

    class_defs = []

    for thing in st.body:
        if type(thing) == AST_CLASS_CLASS:
            class_defs.append(thing)

    return class_defs


def list_methods(classdef):

    function_names = []
    for thing in classdef.body:
        # first check if the thing is a function
        if type(thing) == AST_FUNCTION_CLASS:

            # if it is then we want to make sure it is not one of the
            # special methods (property, classmethod, staticmethod),
            # so get the names of the decorators
            decorator_names = [dec.id for dec in thing.decorator_list if hasattr(dec, 'id')]

            # then check that none of the decorators are one of them
            if not any([True if dec in SPECIAL_METHODS else False for dec in decorator_names]):
                function_names.append(thing.name)

    return function_names


def list_classmethods(classdef):

    function_names = []
    for thing in classdef.body:
        # first check if the thing is a function
        if type(thing) == AST_FUNCTION_CLASS:

            # if it is then we want to make sure it is not one of the
            # special methods (property, classmethod, staticmethod),
            # so get the names of the decorators
            decorator_names = [dec.id for dec in thing.decorator_list if hasattr(dec, 'id')]


            # then check that none of the decorators are one of them
            if any([True if dec == 'classmethod' else False for dec in decorator_names]):
                function_names.append(thing.name)

    return function_names

def list_staticmethods(classdef):

    function_names = []
    for thing in classdef.body:
        # first check if the thing is a function
        if type(thing) == AST_FUNCTION_CLASS:

            # if it is then we want to make sure it is not one of the
            # special methods (property, classmethod, staticmethod),
            # so get the names of the decorators
            decorator_names = [dec.id for dec in thing.decorator_list if hasattr(dec, 'id')]

            # then check that none of the decorators are one of them
            if any([True if dec == 'staticmethod' else False for dec in decorator_names]):
                function_names.append(thing.name)

    return function_names

def list_properties(classdef):

    function_names = []

    for thing in classdef.body:
        # first check if the thing is a function
        if type(thing) == AST_FUNCTION_CLASS:

            # if it is then we want to make sure it is not one of the
            # special methods (property, classmethod, staticmethod),
            # so get the names of the decorators
            decorator_names = [dec.id for dec in thing.decorator_list if hasattr(dec, 'id')]

            # then check that none of the decorators are one of them
            if any([True if dec == 'property' else False for dec in decorator_names]):
                function_names.append(thing.name)

    return function_names

def list_getters(classdef):

    function_names = []

    for thing in classdef.body:
        # first check if the thing is a function
        if type(thing) == AST_FUNCTION_CLASS:

            # if it is then we want to make sure it is not one of the
            # special methods (property, classmethod, staticmethod),
            # so get the names of the decorators
            decorator_names = [dec.attr for dec in thing.decorator_list
                               if type(dec) == AST_ATTRIBUTE_CLASS]

            # then check that none of the decorators are one of them
            if any([True if dec == 'getter' else False for dec in decorator_names]):
                function_names.append(thing.name)

    return function_names

def list_setters(classdef):

    function_names = []

    for thing in classdef.body:
        # first check if the thing is a function
        if type(thing) == AST_FUNCTION_CLASS:

            # if it is then we want to make sure it is not one of the
            # special methods (property, classmethod, staticmethod),
            # so get the names of the decorators
            decorator_names = [dec.attr for dec in thing.decorator_list
                               if type(dec) == AST_ATTRIBUTE_CLASS]

            # then check that none of the decorators are one of them
            if any([True if dec == 'setter' else False for dec in decorator_names]):
                function_names.append(thing.name)

    return function_names



def class_definitions(classdef):
    """Given an ast.ClassDef object return a dictionary of the functions
    (methods, classmethods, and staticmethods), properties (functions
    with the `@property` decorator that are accessed like variables)
    and variables (attributes).

    """

    definitions = {}
    definitions['attributes'] = list_variables(classdef)
    definitions['methods'] = list_methods(classdef)
    definitions['classmethods'] = list_classmethods(classdef)
    definitions['staticmethods'] = list_staticmethods(classdef)
    definitions['properties'] = list_properties(classdef)
    definitions['setters'] = list_setters(classdef)
    definitions['getters'] = list_getters(classdef)

    return definitions



def list_module_definitions(module):
    defs = module_definitions(module)
    return it.chain(*[defs[t] for t in ('functions', 'classes', 'variables')])

def interface_tree(package):
    """Generate the entire Interface Tree (it) for this package.

    This includes all submodules in the package as well as all
    function and class definitions and constant assignment.

    This tree can then be further filtered so as to get a particular
    view of the interface tree (e.g. only public definitions)

    """

    # first generate the package tree. This is just the modules.
    pt = package_tree(package)

    # initialize the interface tree with the nodes (without
    # attributes) and edges from the package tree
    i_tree = pt.copy()
    # delete all the attributes
    for node_id in i_tree.nodes:
        i_tree.node[node_id].clear()

    # then we traverse this and generate make nodes for all the
    # variables, functions, and classes as well as expanding out the
    # definitions within classes to their own nodes as well.
    for mod_fqname in nx.bfs_tree(pt, package.__name__):

        module_node = pt.node[mod_fqname]

        # make nodes for all the functions, variables, and classes
        # with an edge to them
        for function_name in module_node['functions']:
            function_node_id = (mod_fqname, function_name)
            edge = (mod_fqname, function_node_id)
            i_tree.add_edge(*edge)

        for variable_name in module_node['variables']:
            variable_node_id = (mod_fqname, variable_name)
            edge = (mod_fqname, variable_node_id)
            i_tree.add_edge(*edge)

        # for the class we need to get the syntax tree for the module
        # to get the classdefs
        mod_st = load_module_ast(import_module(mod_fqname))
        classdefs = list_classdefs(mod_st)

        for classdef in classdefs:

            # add a node and edge for the class
            classname = classdef.name
            class_node_id = (mod_fqname, classname)
            edge = (mod_fqname, class_node_id)
            i_tree.add_edge(*edge)

            # then get its definitions and add them as well
            class_defs = class_definitions(classdef)

            # attribute
            for attribute in class_defs['attributes']:
                attribute_node_id = (mod_fqname, classname, attribute)
                edge = (class_node_id, attribute_node_id)
                i_tree.add_edge(*edge)

            # methods
            for method in class_defs['methods']:
                method_node_id = (mod_fqname, classname, method)
                edge = (class_node_id, method_node_id)
                i_tree.add_edge(*edge)
            for method in class_defs['classmethods']:
                method_node_id = (mod_fqname, classname, method)
                edge = (class_node_id, method_node_id)
                i_tree.add_edge(*edge)
            for method in class_defs['staticmethods']:
                method_node_id = (mod_fqname, classname, method)
                edge = (class_node_id, method_node_id)
                i_tree.add_edge(*edge)
            for method in class_defs['properties']:
                method_node_id = (mod_fqname, classname, method)
                edge = (class_node_id, method_node_id)
                i_tree.add_edge(*edge)
            for method in class_defs['setters']:
                method_node_id = (mod_fqname, classname, method)
                edge = (class_node_id, method_node_id)
                i_tree.add_edge(*edge)
            for method in class_defs['getters']:
                method_node_id = (mod_fqname, classname, method)
                edge = (class_node_id, method_node_id)
                i_tree.add_edge(*edge)


    return i_tree
