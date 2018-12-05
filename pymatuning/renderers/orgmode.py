import networkx as nx

from pymatuning.listings import mod_basename

def _roots(graph):
    return [x for x in graph.nodes() if graph.out_degree(x)>0 and graph.in_degree(x)==0]

def _tree_output_content(tree_struct, level=0):

    # make list of the content (level, content)
    data = [(level, tree_struct['id'])]

    # if this has children then add those in after this sub trees root
    # data is in
    if 'children' in tree_struct:
        for substruct in tree_struct['children']:
            data.extend(_tree_output_content(substruct, level=level+1))

    return data

def listing(tree, n_indent_spaces=2, marker="-"):
    """Given a NetworkX DiGraph tree object generate a list in plaintext
    in org mode format.
    """

    root = _roots(tree)[0]

    lines_data = _tree_output_content(nx.tree_data(tree, root))
    lines = []
    for indent_level, content in lines_data:

        if type(content) == str:
            content_str = mod_basename(content)
        else:
            content_str = content[-1]

        whitespace = ''.join([' ' for _ in range(indent_level * n_indent_spaces)])
        line = "{whitespace}{marker} {content}".format(whitespace=whitespace,
                                                       marker=marker,
                                                       content=content_str)

        lines.append(line)


    # combine all the lines
    return '\n'.join(lines)



