"""Oh, wow an actual Python file"""
from __future__ import annotations

from dataclasses import dataclass

from helpers import *


@dataclass
class TreeNode:
    text: str
    subnodes: list[TreeNode]


def _construct_forest_tree(node: TreeNode) -> str:
    """Constructs a forest, which
    includes the \\begin{forest} and \\end{forest}
    at the start and end.
    """
    return '\\begin{forest}\n' + _construct_forest_helper(node) + \
           '\n\\end{forest}'


def _construct_forest_helper(node: TreeNode) -> str:
    """A helper to the above.
    Construct the node, which should be wrapped with
    [these brackets] before being returned.
    """
    p1 = '{' + node.text + '}'
    p2_l = [_construct_forest_helper(x) for x in node.subnodes]
    p2 = '\n'.join(p2_l)
    return '[' + p1 + '\n' + p2 + ']'


def construct_tree_wrapper(text: str, index: int) -> str:
    """Given an itemize environment, make a tree out of it.
    Index must be the start of the itemize environment, and that's it. It'll
    convert the entire itemize environment.

    index must be the backslash of \\begin{itemize}
    """
    itemize = '\\begin{itemize}'
    itemize_end = '\\end{itemize}'
    assert text.startswith('\\begin{itemize}', index)
    itemize_after = index + len(itemize)
    env_end = find_env_end(text, index)
    env_true_end = env_end + len(itemize_end)

    before = text[:index]
    during1 = text[itemize_after:env_end]
    after = text[env_true_end:]
    during_tree = [_construct_forest_tree(x) for x in _construct_tree(during1)]
    during_true = '\n\n'.join(during_tree)
    return before.strip() + '\n\n' + during_true + '\n\n' + after


def _construct_tree(text: str) -> list[TreeNode]:
    """Construct a tree structure out of text.
    Text must be an itemize environment without the word itemize.
    Text must not contain any unconcealed verbatim environments as well.

    Rule of thumb: multiple trees will be constructed if the list of nodes that are
    returned exceeds the size of 1 (because how is that a tree, anyways?
    """
    text = text.strip()
    splitted_nodes = [x.strip() for x in split_not_in_environment(text, r'\\item')
                      if x.strip() != '']
    subnode_list: list[TreeNode] = []
    for sp in splitted_nodes:
        itemize_start = '\\begin{itemize}'
        if itemize_start in sp:
            itemize_location = sp.find(itemize_start)  # backslash location
            assert itemize_location != -1
            text_region = sp[:itemize_location].strip()  # no optimization moment

            # print(f'TEXT REGION | {text_region} // END')
            # end of itemize is
            end_of_itemize = find_env_end(sp, itemize_location)
            assert end_of_itemize != -1
            new_list_region = sp[itemize_location + len(itemize_start):end_of_itemize]
            new_node_list = _construct_tree(new_list_region)
            curr_node = TreeNode(text_region, new_node_list)
            subnode_list.append(curr_node)
        else:
            # print(f'NON TEXT REGION | {sp} // END')
            curr_node = TreeNode(sp.strip(), [])
            subnode_list.append(curr_node)
    return subnode_list


def _check_tree_constructor():
    temp_text = \
        R"""\begin{itemize}
\item The labels consists of sequential numbers
   \begin{itemize}
     \item The individual entries are indicated with a black dot, a so-called bullet
     \item The text in the entries may be of any length
     \begin{itemize}
        \item I would like to describe something here
        \item \(\int_{2}^{6}{\frac{42x}{32}dx}\)
        \begin{itemize}
            \item I would never do something like that
            \item but what is the point? \(9+10=21\)
        \end{itemize}
        \item And give a warning here
     \end{itemize}
   \end{itemize}
   \item The numbers starts at 1 with each use of the \texttt{enumerate} environment
   \end{itemize}
   
   I haven't committed tax fraud five times in my life
        """
    tl = _construct_tree(temp_text)
    print(tl)
    return tl


if __name__ == '__main__':
    tttt = \
        R"""\begin{itemize}
\item The labels consists of sequential numbers
   \begin{itemize}
     \item The individual entries are indicated with a black dot, a so-called bullet
     \item The text in the entries may be of any length
     \begin{itemize}
        \item I would like to describe something here
        \item \(\int_{2}^{6}{\frac{42x}{32}dx}\)
        \begin{itemize}
            \item I would never do something like that
            \item but what is the point? \(9+10=21\)
        \end{itemize}
        \item And give a warning here
     \end{itemize}
   \end{itemize}
   \item The numbers starts at 1 with each use of the \texttt{enumerate} environment
   \end{itemize}

   I haven't committed tax fraud five times in my life
        """
    print(construct_tree_wrapper(tttt, 0))
