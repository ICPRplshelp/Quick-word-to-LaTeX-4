"""Most of the helper functions to converter.py and any other modules
"""
import json
import logging
import math
from dataclasses import dataclass, fields
from typing import Optional, Iterable, Callable

# ch = logging.StreamHandler()
# ch.setLevel(logging.DEBUG)
PREAMBLE_PATH = ('preamble.txt', 'preamble_LTable.txt', 'preamble_light.txt')

APA_MODE = True
ALPHABET = 'abcdefghijklmnopqrstuvwxyz'
ALPHABET_ALL = ALPHABET + ALPHABET.upper() + '1234567890-+.,*/?!='
MAX_PAGE_LENGTH = 32


def deduce_preamble_mode(tex_file: str) -> int:
    """Longtable?
    """
    if '\\begin{longtable}' in tex_file:
        # print('Has a longtable')
        return 0
    else:
        # print('Does not have a longtable')
        return 2


def insert_in_preamble(tex_file: str, mode: int = 0) -> str:
    """Insert in preamble
    """
    with open(PREAMBLE_PATH[mode]) as f:
        file_text = f.read()
    # have it insert right before \title
    title_index = find_nth(tex_file, '\\title', 1)
    newest_text = tex_file[:title_index] + '\n' + file_text + '\n' + tex_file[title_index:]
    return newest_text


def many_instances(old_tex: str, tex_file: str, todo_str: str):
    """Many instances
    """
    while True:
        try:
            old_tex, tex_file = one_instance(old_tex, tex_file, todo_str)
        except AssertionError:
            break
    return tex_file


def longtable_eliminator(text: str, label: str = '', caption: str = '') -> str:
    """Instance - Here, everything is in a longtable.
    j is the number of times this has run starting from 0.
    text is a longtable instance.
    """
    headers_so_far = []
    left_border = '\\begin{minipage}[b]{\\linewidth}\\raggedright\n'
    right_border = '\\end{minipage}'  # leading \n only
    i = 1
    while True:
        left_index = find_nth(text, left_border, i) + len(left_border)
        right_index = find_nth(text, right_border, i)
        if right_index == -1:
            break
        cur_header = text[left_index:right_index].strip()
        headers_so_far.append(cur_header)
        i += 1
    tab_start = '\\endhead'
    tab_end = '\\bottomrule'
    tab_s_index = find_nth(text, tab_start, 1) + len(tab_start)
    tab_e_index = find_nth(text, tab_end, 1)
    if tab_s_index != tab_e_index:
        tab_data = text[tab_s_index:tab_e_index].strip()
    else:
        tab_data = ''
    first_row = '& '.join(headers_so_far)
    header_count = len(headers_so_far)
    # a table can have up to 3 headers until we start splitting up the tables.

    max_header_count = 1
    seperator = 'c'
    if header_count > max_header_count:
        em_length = MAX_PAGE_LENGTH // header_count
        seperator = 'm{' + str(em_length) + 'em}'

    table_width = (('|' + seperator) * header_count) + '|'
    if tab_data != '':
        tab_data = '\n\\hline\n' + first_row + '\\\\ \\hline\n' + tab_data + '\n\\hline\n'
    else:
        tab_data = '\n\\hline\n' + first_row + '\n\\hline'
    if caption != '':
        caption_info = '\\caption{' + caption + '}\n'
    else:
        caption_info = ''
    table_start = '\\begin{table}[h]\n\\centering\n' + label + '\n\\begin{tabular}{' + table_width + '}\n'
    table_end = '\\end{tabular}\n' + '\n' + caption_info + '\\end{table}\n'
    new_table = table_start + tab_data + table_end
    new_table = new_table.replace(r'\[', r'\(')  # all math in tables are inline math
    new_table = new_table.replace(r'\]', r'\)')
    return new_table


def detect_end_of_bracket_env(text: str, env_start: int) -> int:
    """Whatever it returns is the position AT the environment.
    Preconditions:
        - no weird brackets in texttt regions.
    """
    # print('new bracket region')
    brackets_to_ignore = 1
    while True:
        ind = find_nth(text, '}', brackets_to_ignore, env_start)
        # print(ind)
        if text[ind - 1] == '\\':  # last
            brackets_to_ignore += 1
            # char can't be \\ and \} has to be out
            continue
        # elif bracket_layers(text, ind, starting_index=env_start) != -1:
        #     # cur_text = text[ind - 1]
        #     brackets_to_ignore += 1
        #     continue
        else:
            break
    return ind


def fix_all_textt(text: str) -> str:
    """Do it
    """
    text = text.replace('{[}', '[')
    text = text.replace('{]}', ']')
    dealt_with = 1
    while True:
        t_index = find_nth(text, r'\texttt{', dealt_with)
        if t_index == -1:
            break
        t_index += len(r'\texttt{')
        end = detect_end_of_bracket_env(text, t_index)
        texttt_bounds = text[t_index:end]
        tb = fix_texttt(texttt_bounds)
        text = text[:t_index] + tb + text[end:]

        dealt_with += 1
    text = combine_all_textt(text)
    return text


def combine_all_textt(text: str) -> str:
    """
    Do it
    Precondition: The document does not end with a texttt.
    This is supposed to run after everything of that is run.
    """
    dealt_with = 1
    min_index = 0
    while True:
        t_index = find_nth(text, r'\texttt{', dealt_with, min_index)
        if t_index == -1:
            break
        end = detect_end_of_bracket_env(text, t_index)
        end += 1
        new_index = find_nth(text, r'\texttt{', 1, end)
        if new_index == end:
            text = text[:end - 1] + text[end + len(r'\texttt{'):]
        else:
            dealt_with += 1
    return text


def fix_texttt(text: str) -> str:
    """Everything has to be in a texttt env

    """
    # slashed_indices = []
    # prev_char = ''
    text = text.replace('–', '-')
    text = text.replace(r'\_', '🬀')
    text = text.replace(r'\&', '🬐')
    text = text.replace(r'\$', '🬠')
    text = text.replace(r'\{', '🬰')
    text = text.replace(r'\}', '🭀')
    text = text.replace(r'{]}', '}')
    text = text.replace('r{[}', '[')
    text = text.replace('\\', '')
    text = text.replace('🬀', r'\_')
    text = text.replace('🬐', r'\&')
    text = text.replace('🬠', r'\$')
    text = text.replace('🬰', r'\{')
    text = text.replace('🭀', r'\}')

    # for i, char in enumerate(text):
    #     if prev_char in ALPHABET_ALL and char == '\\':
    #        slashed_indices.append(i)
    #    prev_char = char
    # for index in slashed_indices:
    #     str_text = [x for x in text]
    #     str_text[index] = ''  # different
    #    text = ''.join(str_text)
    return text


def three_way_isolation(text: str, left_index: int, right_index: int) -> tuple[str, str, str]:
    """Three way isolation
    0: inside, 1: before, 2: after
    """
    return text[left_index:right_index], text[:left_index], text[right_index - 1:]


def eliminate_all_longtables(text: str, disallow_figures: bool = True) -> str:
    """Eliminate all longtables.
    Upper function for the other

    If disallow_figures is true, figuring tables will not count anything.
    """
    # i = 1
    lt_start = '\\begin{longtable}'
    lt_end = '\\end{longtable}'
    table_text_cap = 'Table'
    tables_so_far = []
    # j = 1
    while True:
        lt_start_index = find_nth(text, lt_start, 1)
        lt_end_index = find_nth(text, lt_end, 1) + len(lt_end) + 3
        if lt_start_index == -1 or lt_end_index == -1:
            break
        during, before, after = three_way_isolation(text, lt_start_index, lt_end_index)
        if not disallow_figures and after[:len(table_text_cap)] == table_text_cap:
            end_figure_index = find_nth(after, '\n\n', 1)
            temp_figure_text = after[:end_figure_index]
            temp_figure_text_2 = temp_figure_text[len(table_text_cap) + 1:]
            end_of_numbering_1 = find_nth(temp_figure_text_2, ':', 1)
            end_of_numbering_2 = find_nth(temp_figure_text_2, '\n', 1)
            # we can assert that end of both numbers aren't the same
            if end_of_numbering_1 < 0:
                end_of_numbering_1 = end_of_numbering_2
            if end_of_numbering_2 < 0:
                end_of_numbering_2 = end_of_numbering_1
            end_of_numbering = min(end_of_numbering_2, end_of_numbering_1)
            figure_num = temp_figure_text_2[:end_of_numbering]  # this is actually a string
            figure_caption = temp_figure_text_2[end_of_numbering + 2:end_figure_index]
            after = after[end_figure_index:]
            if figure_num == '':
                figure_num = '-9999'
            fig_label = '\\label{table:p' + figure_num + '}\n'
            tables_so_far.append(figure_num)
            new_table_info = longtable_eliminator(during, fig_label, figure_caption)
        else:
            new_table_info = longtable_eliminator(during, '', '')
        text = before + new_table_info + after
        # j += 1
    return text


def qed(text: str, special: bool = False) -> str:
    """Allow QED support.

    """
    sp = '{}{}' if special else ''
    text = text.replace('\\emph{Proof.}', '\\begin{proof}' + sp)
    text = text.replace('\\[\\blacksquare\\]', '\\end{proof}')
    text = text.replace('\\blacksquare\\]', '\\] \\end{proof}')
    text = text.replace('\\(\\blacksquare\\)', '\\end{proof}')
    text = text.replace('\\blacksquare\\)', '\\) \\end{proof}')
    text = text.replace(r'~◻', '\\end{proof}')
    text = text.replace(r'□', '\\end{proof}')
    text = text.replace(r'◻', '\\end{proof}')
    # text = '\\renewcommand\\qedsymbol{$\\blacksquare$}\n' + text
    return text


def one_instance(old_tex: str, tex_file: str, todo_str: str) -> tuple[str, str]:
    """Just one run
    """
    reduced_old_tex, extract = gather_section(old_tex)
    new_text_file = insert_at_todo(extract, tex_file, todo_str)
    return reduced_old_tex, new_text_file


def file_name_only_forward(path: str) -> str:
    """File path only! / not \\
    """
    l_index = path.rfind('/')
    return path[l_index + 1:]


def truncate_path(text: str, disallow_pdf: bool = False) -> tuple[str, bool]:
    """Truncate path!

    """
    icg = '\\includegraphics{'
    i = 1
    while True:
        location = find_nth(text, icg, i)
        if location == -1:
            break
        ending_index = text.find('}', location + len(icg))
        include_string = text[location + len(icg):ending_index]
        include_string = 'media/' + file_name_only_forward(include_string)
        text = text[:location] + icg + include_string + text[ending_index:]
        i += 1
    bool_state = i >= 2 if disallow_pdf else False
    return text, bool_state


def remove_images(text: str) -> str:
    """Remove all images.
    """
    # figures_so_far = []
    return text.replace('\\includegraphics', '% \\includegraphics')


def detect_include_graphics(text: str, disallow_figures: bool = False) -> str:
    """Center all images.
    """
    # if True:  # WHEN YOU CAN'T COMMENT OUT LINES
    figures_so_far = []
    i = 1

    figure_text_cap = 'Figure'
    while True:
        bl = '\n\\begin{figure}[bh]\n\\centering\n'
        el = '\\end{figure}\n'
        include_index = find_nth(text, '\\includegraphics', i)
        if include_index == -1:
            break
        before = text[:include_index]
        temp_after = text[include_index:]
        try:
            temp_after_index = temp_after.index('\n')
        except ValueError:
            break

        during = temp_after[:temp_after_index + 1]
        after = temp_after[temp_after_index + 2:]  # starts with \n
        if not disallow_figures and after[:len(figure_text_cap)] == figure_text_cap:
            end_figure_index = find_nth(after, '\n\n', 1)
            temp_figure_text = after[:end_figure_index]
            temp_figure_text_2 = temp_figure_text[len(figure_text_cap) + 1:]
            end_of_numbering_1 = find_nth(temp_figure_text_2, ':', 1)
            end_of_numbering_2 = find_nth(temp_figure_text_2, '\n', 1)
            # we can assert that end of both numbers aren't the same
            if end_of_numbering_1 < 0:
                end_of_numbering_1 = end_of_numbering_2
            if end_of_numbering_2 < 0:
                end_of_numbering_2 = end_of_numbering_1
            end_of_numbering = min(end_of_numbering_2, end_of_numbering_1)
            figure_num = temp_figure_text_2[:end_of_numbering]
            figure_caption = temp_figure_text_2[end_of_numbering + 2:end_figure_index]
            after = after[end_figure_index:]
            fig_label = '\\label{fig:p' + figure_num + '}\n'
            el = '\n\\caption{' + figure_caption + '}\n' + fig_label + el
            figures_so_far.append(figure_num)
        else:
            bl = '\n\\begin{center}\n'
            el = '\\end{center}\n'
        text = before + bl + during + el + '\n' + after
        i += 1
    new_figures_so_far = ['\\ref{fig:p' + x + '}' for x in figures_so_far]
    old_figures_so_far = ['Figure ' + y for y in figures_so_far]
    old_figures_so_far_1 = ['figure ' + z for z in figures_so_far]
    for i in range(0, len(old_figures_so_far)):
        text = text.replace(old_figures_so_far[i], 'Figure ' + new_figures_so_far[i])
    for i in range(0, len(old_figures_so_far_1)):
        text = text.replace(old_figures_so_far_1[i], 'figure ' + new_figures_so_far[i])

    return text


def insert_at_todo(extract: str, tex_file: str, todo_str: str) -> str:
    """Insert extract at the first "to do:" in the tex file.
    tex_file must not include the preamble.

    Preconditions: sections don't have newline characters in them.
    """
    first_todo_index = find_nth(tex_file, todo_str, 1)
    if first_todo_index == -1:
        print('Ran out of TODOs in the appending TeX file')
        assert False
    # and then split the thing:
    left_tex = tex_file[:first_todo_index]
    right_text = tex_file[first_todo_index:]
    first_newline_afterwards = right_text.index('\n')
    if first_newline_afterwards == -1:
        right_text = ''
    # elif first_newline_afterwards - first_todo_index > 7:
    #     while True:
    #         if right_text[first_newline_afterwards - 1] == '}':
    #             break
    #         if right_text[first_newline_afterwards - 1] != '}':
    #             first_newline_afterwards = right_text.index('\n', first_newline_afterwards + 1)
    #         if first_newline_afterwards == -1:
    #             right_text = ''
    #             break
    #             # loop again to check

    right_text = right_text[first_newline_afterwards:]
    final_text = left_tex + ' ' + extract + right_text
    return final_text


def gather_section(latex_str: str) -> tuple[str, str]:
    """First index of tuple is the text with the old subsection text removed.
    Second index is the extracted text.
    """
    section_alias = '\\section'
    start_section = find_nth(latex_str, section_alias, 1)
    end_section = find_nth(latex_str, section_alias, 2)

    # if start section isn't -1
    if start_section != -1:
        sliced_section = latex_str[start_section:end_section]
        n = 1
        while True:
            newline_index = find_nth(sliced_section, '}', n)
            if newline_index == -1:
                raise ValueError('Did you put latex code in verbatim environments?')
            if sliced_section[newline_index - 1] == '\\':
                n += 1
                continue
            else:
                break
                # sliced_section.index('\n')
        no_section_text = sliced_section[newline_index + 1:]

        popped_section = latex_str[:start_section] + '\n' + latex_str[end_section:]
        return popped_section, no_section_text
    else:
        print('Ran out of sections in converted word document')
        assert False


def find_nth(haystack: str, needle: str, n: int, starter: Optional[int] = None) -> int:
    """Needle in a haystack but awesome
    Return -1 on failure
    n = 1 is the lowest value of n; any value below 1 is treated as 1
    starter means from what index?
    """
    if starter is None:
        start = haystack.find(needle)
    else:
        start = haystack.find(needle, starter)
    while start >= 0 and n > 1:
        start = haystack.find(needle, start + len(needle))
        n -= 1
    return start


def rfind_nth(haystack: str, needle: str, n: int, starter: int = 0,
              ender: Optional[int] = None) -> int:
    """Same as find_nth, but looking at the opposite direction.
    starter and ender are to be interpreted as slice notation.

    Return -1 on failure.

    >>> test_text_here = '0123456789012345678901234567890'
    >>> rfind_nth(test_text_here, '6', 2, 9, 20)
    -1
    """
    if ender is None:
        ender = len(haystack)
    end = haystack.rfind(needle, starter, ender)
    while end >= 0 and n > 1:
        end = haystack.rfind(needle, starter, end)
        n -= 1
    return end


def do_citations(text: str, bib_contents: str, mode: str = 'mla') -> str:
    """Return text with converted citations.
    """
    authors = extract_authors_from_bib(bib_contents)
    text = citation_handler(text, authors)
    text = bulk_citation_page_handler(text, mode, False, authors)
    text = multi_cite_handler_bulk(text, authors)
    return text


def citation_handler(text: str, citation_list: list[str]) -> str:
    """Handle all non-page citations.
    """
    # citation_list = bib_path
    for src in citation_list:
        bracket_src = '(' + src + ')'
        cite_src = '\\cite{' + src + '}'
        if APA_MODE:
            cite_src = ' (' + cite_src + ')'
        text.replace(bracket_src, cite_src)
    return text


def bulk_citation_page_handler(text: str, mode: str,
                               p: bool, citation_list: list[str]) -> str:
    """Page numbers
    mode: apa1, apa2, or mla (default mla)
    if p is true latex page numbers will start with p. otherwise nothing
    """
    # citation_list = extract_authors_from_bib(bib_path)
    for src in citation_list:
        text = citation_page_handler(text, src, mode, p)
    return text


def create_citations_list(directory: str) -> list[str]:
    """Create a citations list.
    This function shouldn't run at all.
    """
    with open(directory) as f:
        citations = f.read()
    citation_list = citations.split('\n')
    return citation_list


def citation_page_handler(text: str, src: str, mode: str = 'apa2', p: bool = False) -> str:
    """Handle all page citations.
    The text should never make a fake-out citation ( please)

    >>> original_text = 'the reason why \\cite[32]{John} you are (John, p. 39) not.'
    >>> source = 'John'
    >>> expect = 'the reason why \\cite[32]{John} you are\\cite[39]{John} not.'
    >>> citation_page_handler(original_text, source, 'apa2', False) == expect
    True
    >>> original_text = 'the reason why \\cite[32]{John} you are (John 39) not.'
    >>> citation_page_handler(original_text, source, 'mla', False) == expect
    True
    """
    mode = mode.lower()
    if mode == 'apa1':
        str_text = '(' + src + ','
    elif mode == 'apa2':
        str_text = '(' + src + ', p. '
    else:  # MLA
        str_text = '(' + src + ' '
    while True:
        starter = text.find(str_text)
        # temp_text = text[starter:]
        if starter == -1:
            break
        start_offset = len(str_text)
        end = starter + start_offset  # the index after 'p. '
        closing_bracket = text.find(')', end)
        if closing_bracket == -1:
            break
        page_number = text[end:closing_bracket]
        citation_bound_end = closing_bracket + 1
        if p:
            page_number = 'p. ' + page_number
        cite_src = '\\cite[' + page_number + ']{' + src + '}'
        if APA_MODE:
            cite_src = ' (' + cite_src + ')'
        text = text[:starter - 1] + cite_src + text[citation_bound_end:]
    return text


def multi_cite_handler_bulk(text: str, srcs: list[str]) -> str:
    """Handle all the multi-inline citations in bulk.
    Must be called after all the other citation modules.
    """
    for src in srcs:
        text = multi_cite_handler(text, src, srcs)
    return text


MCRAW = r"""
This is (a1, a2, a3, a4). Also, (a1, a2, a3, a4).
"""
T_ALIST = ['a1', 'a2', 'a3', 'a4']


def multi_cite_handler(text: str, cur_src: str, srcs: list[str]) -> str:
    """Handle multiple authors cited in the same inline
    citation.
    If there is anything wrong with the citation syntax, stop the process.
    Author names may not contain parentheses for any reason.

    This will not result in any conflicts because latex's syntax
    is way different.

    Preconditions:
        - All other citation handlers have run
        - Raw text is in the format (Author1, Author2, Author3) or related
    """
    look_for = f'({cur_src}, '
    n = 1
    while True:  # per initial occurrence
        author_list = [cur_src]
        cite_ind = find_nth(text, look_for, n)  # index of the para in in-text cite
        if cite_ind == -1:
            break
        post_cite_ind = cite_ind + len(look_for)  # the index after the whitespace
        next_parentheses = text.find(')', cite_ind)
        if next_parentheses == -1:
            break
        for author in srcs:
            new_author_str = f'{author}, '
            cur_author_ind = text.find(new_author_str, post_cite_ind, next_parentheses)
            if cur_author_ind != -1:
                author_list.append(author)
            else:
                para_author_str = f'{author})'
                ending_author_ind = text.find(para_author_str, post_cite_ind, next_parentheses + 1)
                if ending_author_ind != -1:
                    author_list.append(author)
        # updated text
        text = text[:cite_ind] + r'\cite{' + ','.join(author_list) + '}' + text[next_parentheses + 1:]
    return text


class LatexEnvironment:
    """A class representing an environment.
    Instance Attributes:
        - env_name: name of the LaTeX environment.
        - start: start text of the LaTeX environment.
        - end: end text of the LaTeX environment.
        - encapsulation: Formats required
    """
    env_name: str  # env name, doesn't matter if caps or not
    start: str
    end: str
    encapsulation: str
    initial_newline: bool
    priority: int
    has_extra_args: bool
    extra_args_type: str
    env_prefix: str
    env_suffix: str

    def __init__(self, env_name: str, start: str, end: str,
                 encapsulation: Optional[str] = None, initial_newline: bool = False, priority: int = 0,
                 has_extra_args: bool = False, extra_args_type: str = 'bracket',
                 env_prefix: str = '', env_suffix: str = '', start_alt: str = '') -> None:
        """start and end here are not formatted - formats are done in encapsulation. This is in
        terms of the inputs. In the class itself, start and end are what you would see in
        LaTeX.
        """
        self.initial_newline = initial_newline
        if encapsulation is None or encapsulation == '':
            self.start = start
            self.end = end
        else:
            self.start = '\\' + encapsulation + '{' + start + '}'
            self.end = '\\' + encapsulation + '{' + end + '}'
        self.env_name = env_name
        if start_alt == '':
            self.start_alt = self.env_name
        else:
            self.start_alt = start_alt
        self.priority = priority
        self.has_extra_args = has_extra_args
        self.extra_args_type = extra_args_type
        self.env_prefix = env_prefix
        self.env_suffix = env_suffix


@dataclass
class _RawLatexEnvironment:
    """Before
    """
    env_name: str  # the literal name of the environment. First letter should be
    # in caps. This is the starter keyword for automatic breaks.
    start: str = 'ȚHE#$$$$$$@%@$#VER!!!ASTA#!!!ȚTT'  # Environment starter keyword. Not supported for automatic breaks.
    end: str = 'TH!!!ERȚ!!WAȚ@#ȚSNE*(VEȚAN*@##END'  # Environment end keyword. Not supported for automatic breaks.
    encapsulation: str = ''  # any modifiers to the environment call.
    initial_newline: bool = False  # if the environment must start on a newline.
    priority: int = 3  # the priority of the env
    has_extra_args: bool = False  # whether you want extra arguments in the envs.
    # for example: \begin{definition}[the definition]. Set to false
    # if you want to have a plain environment.
    extra_args_type: str = 'brace'  # bracket or brace which determines what the extra
    # args should be surrounded by. Must be ON if you want automatic breaks.
    env_prefix: str = ''  # text to append before environment declaration: \begin{env}
    env_suffix: str = ''  # text to append after environment declaration: \begin{env}
    name_alt: str = ''  # Replaces the env name for automatic breaks

    # def create_latex_env(self) -> LatexEnvironment:
    #     pass


def work_with_environments(text, envs: dict) -> str:
    """The master function for working with environments.
    """
    envs = unpack_environments(envs)
    return bulk_environment_wrapper(text, envs)


def check_environments(json_dir: str) -> list[LatexEnvironment]:
    """The old version.
    """
    with open(json_dir) as json_file:
        json_data = json.load(json_file)
    env_dict = json_data["environments"]
    envs_so_far = []

    for env_name, env_info in env_dict.items():
        field_names = set(f.name for f in fields(_RawLatexEnvironment))
        raw_latex_env = _RawLatexEnvironment(**{k: v for k, v in env_info.items() if k in field_names})
        latex_env = LatexEnvironment(raw_latex_env.env_name, raw_latex_env.start, raw_latex_env.end,
                                     raw_latex_env.encapsulation, raw_latex_env.initial_newline,
                                     raw_latex_env.priority, raw_latex_env.has_extra_args,
                                     raw_latex_env.extra_args_type,
                                     raw_latex_env.env_prefix, raw_latex_env.env_suffix,
                                     raw_latex_env.name_alt)
        # latex_env = LatexEnvironment(env_name, env_info['start'],
        #                             env_info['end'], env_info['encapsulation'],
        #                             env_info['initial_newline'], env_info['priority'],
        #                             env_info['has_extra_args'], env_info['extra_args_type'])
        envs_so_far.append(latex_env)
    envs_so_far.sort(key=lambda x: x.priority, reverse=True)
    return envs_so_far


def unpack_environments(envs: dict) -> list[LatexEnvironment]:
    """Unpack the environments dictionary and return a list
    of latex environments.
    """
    # with open(json_dir) as json_file:
    #     json_data = json.load(json_file)
    env_dict = envs  # json_data["environments"]
    envs_so_far = []

    for env_name, env_info in env_dict.items():
        field_names = set(f.name for f in fields(_RawLatexEnvironment))
        raw_latex_env = _RawLatexEnvironment(**{k: v for k, v in env_info.items() if k in field_names})
        latex_env = LatexEnvironment(raw_latex_env.env_name, raw_latex_env.start, raw_latex_env.end,
                                     raw_latex_env.encapsulation, raw_latex_env.initial_newline,
                                     raw_latex_env.priority, raw_latex_env.has_extra_args,
                                     raw_latex_env.extra_args_type,
                                     raw_latex_env.env_prefix, raw_latex_env.env_suffix,
                                     raw_latex_env.name_alt)
        # latex_env = LatexEnvironment(env_name, env_info['start'],
        #                             env_info['end'], env_info['encapsulation'],
        #                             env_info['initial_newline'], env_info['priority'],
        #                             env_info['has_extra_args'], env_info['extra_args_type'])
        envs_so_far.append(latex_env)
    envs_so_far.sort(key=lambda x: x.priority, reverse=True)
    return envs_so_far


def bulk_environment_wrapper(text: str, envs: list[LatexEnvironment]) -> str:
    """Return environment_wrapper(text...) run on all environments.
    """

    # env_stack = environment_stack(text, envs)
    # text = env_wrapper_many(text, env_stack)

    # env_basic = [en for en in envs if not en.has_extra_args]
    env_complex = [en for en in envs if en.has_extra_args]
    for env in envs:
        text = quote_to_environment(text, env, env.has_extra_args)
    for env in env_complex:
        text = environment_wrapper_2(text, env)
    for env in envs:
        text = environment_wrapper(text=text, env=env.env_name, start=env.start,
                                   end=env.end, initial_newline=env.initial_newline,
                                   has_extra_args=env.has_extra_args, extra_args_type=env.extra_args_type,
                                   env_info=env)
    return text


@dataclass
class EnvironmentInstance:
    """This would have been a dict
    Because we only support end breaking characters,
    we only have one end position."""
    tag: str
    start_pos_1: int
    start_pos_2: int
    end_pos: Optional[int] = None


def environment_stack(text: str, envs: list[LatexEnvironment]) -> list[EnvironmentInstance]:
    """Generate and return an environment stack, or a list of environment instances.
    """
    # assume extra args type is turned on by default
    # this is terribly broken
    # env nestings work, but we have to add a ghost environment at the bottom.
    text = text + r"""\emph{Info.} Why do I do this.

    ◺"""
    last_tracking_index = 0
    former_tracking_index = -1
    finished_env_instances = []
    working_env_instances = []
    while True:
        former_tracking_index = last_tracking_index
        tracking_index_so_far = []
        # current objectives: scanning all the env names, figure out which one starts the earliest.
        for env in envs:
            env_start_text = env.start
            temp_start = find_nth(text, env_start_text, 1, last_tracking_index)
            temp_end = temp_start + len(env.start)  # the index AFTER the end of the starting keyword
            env_tag = env.env_name
            temp_dict = {'start': temp_start, 'start_end': temp_end, 'tag': env_tag}
            tracking_index_so_far.append(temp_dict)
        stopper = find_closest_unicode_char_index(text, last_tracking_index)
        if stopper == -1:
            stopper = math.inf
        tracking_index_so_far.sort(key=lambda x: x['start'] if x['start'] != -1 else math.inf, reverse=False)
        target_env_instance = tracking_index_so_far[0]
        tiev_start = target_env_instance['start']
        if tiev_start < 0:
            tiev_start = math.inf
        last_tracking_index = min(tiev_start + 1, stopper + 1)  # the loc AFTER stopper
        # if last_tracking_index == math.inf:
        #     break
        if stopper < target_env_instance['start']:
            working_env_instances[-1].end_pos = stopper
            finished_env_instances.append(working_env_instances.pop())
        elif (target_env_instance['start'] == -1 or target_env_instance == math.inf) and stopper == math.inf:
            # working_env_instances[-1].end_pos = stopper
            # finished_env_instances.append(working_env_instances.pop())
            break
        elif last_tracking_index < former_tracking_index:
            # working_env_instances[-1].end_pos = stopper
            # finished_env_instances.append(working_env_instances.pop())
            break
        else:
            temp_env_instance = EnvironmentInstance(target_env_instance['tag'],
                                                    target_env_instance['start'],
                                                    target_env_instance['start_end'])
            working_env_instances.append(temp_env_instance)
    if len(working_env_instances) != 0:
        logging.warning('You didn\'t close all environments. That may cause problems.'
                        'I will ignore unclosed environments.')
    return finished_env_instances


def find_closest_unicode_char_index(text: str, min_index: int) -> int:
    unicode = ['◾', '▨', '◺']
    indices_so_far = []
    # return min(find_nth(text, uni, 1, min_index) for uni in unicode)
    for uni in unicode:
        ind = find_nth(text, uni, 1, min_index)
        indices_so_far.append(ind)
    if all(u == -1 for u in indices_so_far):
        return -1
    else:
        return min(v for v in indices_so_far if v != -1)


def env_wrapper_many(text: str, env_instances: list[EnvironmentInstance]) -> str:
    """That but multiple times"""
    for env_instance in env_instances:
        text = environment_wrapper_new(text, env_instance)
    return text


def environment_wrapper_new(text: str, env_instance: EnvironmentInstance) -> str:
    """If text is between start and end, place it in an environment.
    This replaces ALL environments.
    text: our text
    env: environment name defined in latex.
    start: substring that indicates the start of an environment.
    end: substring that indicates the end of it.
    initial_newline: if True, '\n' must precede start.
    """
    # weird_unicode_chars = ['◾', '▨', '◺']
    # if initial_newline and start[0] != '\n':
    #     start = '\n' + start
    start_pos_1 = env_instance.start_pos_1
    start_pos_2 = env_instance.start_pos_2
    # indices_so_far = []
    end_pos_7 = env_instance.end_pos
    end_pos_8 = end_pos_7 + 1  # 1 is the length of emojis
    end_pos_1, end_pos_2 = end_pos_7, end_pos_8
    # can't find any; occurs when environments are exhausted
    if -1 in {start_pos_1, start_pos_2, end_pos_1, end_pos_2}:
        return text
    # misplaced environments
    if start_pos_1 >= end_pos_1:
        return text
    begin_env = '\n\\begin{' + env_instance.tag + '}'
    end_env = '\n\\end{' + env_instance.tag + '}\n'

    # if has_extra_args:  # only generate extra args when permitted AND does not cut off on line 1
    start_pos_3 = find_nth(text, '\n\n', 1, start_pos_2)
    if start_pos_3 != -1 and end_pos_1 > start_pos_3 and end_pos_1 - start_pos_3 <= 100:
        # match extra_args_type:
        #    case 'bracket':
        #        brc = ('[', ']')
        #    case 'brace':
        #        brc = ('{', '}')
        #    case _:
        #        brc = ('[', ']')
        extra_env_args = (text[start_pos_2:start_pos_3].strip()).replace('\n', '')
        if all(k in extra_env_args for k in {'{[}', '{]}'}) or all(k in extra_env_args for k in {'\\{', '\\}'}):
            begin_env = begin_env + extra_env_args.replace(r'\{', '{').replace(r'\}', '}'). \
                replace('{[}', '[').replace('{]}', ']')
            spbr = find_nth(text, '\\}', 1, start_pos_2) + 2
            spbc = find_nth(text, '{]}', 1, start_pos_2) + 3
            spbr, spbc = min(spbr, start_pos_3), min(spbc, start_pos_3)
            decrease_value = max(spbr, spbc) if not all(start_pos_3 == x for x in [spbr, spbc]) else start_pos_2
            start_pos_2 += decrease_value

    # prior_text = text[:start_pos_1]
    # post_text = text[:end_pos_2]
    text = text[:start_pos_1] + begin_env + '\n' + text[start_pos_2:end_pos_1].strip() + end_env + text[end_pos_2:]
    # call the function again
    return text  # recursive


# SAMPLE_LATEX_ENV = unpack_environments('config.json')

SAMPLE_ENV_TEXT = r"""
This is some text.

\textbf{Definition - environments:} This is something
that needs to be said

\[some math region\]

we're out not yet.

\begin{itemize}
    \item not anymore?
    \item I don't think so.

\[some math region\]

Now we're out.

\textbf{Corollary.} This does not work. ◺
"""


def environment_wrapper_2(text: str, env_info: LatexEnvironment) -> str:
    """An updated version of the environment wrapper which uses a newer word syntax.
    Compatible with the old environment wrapper, though this is always run first.
    """
    braces = env_info.extra_args_type != 'bracket'
    dashes = {'-', '–', '—'}
    k_begin = r'\begin{' + env_info.env_name.lower() + '}'
    k_end = r'\end{' + env_info.env_name.lower() + '}'
    keyword = env_info.start_alt
    wrapper = 'textbf'
    br = '{}' if braces else '[]'
    allowed_terms = [r'\begin{enumerate}', r'\begin{itemize}']

    keyword_wrapper = '\\' + wrapper + '{' + keyword + ' '
    # find nth: haystack, needle, n, starter = None
    n = 1  # skip
    while True:
        start = find_nth(text, keyword_wrapper, n)
        if start == -1:  # BASE CASE: we couldn't find an environment starter
            break
        start_after = start + len(keyword_wrapper)  # index of the dash
        if (text[start_after] not in dashes) or text[start - 2:start] != '\n\n':
            n += 1
            continue
        # otherwise

        end = local_env_end(text, start)  # find_nth(text, '}', 1, start_after)
        # find_endbrace(text, start_after)
        term = text[start_after + 2:end]
        if term[-1] == ':':
            term = term[:-1]
        next_nl_skip = 1
        while True:  # intent: math regions don't break. Actual: Max of one math region.
            next_newline = find_nth(text, '\n\n', next_nl_skip, end + 1)
            if next_newline == -1:  # base case: there is now next newline. Then give up
                # next_newline = len(text) - 1
                return text
                # break

            elif text[next_newline + 2:next_newline + 4] == r'\[' or text[next_newline + 2] in ALPHABET or any(
                    text[next_newline + 2:].startswith(tx) for tx in allowed_terms):
                next_nl_skip += 1
                continue
            else:
                break
        text = text[:start] + k_begin + br[0] + term + br[1] + env_info.env_suffix + '\n' + text[
                                                                                            end + 1:next_newline].strip() + '\n' + k_end + text[
                                                                                                                                           next_newline:]
    return text


def environment_wrapper(text: str, env: str, start: str, end: str, env_info: LatexEnvironment,
                        initial_newline: bool = False, has_extra_args: bool = False,
                        extra_args_type: str = 'bracket') -> str:
    """If text is between start and end, place it in an environment.
    This replaces ALL environments.
    text: our text
    env: environment name defined in latex.
    start: substring that indicates the start of an environment.
    end: substring that indicates the end of it.
    initial_newline: if True, '\n' must precede start.
    """
    weird_unicode_chars = ['◾', '▨', '◺']
    if initial_newline and start[0] != '\n':
        start = '\n' + start
    start_pos_1 = find_nth(text, start, 1)  # the index of the first char of start.
    start_pos_2 = start_pos_1 + len(start)  # the index of the char after start.
    indices_so_far = []
    for weird_char in weird_unicode_chars:
        end_pos_special = find_nth(text, weird_char, 1, start_pos_2)
        if end_pos_special != -1:
            indices_so_far.append(end_pos_special)
    end_pos_7 = min(indices_so_far) if indices_so_far != [] else math.inf
    end_pos_8 = end_pos_7 + 1  # 1 is the length of emojis
    end_pos_1 = find_nth(text, end, 1, start_pos_2)  # the first index of the ending
    end_pos_2 = end_pos_1 + len(end)  # the character right after the ending
    if end_pos_7 < end_pos_1 or end_pos_1 == -1:
        end_pos_1, end_pos_2 = end_pos_7, end_pos_8
    # can't find any; occurs when environments are exhausted
    if -1 in {start_pos_1, start_pos_2, end_pos_1, end_pos_2}:
        return text
    # misplaced environments
    if start_pos_1 >= end_pos_1:
        return text
    begin_env = '\n\\begin{' + env.lower() + '}'
    end_env = '\n\\end{' + env.lower() + '}\n'

    if has_extra_args:  # only generate extra args when permitted AND does not cut off on line 1
        start_pos_3 = find_nth(text, '\n\n', 1, start_pos_2)
        if start_pos_3 != -1 and end_pos_1 > start_pos_3 and abs(end_pos_1 - start_pos_3) >= 10:
            match extra_args_type:
                case 'bracket':
                    brc = ('[', ']')
                case 'brace':
                    brc = ('{', '}')
                case _:
                    brc = ('[', ']')
            extra_text = text[start_pos_2:start_pos_3]
            begin_env = begin_env + env_info.env_prefix + brc[0] + extra_text.strip() + brc[1] + env_info.env_suffix
            start_pos_2 = start_pos_3
        elif len(env_info.env_suffix) > 0:
            match extra_args_type:
                case 'bracket':
                    brc = ('[', ']')
                case 'brace':
                    brc = ('{', '}')
                case _:
                    brc = ('[', ']')
            extra_text = brc[0] + brc[1]
            begin_env = begin_env + env_info.env_prefix + brc[0] + brc[1] + env_info.env_suffix
            # extra_env_args = (text[start_pos_2:start_pos_3].strip()).replace('\n', '')
            # if all(k in extra_env_args for k in {'{[}', '{]}'}) or all(k in extra_env_args for k in {'\\{', '\\}'}):
            # begin_env = begin_env + extra_env_args.replace(r'\{', '{').replace(r'\}', '}'). \
            #     replace('{[}', '[').replace('{]}', ']')
            # spbr = find_nth(text, '\\}', 1, start_pos_2) + 2
            # spbc = find_nth(text, '{]}', 1, start_pos_2) + 3
            # spbr, spbc = min(spbr, start_pos_3), min(spbc, start_pos_3)
            # decrease_value = max(spbr, spbc) if not all(start_pos_3 == x for x in [spbr, spbc]) else start_pos_2
            # start_pos_2 += decrease_value

    # prior_text = text[:start_pos_1]
    # post_text = text[:end_pos_2]
    text = text[:start_pos_1] + begin_env + '\n' + text[start_pos_2:end_pos_1].strip() + end_env + text[end_pos_2:]
    # call the function again
    return environment_wrapper(text, env, start, end, env_info, initial_newline, has_extra_args,
                               extra_args_type)  # recursive


def dy_fixer(text: str) -> str:
    """Fix how pandoc deals with dy and dx.
    """
    low_letters = {'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o',
                   'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z'}
    cap_letters = {letter.upper() for letter in low_letters}
    extra_letters = {'θ'}
    # I wonder how theta will work with this?
    all_letters = (low_letters.union(cap_letters)).union(extra_letters)
    for letter_instance in all_letters:
        d_text = '\\text{d' + letter_instance + '}'
        d_text_fixed = '\\text{d}' + letter_instance
        text = text.replace(d_text, d_text_fixed)
    return text


# αβγδεϵζηθϑικλμνξοπϖρϱσςτυφϕχψωΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ
REPLAC = {'α': r'\alpha', 'β': r'\beta', 'γ': r'\gamma', 'δ': r'\delta',
          'θ': r'\theta', 'π': r'\pi', 'Ω': r'\Omega'}


def text_bound_fixer(text: str, replacement: dict[str, str], n: int = 1) -> str:
    """Detect and fix text environments with
    unicode characters. Also fix text environments that are two characters
    or shorter.
    """
    # logging.warning('text is ' + text)

    # replacement = {'π': r'\pi'}
    unicode_list = list(replacement.keys())
    # n = 1  # ignored count starting from 1
    btext = r'\text{'
    text_index = find_nth(text, btext, n)
    if text_index == -1:
        # logging.warning('could not find another text env')
        return text
    starting_index = text_index + len(btext)
    layers_in = 0
    min_index = starting_index
    while True:
        inner_brace = text.find(r'{', min_index)
        outer_brace = text.find(r'}', min_index)
        if outer_brace == -1:
            # logging.warning('No outer brace')
            return text
        if inner_brace == -1:
            inner_brace = math.inf
        if inner_brace < outer_brace:
            layers_in += 1
            min_index = inner_brace + 1
            continue
        else:
            if layers_in > 0:
                layers_in -= 1
                min_index = outer_brace - 1
            else:  # if layers_in == 0
                break
    inner_text = text[starting_index:outer_brace]
    fix_region = check_inner_text(inner_text) or check_char_bulk(inner_text, unicode_list)
    # print(text)
    if fix_region:

        # logging.warning('fix region detected')
        for u1, u2 in replacement.items():
            inner_text = inner_text.replace(u1, u2 + ' ')
        text = text[:text_index] + inner_text + text[outer_brace + 1:]
        return text_bound_fixer(text, replacement, n)
    else:
        n += 1
        # logging.warning(n)
        return text_bound_fixer(text, replacement, n)


def check_inner_text(inner_text: str) -> bool:
    """Check if the region of an inner text should be processed.
    We already know no weird unicode characters will be within them.

    TRUE if the region should be fixed
    FALSE if the region should NOT be fixed.
    """
    # DON'T fix if the text is over 2 leters long
    if len(inner_text) >= 3:
        return False
    # AUTO FALSE:
    whitelisted_words = {
        'is', 'be', 'do', 'go', 'hi', 'of', 'so', 'or', 'oh'
    }
    # two letter case
    if inner_text in whitelisted_words:
        return False
    # if it is d by itself and only by itself
    elif inner_text == 'd':
        return False
    else:
        return True


def check_char_bulk(text: str, uni: list[str]) -> bool:
    """Return True if at least one str in uni is in text.
    """
    for u in uni:
        if u in text:
            return True
    return False


def bracket_layers(text: str, index: int,
                   opening_brace: str = '{', closing_brace: str = '}', escape_char: bool = True,
                   starting_index: int = 0) -> int:
    """Return the depth of the index in text based on opening_brace and closing_brace
    When escape_char is true, only if opening_brace / closing_brace are both length 1, then it
    will ignore instances where the escape character is used.

    If the index you are looking at is an opening brace or a closing brace,
    it will check the next position (even if it is blank).

    If the above case is true and the next position is also an opening or closing brace,
    it will treat that the opening or closing brace is not a brace.

    The starting index is the minimum index where brackets will be tracked.

    >>> temp_text = '{123\\{56}89}12'
    >>> bracket_layers(temp_text, 6)
    1
    """
    if not (len(opening_brace) == 1 and len(closing_brace) == 1):
        escape_char = False
    layer = 0
    prev_char = ''
    for i, char in enumerate(text):
        if i < starting_index:
            continue
        if escape_char and prev_char == '\\':
            prev_char = ''
            continue
        if char == opening_brace:
            layer += 1
        if char == closing_brace:
            layer -= 1
        if i == index:
            return layer

        prev_char = char
    if index == -1:
        return layer
    else:
        raise IndexError('Your index was out of bounds.')


def split_all_equations(text: str, max_len: int, skip: int = 0) -> str:
    """Split equation done for all equations.
    Must be done before dollar sign equations, but after alignment regions
    are processed for the first time. If fix alignment regions are off,
    this may not run.

    Initially, skip must always be set to 0.
    """
    starting_index = find_nth(text, r'\[', skip + 1)
    finishing_index = find_nth(text, r'\]', skip + 1)
    if -1 in (starting_index, finishing_index):
        return text
    assert starting_index < finishing_index
    eqn_text = text[starting_index + 2:finishing_index]
    new_eqn_text = split_equation(eqn_text, max_len)
    if new_eqn_text is None:
        return split_all_equations(text, max_len, skip + 1)
    else:
        try:
            text = text[:starting_index] + r'\[' + new_eqn_text + r'\]' + text[finishing_index + 2:]
            return split_all_equations(text, max_len, skip + 1)
        except IndexError:
            text = text[:starting_index] + r'\[' + new_eqn_text + r'\]'
            return split_all_equations(text, max_len, skip + 1)


def split_equation(text: str, max_len: int, list_mode: bool = False) -> None | str | list[str]:
    """Return a split version of an equation.
    text is the raw equation text.
    max_len is the max length of an equation line before a newline
    has to be added.
    Return none if the equation does not need to be split.
    If list_mode is set to True, then return as a list of strings.
    """
    text = text.strip()
    eqn_len = calculate_eqn_length(text)  # split equal signs.
    breaker_chars = {'<', '>', '\\leq', '\\geq', '=', '\\subset', '\\subseteq', '\\not\\subset', '\\neq'}
    if eqn_len > max_len and any(x in text for x in breaker_chars):
        # everything goes down here
        equal_indexes = [0]  # the index where equal signs start.
        for i, char in enumerate(text):
            if char in {'=', '<', '>', r'\leq', r'\geq'} and bracket_layers(text, i) == 0:
                equal_indexes.append(i)
        lines_of_eqn = []
        for i, eq_index in enumerate(equal_indexes):
            if i == 0:
                continue
            temp_start = equal_indexes[i - 1]
            temp_end = eq_index
            lines_of_eqn.append(text[temp_start:temp_end])

        # now we have the lines of equation
        # now we want to distribute them
        master = []
        cur_line = []
        for eqn_line in lines_of_eqn:
            cur_line.append(eqn_line)
            cur_line_len = calculate_eqn_length(''.join(cur_line))
            if cur_line_len > max_len and len(cur_line) >= 2:
                cur_line.pop(-1)
                master.append(cur_line)
                cur_line = [eqn_line]
        if cur_line:
            master.append(cur_line)
        # combine everything.
        new_master = [''.join(cl) for cl in master]
        final_str = ''
        if not list_mode:
            for line in new_master:
                final_str = final_str + '{' + line + '}'
            return final_str
        else:
            return new_master


def calculate_eqn_length(text: str, disable: Optional[Iterable] = None) -> int:
    """Return the relative length of an equation line.
    """
    # list of defined functions:
    if disable is None:
        disable = []
    text = text.lower()
    predetermined_functions = {'sin', 'cos', 'tan', 'csc', 'sec', 'cot', 'arcsin', 'arccos', 'arctan',
                               'log', 'ln', 'sqrt', 'sinh', 'cosh', 'tanh', 'coth'}
    # text = text.replace('\\left', '')
    # text = text.replace('\\right', '')

    # fraction blocks (this will recursively run itself)
    if 'frac' not in disable:
        while True:
            frac_index = find_nth(text, r'\frac', 1)
            if frac_index == -1:
                break
            ending_frac_index = index_fourth_closing_bracket(text, frac_index) + 1  # AT the char AFTER }
            if ending_frac_index == 0:
                break
            text = text[:frac_index] + seperate_fraction_block(text[frac_index:ending_frac_index]) + \
                   text[ending_frac_index:]

    if 'matrix' not in disable:
        text = remove_matrices(text, 'matrix')
        text = remove_matrices(text, 'bmatrix')

    for fun in predetermined_functions:
        text = text.replace('\\' + fun, fun)

    text = remove_envs(text)
    text = text.replace(' ', '')
    text = text.replace(',', ', ')
    if disable is None:
        pass
    logging.warning(text)
    return len(text)


def remove_envs(text: str) -> str:
    """Remove everything between \\ up until it's not a letter

    >>> temp_text = r'\lim(2+4)+\sum(3+6)'
    >>> remove_envs(temp_text)
    '(2+4)+(3+6)'
    """
    backslash_location = -1
    index_diff = 0
    first_backslash = False
    ending_location = -1
    for i, char in enumerate(text):
        if not first_backslash and char == '\\':
            backslash_location = i
            first_backslash = True
            continue
        if first_backslash:
            if char in ALPHABET:
                index_diff += 1
            else:
                if index_diff == 0:
                    first_backslash = False
                else:
                    ending_location = i
                    break
    if backslash_location == -1 or ending_location == -1:
        return text
    else:
        text = text[:backslash_location] + 'j' + text[ending_location:]
        return remove_envs(text)


def index_fourth_closing_bracket(text: str, index: int) -> int:
    """Return the index of the fourth closing bracket starting at index.
    """
    bracket_positions = []
    bracket_layers_sep = 0
    prev_char = None
    for i, char in enumerate(text):
        if i <= index:
            prev_char = char
            continue
        else:
            if prev_char != '\\':
                if char == '{':
                    if bracket_layers_sep == 0:
                        bracket_positions.append(i)
                    bracket_layers_sep += 1
                if char == '}':
                    if bracket_layers_sep == 1:
                        bracket_positions.append(i)
                        if len(bracket_positions) == 4:
                            return i
                    bracket_layers_sep -= 1
            prev_char = char
    return -1


def seperate_fraction_block(frac_text: str) -> str:
    """Return the side of the fraction that is longer.
    Preconditions:
        - frac_text looks like \\frac{}{}

    >>> temp_text = r'\frac{2+4+6}{7}'
    >>> seperate_fraction_block(temp_text)
    '2+4+6'
    """
    bracket_positions = []
    bracket_layers_sep = 0
    prev_char = None
    for i, char in enumerate(frac_text):
        if prev_char != '\\':
            if char == '{':
                if bracket_layers_sep == 0:
                    bracket_positions.append(i)
                bracket_layers_sep += 1
            if char == '}':
                if bracket_layers_sep == 1:
                    bracket_positions.append(i)
                bracket_layers_sep -= 1
        prev_char = char
    assert bracket_positions[-1] == len(frac_text) - 1  # the last closing brace
    numerator = frac_text[bracket_positions[0] + 1:bracket_positions[1]]
    denominator = frac_text[bracket_positions[2] + 1:bracket_positions[3]]
    num_len = calculate_eqn_length(numerator, ['frac', 'matrix'])
    den_len = calculate_eqn_length(denominator, ['frac', 'matrix'])
    return numerator if num_len >= den_len else denominator


def remove_matrices(text: str, matrix_type: str) -> str:
    """Approximate the length of all matrices.
    """
    start = r'\begin{' + matrix_type + '}'
    end = r'\end{' + matrix_type + '}'
    start_pos_1 = find_nth(text, start, 1)  # the index of the first char of start.
    start_pos_2 = start_pos_1 + len(start)  # the index of the char after start.
    end_pos_1 = find_nth(text, end, 1)
    end_pos_2 = end_pos_1 + len(end)
    # can't find any; occurs when environments are exhausted
    if -1 in {start_pos_1, start_pos_2, end_pos_1, end_pos_2}:
        return text
    else:
        matrix_text = text[start_pos_2:end_pos_1].replace('\n', '')
        matrix_rows = matrix_text.split(r'\\')
        row_len = []  # a list of ints
        for row in matrix_rows:
            row_len.append(calculate_eqn_length(row, ['frac', 'matrix']))
        max_row_len = max(row_len)
    text = text[:start_pos_1] + 'a' * max_row_len + text[end_pos_2:]
    return remove_matrices(text, matrix_type)


def combine_environments(text: str, env: str) -> str:
    """Combine broken-up environments.
    Example: env = 'align*'"""
    skip = 1
    end_str = '\\end{' + env + '}'
    begin_str = '\\begin{' + env + '}'
    while True:
        end_pos = find_nth(text, end_str, skip)
        if end_pos == -1:
            break
        next_start_pos = find_nth(text, begin_str, 1, end_pos + len(end_str))
        if next_start_pos == -1:
            break
        # this is the position of the backslash of the next environment
        text_between = text[end_pos + len(end_str):next_start_pos]
        if check_region_empty(text_between):
            text = text[:end_pos] + r' \\' + text[next_start_pos + len(begin_str):]
        else:
            skip += 1
    return text


def check_region_empty(text_between: str) -> bool:
    """Check if text_between only contains newline characters and spaces
    """
    for char in text_between:
        if char not in {' ', '\n'}:
            return False
    return True


TEMP_OLD_TEXT = r"""
\title{This is the title for now}
\author{PLEASE DO THIS I CANNOT}
\date{YESTERDAY I DID}
"""


def test_author() -> None:
    """Why
    """
    aa = swap_author(TEMP_OLD_TEXT, 'John', 'author')
    # print(aa)


def swap_day_with_today(text: str) -> str:
    """Swap the date of the document with today.
    If there is no date specified, then add a date with today.
    """
    raise NotImplementedError


def find_author(text: str, props: str = 'author') -> str:
    """Find the current author of the text.
    text is the entire text.
    Raise ValueError if we can't find an author.
    """
    auth = '\\' + props + '{'
    author_pos = find_nth(text, auth, 1) + len(auth)
    if author_pos == -1:
        raise ValueError
    else:
        end_author_pos = find_nth(text, '\n', 1, author_pos) - 1  # focused on the closing bracket
        author_name = text[author_pos:end_author_pos]
        return author_name


def swap_author(text: str, new_author: str, props: str = 'author') -> str:
    """Change the author. text is the entire text.
    If no existing author field, return what is written in text.
    """
    auth = '\\' + props + '{'
    author_pos = find_nth(text, auth, 1)
    if author_pos == -1:
        return text
    end_author_pos = find_nth(text, '\n', 1, author_pos)
    return text[:author_pos] + auth + new_author + '}' + text[end_author_pos:]


def strip_string(text: str) -> str:
    """Strip the string.
    """
    text = text.replace('\n', '')
    return text.strip()


# OBJECTIVES: For each section, remove any newline characters in between them.


def modify_text_in_environment(text: str, env: str, modification: Callable[[str], str]) -> str:
    """Modify text in all instances of the environment env.
    Preconditions:
        - No LaTeX code in verbatim environments
        - Target environment doesn't nest any additional environments
    this will not work for things that are not defined as environments
    """
    envs_traversed = 1
    begin = r'\begin{' + env + '}'
    end = r'\end{' + env + '}'
    while True:
        # print(envs_traversed)
        start_pos_1 = find_nth(text, begin, envs_traversed)  # the index at the backslash of begin
        start_pos_2 = start_pos_1 + len(begin)  # the index on the char after begin env

        end_pos_1 = find_nth(text, end, envs_traversed)
        # end_pos_2 = end_pos_1 + len(end)

        if -1 in {start_pos_1, end_pos_1}:
            break

        before = text[:start_pos_2]
        during = text[start_pos_2:end_pos_1]
        after = text[end_pos_1:]

        during = modification(during)

        text = before + during + after
        envs_traversed += 1
    return text


def longtable_backslash_add_line(text: str) -> str:
    """Add hline after all \\s, except the first one and the last one.

    Preconditions: no align regions or anything containing backslashes are allowed
    """
    text = text.replace(r'\\', '🯰', 1)
    backslash_occur = text.count(r'\\')
    text = text.replace(r'\\', r'\\ \hline', backslash_occur - 1)
    text = text.replace('🯰', r'\\')
    return text


def longtable_backslash_add_full(text: str) -> str:
    return modify_text_in_environment(text, 'longtable', longtable_backslash_add_line)


# bracket_layers is a useful function


TEST_BIB = r"""
@conference{Xconference,
    author    = "",
    title     = "",
    booktitle = "",
    ?_editor   = "",
    ?_volume   = "",
    ?_number   = "",
    ?_series   = "",
    ?_pages    = "",
    ?_address  = "",
    year      = "XXXX",
    ?_month    = "@youuuu",
    ?_publisher= "",
    ?_note     = "",
}

@customone{thenotthe,
    author    = "",
    title     = "",
    booktitle = "",
    ?_editor   = "",
    ?_volume   = "",
    ?_number   = "",
    ?_series   = "",
    ?_pages    = "",
    ?_address  = "",
    year      = "XXXX",
    ?_month    = "",
    ?_publisher= "",
    ?_note     = "",
}
"""


def extract_authors_from_bib(bib_text: str) -> list[str]:
    """Return a list of author tags from a .bib file.

    Preconditions:
        - bib_text is the text contents of the .bib file and must be formatted as such.
        - author tags don't have commas
        - none of the file types referenced are in a format that requires an opening brace
    """
    skip = 1
    authors = []
    while True:
        at_ind = find_nth(bib_text, '@', skip)
        if at_ind == -1:
            break
        # who would ever put an @ symbol inside any field that isn't an author declaration
        bracket_layer = bracket_layers(bib_text, at_ind)
        if bracket_layer > 0:
            logging.info('someone put an @ symbol inside the citation thing')
            skip += 1
            continue
        bracket_afterwards = find_nth(bib_text, '{', 1, at_ind)
        comma_afterwards = find_nth(bib_text, ',', 1, bracket_afterwards)
        author_name = bib_text[bracket_afterwards + 1:comma_afterwards]
        authors.append(author_name)
        skip += 1
    return authors


EX_AT = r"""
\title{Title}
\subtitle{Subtitle}
\author{Author}
\date{What day is it}
"""


def retain_author_info(text: str) -> str:
    """Return author-related metadata
    """
    mdl = ['title', 'author', 'date']
    metadata = {}
    for md in mdl:
        try:
            auth = find_author(text, md)
            metadata[md] = auth
        except ValueError:
            pass
    author_text = ''
    for mdd, txt in metadata.items():
        author_text += '\\' + mdd + '{' + txt + '}\n'
    return author_text


def verbatim_to_listing(text: str, lang: str) -> str:
    """Converts all verbatim environments to the language in question.
    No language detection is done.
    Language must be in this list:
    https://www.overleaf.com/learn/latex/Code_listing
    """
    text = text.replace(r'\begin{verbatim}', r'\begin{lstlisting}[language=' + lang + ']')
    text = text.replace(r'\end{verbatim}', r'\end{lstlisting}')
    return text


def any_layer(text: str, index: int, start: str, end: str) -> int:
    """Return the depth of the index in text, depending on start and end.

    If the index is in the middle of start and end, the first letter
    of the starting and ending keywords will act as the marker.

    If the index is on the first character of the start and end
    keyword, it will act as the index is one more, then do calculations
    normally.

    Preconditions:
        - '\\' + start not in text
        - '\\' + end not in text

    >>> start_t = 'start'
    >>> end_t = 'end'
    >>> text_t = 'start01end234start0123end789end'
    >>> any_layer(text_t, 19, start_t, end_t)
    1
    """
    n1 = 1
    starting_ind = []
    while True:
        temp_ind = find_nth(text, start, n1)
        if temp_ind == -1:
            break
        else:
            starting_ind.append(temp_ind)
            n1 += 1
    n2 = 1
    ending_ind = []
    while True:
        temp_ind2 = find_nth(text, end, n2)
        if temp_ind2 == -1:
            break
        else:
            ending_ind.append(temp_ind2)
            n2 += 1
    start_depth = lst_smaller_index(index, starting_ind)
    ending_depth = lst_smaller_index(index, ending_ind)
    final_depth = start_depth - ending_depth
    return final_depth


def lst_smaller_index(item: int, lst: list[int]) -> int:
    """Return the index AFTER where item occurs in list.
    Otherwise, return the index where item is greater than
    the item of the current index, but less than the item of the
    next index.

    Preconditions:
        - lst is sorted
        - lst has no repeating elements

    >>> tl = [2, 4, 6, 8, 10]
    >>> lst_smaller_index(10, tl)
    5
    >>> lst_smaller_index(7, tl)
    3
    >>> lst_smaller_index(6, tl)
    3
    >>> lst_smaller_index(5, tl)
    2
    >>> lst_smaller_index(4, tl)
    2
    >>> lst_smaller_index(3, tl)
    1
    >>> lst_smaller_index(2, tl)
    1
    >>> lst_smaller_index(1, tl)
    0

    """
    for i, li in enumerate(lst):
        if item < li:  # 1
            return i
    return len(lst)


def local_env_layer(text: str, index: int, local_env: str) -> bool:
    """Return whether index is in a local environment.
    Like black slash texttt or so on.

    Preconditions:
        - index isn't located anywhere where the env substring appears
        - text[index] != '}'
        - '}' not in local_env

    >>> te = 'abc\\wh{force}the'
    >>> local_env_layer(te, 10, 'wh')
    True
    """
    env_kw = '\\' + local_env + '{'
    closest_starter = text.rfind(env_kw, 0, index)  # type: int
    if closest_starter == -1:
        return False
    n = 1
    # cur_ind = None
    while True:
        closest_bracket = find_nth(text, '}', n, closest_starter)
        if closest_bracket == -1:
            raise ValueError
        b_layer = bracket_layers(text, closest_bracket, starting_index=closest_starter)
        if b_layer == 0:
            # cur_ind = closest_bracket
            break
        else:
            n += 1
    return closest_starter < index < closest_bracket


def local_env_end(text: str, index: int) -> int:
    """Return the position of the closing brace where the local environment ends.

    It is strongly recommended that text[index] == '\\' and
    is the start of a local environment declaration.

    >>> te = 'abc\\wh{fo3rce}the'
    >>> local_env_end(te, 3)
    13
    """
    n = 1
    while True:
        closest_bracket = find_nth(text, '}', n, index)
        if closest_bracket == -1:
            raise ValueError
        b_layer = bracket_layers(text, closest_bracket, starting_index=index)
        if b_layer == 0:
            # cur_ind = closest_bracket
            break
        else:
            n += 1
    return closest_bracket


TEST_STR_AGAIN = r"""
CCCCCC
\begin{verbatim}
ccccccccccccccccccccc
\end{verbatim}
CCCCCC
"""


def check_in_environment(text: str, env: str, index: int) -> bool:
    """Return if current index in environment.

    Preconditions:
        - index is not part of any environment declarations.

    >>> check_in_environment(TEST_STR_AGAIN, 'verbatim', 29)
    True
    """
    if index < 0:
        index = len(text) - index
    env_str = '\\begin{' + env + '}'
    env_end = '\\end{' + env + '}'
    v1_cie = text.find(env_str, index)  # this is allowed to be -1. Fallback to len(text)
    if v1_cie == -1:
        v1_cie = len(text)
    v2_cie = text.find(env_end, index)
    if v2_cie == -1:
        return False
    v3_cie = text.rfind(env_str, 0, index)
    if v3_cie == -1:
        return False
    v4_cie = text.rfind(env_end, 0, index)  # this is allowed to be -1.
    return not (v1_cie < v2_cie or v4_cie > v3_cie)


def do_something_to_local_env(text: str, env: str, func: Callable[[str], str]) -> str:
    """Do something to everything in a local environment.
    Such as texttt{modify stuff here}.

    Preconditions:
        - No LaTeX-like code in verbatim environments
    """
    env_str = '\\' + env + '{'
    skip = 1
    while True:
        # locate where the next environment is
        ind = find_nth(text, env_str, skip)
        if ind == -1:
            break
        # locate where the local environment ends
        local_skip = 1
        while True:
            ind_2 = find_nth(text, '}', local_skip, ind)
            if text[ind_2 - 1] == '\\':
                local_skip += 1
                continue
            assert ind_2 != -1
            bracket_layer = bracket_layers(text, ind_2)
            if bracket_layer == 0:
                break
            else:
                local_skip += 1
                # continue
        # Do stuff in the text. TODO: Enable ignore nested envs; enable ignore commands
        env_text = text[ind + len(env_str):ind_2]
        new_env_text = func(env_text)
        text = text[:ind + len(env_str)] + new_env_text + text[ind_2:]
        skip += 1
    return text


RRR = r"""
\[\begin{matrix}
\int_{}^{}{4 + 2dx} + \sqrt{4 + 2}\ \# 40 \\
\end{matrix}\]

\[\begin{matrix}
\int_{}^{}{4 + 2dx} + \sqrt{4 + 2}\ \# 40 \\
\end{matrix}\]

\[\begin{matrix}
\int_{}^{}{4 + 2dx} + \sqrt{4 + 2}\ \# 40 \\
\end{matrix}\]

\[\begin{matrix}
\int_{}^{}{4 + 2dx} + \sqrt{4 + 2}\ \# 40 \\
\end{matrix}\]
"""


def bad_backslash_replacer(text: str, eqs: str = '\\[', eqe: str = '\\]') -> str:
    """Replaces all bad backslash instances with just spaces.
    """
    rpl = r'\ '
    # eqs = r'\['
    # eqe = r'\]'
    fake_unicode = '🮿'
    ind = 0
    while True:
        try:
            extracted, st_in, en_in = find_between(text, eqs, eqe, ind)
        except ValueError:
            break
        extracted = extracted.replace(r'\ \text{', fake_unicode)
        extracted = extracted.replace(rpl, ' ')
        extracted = extracted.replace(fake_unicode, r'\ \text{')
        text = text[:st_in] + extracted + text[en_in:]
        ind = st_in + len(eqs) + len(extracted) + len(eqe)
    return text


def find_between(s: str, first: str, last: str, stt: int) -> tuple[str, int, int]:
    """Return extracted string between two substrings, start index, and end index
    start index is based on extracted.
    """
    start = s.index(first, stt) + len(first)
    end = s.index(last, start)
    return s[start:end], start, end


TEST_TEXT_AGAIN = r"""
\end{proof}
\begin{proof}
proof text here
\begin{proof}
\begin{proof}
\begin{proof}
\end{proof}
\end{proof}
\end{proof}
\end{proof}
\begin{proof}
\begin{proof}

\begin{proof}
\begin{proof}


"""

TEST_DOC_2 = r"""

\section{aaaaa}
THIS IS THIS IS
THIS IS THIS IS
\subsection{THIS IS THIS IS}
THIS IS THIS IS THIS IS THIS
THIS IS THIS IS THIS IS THIS IS
THIS IS THIS IS THIS
\subsubsection{THIS IS THIS IS THIS IS}
COMPLETELY BLANK TEXT
"""


def extract_all_sections(text: str) -> list[str]:
    """Extract all sections from this document."""
    sections = []
    prev_ind_so_far = -1
    while True:
        # print('in while loop')
        cur_ind_so_far = find_next_section(text, prev_ind_so_far + 1)
        # print(cur_ind_so_far)
        section_text = text[prev_ind_so_far:cur_ind_so_far]
        sections.append(section_text)
        prev_ind_so_far = cur_ind_so_far
        if cur_ind_so_far >= len(text):
            break
    return sections


def environment_fallback(text: str, target_env: str) -> str:
    """Prevents environments from not being closed.
    An environment is not closed if it is open within a section
    and closed after the section ends.

    Also, if an environment is not open in a section but closed in
    a later section, then we have a problem.

    A proof environment is well-formed if it is well formed.
    """
    env_str = '\\begin{' + target_env + '}'
    env_end = '\\end{' + target_env + '}'
    # n = 1
    # m = 1
    # begin environments without proper endings
    new_section_list = []
    section_list = extract_all_sections(text)
    for t_section in section_list:
        n = 1
        m = 1
        while True:
            closest_start = find_nth(text, env_str, n, 0)
            closest_end = find_nth(text, env_end, m, 0)
            if closest_start != -1 and closest_end != -1 and closest_start > closest_end:
                # remove closest end and retry
                t_section = t_section[:closest_end] + t_section[closest_end + len(env_end):]
            elif closest_end == -1 and closest_start != -1:
                # only start exists? remove it
                t_section = t_section[:closest_start] + t_section[closest_start + len(env_str):]
            elif closest_start == -1 and closest_end != -1:
                # remove closest end and retry
                t_section = t_section[:closest_end] + t_section[closest_end + len(env_end):]
            elif closest_start == -1 and closest_end == -1:
                break
            else:
                n += 1
                m += 1
        new_section_list.append(t_section)
    return ''.join(new_section_list)

    # preconditions: both above is not -1. Otherwise, we have to handle them seperately
    #     section_from_start = find_next_section(text, closest_start)
    #     if closest_start != -1 and closest_end != -1:
    #         if closest_start < closest_end and not (closest_start <= section_from_start <= closest_end):
    #             # passable
    #             n += 1
    #             m += 1
    #             continue
    #         elif closest_start < closest_end and closest_start <= section_from_start <= closest_end:
    #             # remove the proof starters and proof stoppers
    #             text = text[:closest_start] + text[closest_start + len(env_str):] + text[:closest_end] + text[closest_end + len(env_end):]
    #         else:
    #             # closest end is before closest start so remove the proof closure
    #             text = text[:closest_end] + text[closest_end + len(env_end):]
    #     elif closest_start == -1 and closest_end != -1:
    #         # remove it
    #         text = text[:closest_end] + text[closest_end + len(env_end):]
    #     elif closest_end == -1 and closest_start != -1:
    #         # conclude at end of section
    #         text = text[:section_from_start] + env_end + text[:section_from_start]
    #     elif closest_end == -1 and closest_end == -1:
    #         # stop checking
    #         break
    # return text
    #

    #     env_s_ind = find_nth(text, env_str, n)
    #     if env_s_ind == -1:
    #         break
    #     env_next_s_ind = find_nth(text, env_str, n + 1)
    #     if env_next_s_ind == -1:
    #         env_next_s_ind = len(text)
    #     ending_env_ind = text.find(env_end, env_s_ind)
    #     if ending_env_ind == -1:
    #         ending_env_ind = env_next_s_ind
    #     next_section_ind = find_next_section(text, env_s_ind)
    #     if next_section_ind < ending_env_ind < env_next_s_ind:
    #         # if the next section starts before the proof ends
    #         logging.warning('Found a runaway environment definition')
    #         text = text[:next_section_ind] + '\n' + env_end + '\n\n' + text[next_section_ind:]
    #     elif env_next_s_ind < ending_env_ind < next_section_ind:
    #         # if the next proof starts before the current proof ends
    #         logging.warning('Found a new environment declaration whilst the previous one'
    #                         ' never closed')
    #         text = text[:env_next_s_ind] + '\n' + env_end + '\n\n' + text[env_next_s_ind:]
    #         print(text)
    #     elif env_next_s_ind == ending_env_ind == next_section_ind:
    #         # if the proof doesn't close and the end of the document hits without
    #         # any of the other cases occurring
    #         logging.warning('end of document reached')
    #         text = text[:env_s_ind] + text[env_s_ind + len(env_str):]
    #     n += 1
    # # end environments without proper beginnings
    # n = 1  # reset n again
    # while True:
    #     env_e_ind = find_nth(text, env_end, n)
    #     if env_e_ind == -1:
    #         break
    #     prev_env_end = text.rfind(env_end, 0, env_e_ind)
    #     # -1 fallback default
    #     if prev_env_end == -1:
    #         prev_env_end = -5
    #     prev_section = find_previous_section(text, env_e_ind)
    #     # -1 fallback default
    #     prev_env_start = text.rfind(env_str, 0, env_e_ind)
    #     # -1 fallback default
    #     if prev_env_start == -1:
    #         prev_env_start = -7
    #     # this is required:
    #     # the declaration for the environment must be before the environment ending
    #     # and the declaration for the previous section must be placed before
    #
    #     condition = prev_env_start > prev_env_end and prev_env_start > prev_section
    #     if condition:
    #         n += 1
    #     else:
    #         text = text[:env_e_ind] + text[env_e_ind + len(env_end):]
    # return text


def find_previous_section(text: str, max_index: int, max_depth: int = 6) -> int:
    """Find when the previous section / subsection / subsubsection occurs.
    The number returned should be the index of the backslash of whehere
    the new section occurs.
    """
    highest_start = 0
    if max_depth < 0:
        max_depth = 0
    for i in range(max_depth, -1, -1):
        section_keyword = '\\' + 'sub' * i + 'section' + '{'
        s_start = text.rfind(section_keyword, 0, max_index)
        # -1 already does the job here
        if highest_start < s_start:
            highest_start = s_start
    return highest_start


def find_next_section(text: str, min_index: int, max_depth: int = 6) -> int:
    """Find when the next section / subsection / subsubsection occurs.
    The number returned should be the index of the backslash of where
    the new section occurs.
    section is depth 0. subsection is depth 1.
    If it can't find the next section then return the position of the end of the document.
    """
    lowest_start = len(text)
    if max_depth < 0:
        max_depth = 0
    for i in range(max_depth, -1, -1):
        section_keyword = '\\' + 'sub' * i + 'section' + '{'
        # print(f'looking for {section_keyword}')
        s_start = text.find(section_keyword, min_index)
        if s_start == -1:
            s_start = len(text)
        if lowest_start > s_start:
            lowest_start = s_start
    return lowest_start


def quote_to_environment(text: str, env: LatexEnvironment, has_extra_args: bool = True) -> str:
    """Turns quotes to environments. env is the name of the env to convert to.
    env_kw is the keyword for this region to be formatted like this (syntax in MD):
    **Definition: Extra args.** Definition text.
    Text boldface must be used here.

    has_extra_args: you know what this is.

    Syntax: Env call: <Env tag>. <Text afterwards>
    We assume Env call is bolded before being passed to this function.

    Preconditions:
        - No LaTeX code in verbatim environments
        - Target environment doesn't nest any additional environments
    this will not work for things that are not defined as environments
    """
    envs_traversed = 1
    begin = r'\begin{quote}' + '\n'
    end = '\n' + r'\end{quote}'
    while True:
        # print(envs_traversed)
        start_pos_1 = find_nth(text, begin, envs_traversed)  # the index at the backslash of begin
        start_pos_2 = start_pos_1 + len(begin)  # the index on the char after begin env

        end_pos_1 = find_nth(text, end, envs_traversed)
        # end_pos_2 = end_pos_1 + len(end)

        if -1 in {start_pos_1, end_pos_1}:
            break

        # before = text[:start_pos_2]
        during = text[start_pos_2:end_pos_1]

        tbf = r'\textbf{'

        if not during.startswith(tbf):
            envs_traversed += 1
            continue
        declare_end = local_env_end(during, 0)
        bold_str = during[len(tbf):declare_end]
        if not bold_str.startswith(env.env_name):  # is something like "Definition" or an alias to that
            envs_traversed += 1
            continue
        k_begin = r'\begin{' + env.env_name.lower() + '}'
        k_end = r'\end{' + env.env_name.lower() + '}'
        env_starter_contents = bold_str.split(':')
        if has_extra_args:
            if len(env_starter_contents) == 2:
                env_title = env_starter_contents[1].strip().replace('\n', ' ')
            elif len(env_starter_contents) == 1:
                env_title = ''
            else:
                assert False  # who decided to put more than one colon?
            br = ('[', ']') if env.extra_args_type == 'bracket' else ('{', '}')
            text = text[:start_pos_1] + env.env_prefix + k_begin + br[0] + \
                   env_title + br[1] + \
                   env.env_suffix + '\n' + \
                   during[declare_end + 1:end_pos_1] + k_end + text[end_pos_1 + len(end):]
        else:
            text = text[:start_pos_1] + env.env_prefix + k_begin + \
                   env.env_suffix + '\n' + \
                   during[declare_end + 1:end_pos_1].strip() + k_end + text[end_pos_1 + len(end):]
    return text


def detect_if_bib_exists(text: str) -> tuple[bool, str, int]:
    """Return True if there is an upper section named this:

    Bibliography

    This is case-sensitive, but no trailing whitespaces or newlines.

    If True is returned, it will also return text with the bib section removed.
    It will also return the index where the original bibliography was.
    Otherwise, it will return text with no modifications.

    No works cited or references - we want Chicago style only.
    """
    bib_section: str = '\\section{Bibliography}'
    r_location = text.rfind(bib_section)
    if r_location == -1:
        return False, text, -1
    # else
    next_section = find_next_section(text, r_location + len(bib_section), max_depth=0)
    text = text[:r_location] + '\n\n\n' + text[next_section:]
    return True, text, r_location + 1


def verb_encryptor(count: int) -> str:
    """This was a list of verb encryptors, but
    we wouldn't list everything

    Preconditions:
        - count >= 0
    """
    return f'🬟{count}⚋⚌⚍⚎⚏🬯'


# def check_verbatims() -> str:
#     """I just want to see if this works
#
#     """
#     txt = r"""
#     no longer encrypted
#     \begin{verbatim}
#         encrypted
#     \end{verbatim}
#     not encrypted yet
#     \begin{verbatim}
#         encrypted
#     \end{verbatim}
#     not encrypted yet
#     """
#     txt, d_info = hide_verbatims(txt)
#     pass
#     tx = show_verbatims(txt, d_info)
#     print(tx)
#     return tx

def hide_verbatims(text: str) -> tuple[str, dict[str, str]]:
    """Hide all verbatim stuff.
    Put them in a dictionary.

    Note: the begin and end verbatim calls will still be present in the document. It is merely
    the text contents that are being concealed.
    """
    env = 'verbatim'
    envs_traversed = 1
    begin = r'\begin{' + env + '}'
    end = r'\end{' + env + '}'
    dict_so_far = {}
    i = 0
    while True:
        # print(envs_traversed)
        start_pos_1 = find_nth(text, begin, envs_traversed)  # the index at the backslash of begin
        start_pos_2 = start_pos_1 + len(begin)  # the index on the char after begin env

        end_pos_1 = find_nth(text, end, envs_traversed)
        # end_pos_2 = end_pos_1 + len(end)

        if -1 in {start_pos_1, end_pos_1}:
            break

        before = text[:start_pos_2]
        during = text[start_pos_2:end_pos_1]
        after = text[end_pos_1:]

        ve_value = verb_encryptor(i)
        dict_so_far[ve_value] = during
        during = ve_value

        text = before + during + after
        envs_traversed += 1
        i += 1
    return text, dict_so_far


def show_verbatims(text: str, verb_info: dict[str, str]) -> str:
    """Unhide all verbatim environments.
    """
    for key, value in verb_info.items():
        text = text.replace(key, value)
    return text
