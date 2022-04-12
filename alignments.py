"""This module helps align equations.
"""
import logging
from typing import Optional, Union

# import os
import re
# import sys
import helpers as dbl

import sys
sys.setrecursionlimit(20000)
# (   ]
# 'aaa(aa]aa' to 'aaa[removed]aa[removed]aa'
# import time


# def work_with_file(file: str, output: str, citation_path: str):
#     """Work with latex code.
#     """
#     # opening stuff
#     with open(file) as f:
#         file_text = f.read()
#     # fixing stuff
#     new_file_text = latex_repair(file_text, citation_path)
#     # print(new_file_text)
#     # writing the output
#     with open(output, 'w') as f:
#         f.write(new_file_text)


# def work_with_multiple_files(file1: str, file2: str, output: str):
#     """Work with two latex code. file1 gets inserted into file2.
#     """
#     with open(file1) as f:
#         file_text_1 = f.read()
#     with open(file2) as f:
#         file_text_2 = f.read()
#     new_file_text_1 = latex_repair(file_text_1, '', False)
#     new_file_text_2, new_file_start, new_file_end = document_extract(file_text_2)
#     preamble_mode = dbl.deduce_preamble_mode(new_file_text_2)
#     new_file_start = dbl.insert_in_preamble(new_file_start, preamble_mode)
#     new_file_text_3 = dbl.many_instances(new_file_text_1, new_file_text_2)
#     new_file_text_4 = new_file_start + new_file_text_3 + new_file_end
#
#     with open(output, 'w') as f:
#         f.write(new_file_text_4)


def document_extract(tex_file: str) -> tuple[str, str, str]:
    """Return everything in the document environment, the text before, and the text after.
    """
    start = '\\begin{document}'
    end = '\\end{document}'
    document_text, start, end = find_between(tex_file, start, end)
    sliced_start = tex_file[:start]
    sliced_end = '\n' + tex_file[end:]
    return document_text, sliced_start, sliced_end


# def latex_repair(text: str, citation_path: str = '', return_preamble: bool = True) -> str:
#     """Cleans up tex files converted from pandoc.
#     """
#     start = '\\begin{document}'
#     end = '\\end{document}'
#     allow_proofs = False
#     if '\\emph{Proof.}' in text:
#         # proof_state = input('You have proofs. Would you like to '
#         #                    'enable proofs? (y/n, default y) ').lower()
#         allow_proofs = False  # if proof_state == 'n' else True
#     document_text, start, end = find_between(text, start, end)
#
#     # HYPERTARGET REMOVER
#     document_text_1 = hypertarget_eliminator(document_text)
#     # OVERSET REMOVER
#     document_text_2 = fix_vectors(document_text_1)
#     # ALIGNMENTS
#     document_text_3 = fix_vectors_again(document_text_2)
#     while True:
#         try:
#             document_text_3 = replace_align_region(document_text_3, allow_proofs)
#         except AssertionError:
#             break
#     document_text_4 = dollar_sign_equations(document_text_3)
#     document_text_4 = dbl.detect_include_graphics(document_text_4)
#     document_text_4 = prime_dealer(document_text_4)
#     if allow_proofs:
#         document_text_4 = dbl.qed(document_text_4)
#     has_bib_file = False
#     if citation_path != '' and len(citation_path) >= 4 and citation_path[-4:] == '.txt':
#         document_text_4 = dbl.do_citations(document_text_4, citation_path)
#         has_bib_file = True
#         document_text_4 = document_text_4 + '\\medskip\n\\printbibliography'
#
#     if return_preamble:
#         final_text = text[:start] + '\n' + document_text_4 + '\n' + text[end:]
#         return deal_with_preamble(final_text, has_bib_file)
#     else:
#         return document_text_4
#     # by this point, document_text_3 ends up being


def prime_dealer(text: str) -> str:
    """Fixes primes
    """
    replace_list = {"^{'}": "'", "^{''}": "''", "^{'''}": "'''"}
    for r in replace_list:
        text = text.replace(r, replace_list[r])
    return text


HARDCODED_TEXT = r"""\documentclass[fontsize=11pt]{article}  
\usepackage{amsmath, amssymb}
\usepackage{lmodern, iftex}  
\usepackage[utf8]{inputenc}  
\usepackage{array}
\usepackage{graphicx}
\setlength{\parindent}{0pt}
\setlength{\parskip}{6pt plus 2pt minus 1pt}
\usepackage{mathtools}
"""


def deal_with_preamble(text: str, has_bib_file: Union[bool, str] = False,
                       remove_default_font: bool = False, preamble_path: str = '',
                       erase_existing_preamble: bool = False, omit_section_numbering: bool = False) -> str:
    """Deal with the preamble
    text is ALL the text within the preamble.
    """
    # prestart = ''

    prestart = preamble_path
    if isinstance(has_bib_file, bool) and has_bib_file is True:
        assert False  # this is never supposed to run.
        # bib_file_name = input('What is your .bib file name? (Must include suffix .bib) ')
        # prestart = prestart + '\n\\addbibresource{' + bib_file_name + '}\n\n'
    elif isinstance(has_bib_file, str):  # type(has_bib_file) == type('string'):
        prestart = prestart + '\n\\bibliography{' + has_bib_file + '}\n\n'
    section_num_text = '\\setcounter{secnumdepth}{-\\maxdimen} % remove section numbering' if not \
        omit_section_numbering else '% remove section numberinging'
    pack_import_indicator = '\\usepackage{iftex}\n'
    if not erase_existing_preamble:
        processed_text = insert_after(text, pack_import_indicator, prestart)
        processed_text = processed_text.replace(section_num_text, '\n')
        if remove_default_font:
            processed_text = processed_text.replace(R'\usepackage{lmodern}', '')
    # to_remove = generate_text_to_remove()
    # for remove_instance in to_remove:
    #    processed_text = processed_text.replace(remove_instance, '', 1)
    else:
        processed_text = HARDCODED_TEXT + prestart + dbl.retain_author_info(text) + '\n\\begin{document}'
    # processed_text = dbl.date_today(processed_text)
    return processed_text


def insert_after(haystack: str, needle: str, new_text: str) -> str:
    """ Inserts 'newText' into 'haystack' right after 'needle'. """
    i = haystack.find(needle)
    return haystack[:i + len(needle)] + new_text + haystack[i + len(needle):]


def dollar_sign_equations(text: str) -> str:
    """Dollar sign equations.
    """
    text = text.replace('\\(', '$')
    text = text.replace('\\)', '$')
    text = text.replace('\\[', '$$')
    text = text.replace('\\]', '$$')
    return text


def find_between(s: str, first: str, last: str) -> tuple[str, int, int]:
    """Return extracted string between two substrings, start index, and end index

    """
    try:
        start = s.index(first) + len(first)
        end = s.index(last, start)
        return s[start:end], start, end
    except ValueError:
        logging.warning('Threw an assert False on find between')
        assert False, 'no ' + first + '.'


def remove_circ_brackets(txt: str) -> str:
    """

    >>> remove_circ_brackets('text<text>text(text)text(text]')
    'text[removed]text(text)text(text]'
    """
    return re.sub(r'\([^)]*\)', '[removed]', txt)


def fix_vectors(txt: str) -> str:
    """fix all vectors. run once.

    >>> expected_string = '\\textbf{u} + \\textbf{v}'
    >>> fv = fix_vectors('\\overset{⃑}{u} + \\overset{⃑}{v}')
    >>> fv == expected_string
    True

    """
    # arg1 = "overset{⃑}"
    arg1 = 'overset{âƒ‘}'
    replace1 = "mathbf"
    # txt = "\overset{45urrrrrr&R&}"
    # y = re.findall("^\\\\overset\{.*\}", txt)
    # print(y)
    x = re.sub("\\\\" + arg1, "\\\\" + replace1, txt)
    # print(x)
    return x


def fix_vectors_again(txt: str) -> str:
    """fix all vectors. run once.

    >>> expected_string = '\\textbf{u} + \\textbf{v}'
    >>> fv = fix_vectors('\\overset{⃑}{u} + \\overset{⃑}{v}')
    >>> fv == expected_string
    True

    """
    arg1 = "overset{⃑}"
    # arg1 = 'overset{âƒ‘}'
    replace1 = "mathbf"
    # txt = "\overset{45urrrrrr&R&}"
    # y = re.findall("^\\\\overset\{.*\}", txt)
    # print(y)
    x = re.sub("\\\\" + arg1, "\\\\" + replace1, txt)
    # print(x)
    return x


def hypertarget_eliminator(txt: str) -> str:
    """Eliminate hypertargets. run once.

    \\hypertarget{example-2-onto-but-not-one-to-one}{%\n\\subsubsection{Example 2: Onto but not\none-to-one}\\label{example-2-onto-but-not-one-to-one}}
    """
    # arg1 = "overset"
    # replace1 = "textbf"
    # txt = "\\hypertarget{example-2-onto-but-not-one-to-one}{%\n\\subsubsection{Example 2: Onto but
    # not\none-to-one}\\label{example-2-onto-but-not-one-to-one}}"
    # y = re.findall("^\\\\hypertarget\{.*\}", txt)
    z = re.sub("\\\\hypertarget{.*}{%", '', txt)
    # print(z)
    a = re.sub("\\\\label{.*}", '', z)
    # print(a)
    # x = re.sub("\\\\" + arg1, "\\\\" + replace1, txt)
    # x = re.sub("\(.*\)", "[remove]", x)
    # x = re.sub("d", "D", x)
    # print(x)
    return a


def replace_align_region(text: str, proofs: bool = False,
                         auto_align: bool = False, max_line_length: int = -1,
                         extra_info: Optional[dict] = None) -> tuple[str, bool]:
    """The entire process
    THIS ONE IS THE ONE WE ARE GOING TO USE
    loop until error occurs.

    Preconditions:
        - no weird things in verbatim environments that could mess with this
    """
    if extra_info is None:
        extra_info = {}
    temp_al = detect_align_region(text)
    if temp_al is not None:
        isolated, start_replace, end_replace = temp_al
    else:
        # logging.warning('returning back.')
        return text, True
    replace_with = process_align_region(isolated, auto_align, max_line_length, extra_info=extra_info)
    proof_line = ''
    # if proofs and R'\blacksquare' in replace_with:
    #     replace_with = replace_with.replace(R'\ \blacksquare', '')
    #     replace_with = replace_with.replace(R'\blacksquare', '')
    #     proof_line = '\n\\end{proof}\n'
    align_start = '\n\\begin{align*}\n'
    align_end = '\\end{align*}\n'
    end_result = text[
                 :start_replace - 1] + align_start + replace_with.strip() + '\n' + align_end + \
                 proof_line + text[
                              end_replace:]
    return end_result, False


TEST_EQN = r"""
This is the text before

\[{\begin{matrix}
9 + 10 = 21\ \#(4) \\
\end{matrix}
}{\begin{matrix}
420 + 69\#(4) \\
\end{matrix}
}{\begin{matrix}
71 + 22\#(3) \\
\end{matrix}
}{\begin{matrix}
83 + 42\#(9) \\
\end{matrix}
}\begin{matrix}
42 + 534r\#(67) \\
\end{matrix}\]

This is the text after
"""


TEST_EQN_AGAIN = r"""
you are not \\[{9 + 10 = 21}{420 + 69 = 222}\\] real
"""


def detect_align_region(text: str) -> Optional[tuple[str, int, int]]:
    """Return isolate string, start index, end index + 1 for the first align region found in text.
    Return nothing if no align region found.
    Detect an alignment region. An alignment region starts with \[ and ends with \],
    but only if { follows \[. It will only detect if that happens for the first time.
    Return None if we can't do that.

    >>> string = 'you are not \\[{9 + 10 = 21}{420 + 69 = 222}\\] real'
    >>> output = '\\[{9 + 10 = 21}{420 + 69 = 222}\\]'
    >>> detect_align_region(string) == output
    True


    """
    # text = 'aaaa(bb()()ccc)dd'
    # istart = []  # stack of indices of opening parentheses
    # d = {}

    inside = False  # True if \[ has passed and not closed
    brace_layer = 0
    last_opening_region = 0
    prev_is_backslash = False
    prev_is_opening_bracket = False  # if the prev is \[ - the [
    finished_region = [-1, -1]
    found = False
    special_region_info = None
    for i, c in enumerate(text):  # the massive for loop
        assert not (prev_is_opening_bracket and prev_is_backslash), '[ and \\ at the same time'

        if prev_is_opening_bracket and c != '{':
            inside = False
            prev_is_opening_bracket = False
        else:
            prev_is_opening_bracket = False  # if \[{
        # It's not an alignment region if all of the conditions are met:
        # Inside is True
        # brace_layer is 0
        # the char we are focusing at is not {, }, or \n, and
        # \{ and \} do not count as braces
        if inside:
            if c == '\\':
                pass
            elif prev_is_backslash and (c == '[' or c == ']'):
                pass
            elif not prev_is_backslash and (c == '{' or c == '}'):  # bare { or }
                if c == '{':
                    brace_layer += 1
                elif c == '}':
                    brace_layer -= 1
                else:
                    assert False  # we will NEVER reach there
            elif prev_is_backslash and (c in {'[', ']'}):  # bare \[ or \]
                pass  # prevents the branch below from happening. We would've ended stuff here.
            elif c == '\n':
                pass
            else:
                if brace_layer <= 0:  # this is a very special case.
                    # if that is the case, skip to the next \\]
                    # then check everything between c and before \\], stripped
                    ti_c = text.find('\\]', i)
                    assert ti_c != -1
                    last_part = text[i - 1:ti_c].strip()
                    state = dbl.valid_matrix(last_part)
                    if not state:  # this happens the most often
                        inside = False  # this is rarer.
                    else:
                        finished_region[0] = last_opening_region
                        finished_region[1] = ti_c + 2
                        found = True
                        special_region_info = [i - 1, ti_c]  # positions to add { and }, similar to list.insert()
                        break

        if prev_is_backslash:
            if c == '[':
                inside = True
                last_opening_region = i - 1
                prev_is_opening_bracket = True
            if c == ']' and inside:
                # print('captured a region')
                finished_region[0] = last_opening_region
                finished_region[1] = i + 1
                assert finished_region[0] <= finished_region[1], 'future sight'
                found = True
                break
        prev_is_backslash = (c == '\\')  # if c is \\
        # if prev_is_backslash:
        #    print(prev_is_backslash)
    # if we ever find one
    if found:
        if special_region_info is None:
            captured_region = text[finished_region[0]:finished_region[1]]
            print(captured_region)
        else:
            captured_region = text[finished_region[0]:special_region_info[0]] + '{' + \
                              text[special_region_info[0]:special_region_info[1]] + '}' + \
                              text[special_region_info[1]:finished_region[1]]
            print(captured_region)

        return captured_region, finished_region[0], finished_region[1]
    else:
        # print('ran out of alignment regions to check')
        return None


def process_align_region(txt: str, auto_align: bool = False, max_line_len: int = -1,
                         extra_info: Optional[dict] = None) -> str:
    """Repairs all multiline equation environments.

    Preconditions:
        - txt is the text inside \[ and \]
        - txt must start with { and end with }
        - this must run AFTER the overset eliminator is conducted
    >>> process_align_region('{the reason why}{I have no idea}{please help}')
    """
    if extra_info is None:
        extra_info = {}
    # max_line_len = 40
    # text_so_far = txt
    # uni_seperator = 'Ↄ'
    txt = txt.replace('\n', '')  # may make equations long.
    separator_points = bracket_region_outer(txt, '{', '}')
    # it is slicing time
    lines_so_far = []
    for start in separator_points:
        true_start = start + 1  # the char after {
        true_end = separator_points[start]  # the char before }
        lines_so_far.append(txt[true_start: true_end])
    if max_line_len >= 1:
        lines_so_far_1 = []
        for line in lines_so_far:
            edited_line = dbl.split_equation(line, max_line_len, True)
            if edited_line is None:
                edited_line = [line]
            else:
                pass  # logging.warning("We did split something")
            for lin in edited_line:
                lines_so_far_1.append(lin)
        if len(lines_so_far_1) != len(lines_so_far):
            pass
    else:
        lines_so_far_1 = lines_so_far
    lines_so_far_2 = [align_expression(a_line, auto_align, extra_info=extra_info) for a_line in lines_so_far_1]
    # print(lines_so_far)
    output = ' \\\\\n'.join(lines_so_far_2)
    return output


TEST_MATRIX = r"""
\[{\begin{matrix}
9 + 10\# 5 \\
\end{matrix}
}{\begin{matrix}
9 + 10\# 6 \\
\end{matrix}
}{\begin{matrix}
9 + 10\# 7 \\
\end{matrix}
}{\begin{matrix}
9 + 10\ \#\text{this\ is\ the\ final\ comment} \\
\end{matrix}
}\]
"""


def check_start_matrix(text: str) -> tuple[Optional[str], Optional[str]]:
    """Check if text starts and ends with matrix declarations.

    This works perfectly; however, if we use alignment environments, typically the last one will be a bit broken.
    """
    # logging.warning(text)
    text = text.strip()  # strip the text first
    bm = R'\begin{matrix}'
    em = R'\end{matrix}'
    starting_matrix_location = text.find(bm)
    # conditions: above is 0
    if starting_matrix_location != 0:
        return None, None
    ending_matrix_location = text.rfind(em)
    required_ending_location = len(text) - len(em)
    # conditions: ending matrix ends where it is supposed to end
    if ending_matrix_location != required_ending_location:
        return None, None
    # Matrix conditions should be met by this point.
    hashtag = R'\#'
    if R'\#' not in text:
        return None, None
    # intl passing location. For now, let's assume that this is only where # appears.
    ti_temp = text.rfind(hashtag)  # the index of the last hashtag, starting at the backslash
    if dbl.any_layer(text, ti_temp, R'\left', R'\right') != 0:
        return None, None
    if dbl.any_layer(text, ti_temp, R'\begin', R'\end') != 1:
        return None, None
    # if dbl.any_layer(text, ti_temp, bm, em) != 1:
    #     return None, None
    start = ti_temp + len(hashtag)
    end = text.find(R'\\', start)
    # we assume we didn't define any matrices in our comment
    comment = text[start:end].strip()
    b_start = len(bm)
    # ti_temp is also where the hashtag point starts, so everything before it is the contents
    equation_contents = text[b_start:ti_temp].strip()
    return equation_contents, comment


def align_expression(text: str, auto_align: bool = False, extra_info: Optional[dict] = None) -> str:
    """Adds an & when applicable. If not, add it at the start.

    Preconditions:
        - text is a singular-line equation within an alignment environment

    Extra info:
        - comment_type: align or shortintertext

    >>> text = 'y = x + 2'
    >>> align_expression(text, True)
    'y &= x + 2'
    >>> text = 'y {>} x + 2'
    >>> align_expression(text, True)
    '&y {>} x + 2'
    >>> text = 'y {>} < x + 2'
    >>> align_expression(text, True)
    'y {>} &< x + 2'
    """
    if extra_info is None:
        # extra_info = {}
        raise ValueError  # THIS NEVER RUNS!!!

    # extra_info = {'comment_type': 'shortintertext'}
    cur_mode = extra_info.get('comment_type', '')
    assert cur_mode in {'', 'align', 'shortintertext'}
    si_text = ''
    temp_comment = ''
    if cur_mode not in {'align', 'shortintertext'}:
        pass
    else:
        temp_text, temp_comment = check_start_matrix(text)
        if temp_text is not None:
            # temp_comment = dbl.equation_to_regular_text(temp_comment)  # nope, won't work.
            logging.info('looks like we have a comment')
            text = temp_text
            si_text = R'\shortintertext{' + temp_comment + '}' + '\n'
        else:
            temp_comment = ''

    if not auto_align:
        return '& ' + text
    else:
        hierarchy = [
            {'='},
            {'<', '>', '\\leq', '\\geq', '\\approx'},
            {'\\subset', '\\subseteq', '\\not\\subset'},
            {'\\neq'}
        ]
        for series in hierarchy:
            occurrences = set()
            for symbol in series:
                ind = text.find(symbol)
                layer = dbl.bracket_layers(text, ind)
                if ind != -1 and layer == 0:
                    occurrences.add(ind)
            if occurrences != set():
                min_ind = min(occurrences)
                final_string = text[:min_ind] + '&' + text[min_ind:]
                if cur_mode == 'shortintertext':
                    final_string = si_text + final_string
                elif cur_mode == 'align' and temp_comment != '':
                    final_string = final_string + ' && ' + temp_comment
                return final_string
        to_return = '&' + text
        if cur_mode == 'shortintertext':
            to_return = si_text + '&' + text
        elif cur_mode == 'align' and temp_comment != '':
            to_return = to_return + ' && ' + temp_comment
        return to_return


def bracket_region(text: str, open: str, close: str) -> dict:
    """Bracket region.
    \{ x+y \} means \\{ x+y \\}
    Preconditions:
        - len(open) = 1 and len(close) = 1
        - open != '\\' and close != '\\'

    >>> bracket_region('abc\bdefghi', 'b', 'h')

    """
    # text = 'aaaa(bb()()ccc)dd'
    istart = []  # stack of indices of opening parentheses
    d = {}

    # if the previous char is a \\, then don't check the next one. \\ counts as 1 char
    backslash_state = False
    for i, c in enumerate(text):
        if c == '\\':
            backslash_state = True
        elif backslash_state:
            backslash_state = False
        if c == open:
            if not backslash_state:  # if the previous char isn't \\
                istart.append(i)
            elif c != '\\':  # turn it back to false, UNLESS c == \\
                backslash_state = False
        if c == close:
            if not backslash_state:
                try:
                    d[istart.pop()] = i
                except IndexError:
                    print('Too many closing parentheses')
            elif c != '\\':
                backslash_state = False
    if istart:  # check if stack is empty afterwards
        print('Too many opening parentheses')
    return d


def bracket_region_outer(text: str, open: str, close: str):
    """Bracket region. Outer only. Skips backslash cases.
    \{ x+y \} means \\{ x+y \\}
    Preconditions:
        - len(open) = 1 and len(close) = 1
        - open != '\\' and close != '\\'

    >>> bracket_region('abc\bdefghi', 'b', 'h')

    """
    # text = 'aaaa(bb()()ccc)dd'
    istart = []  # stack of indices of opening parentheses
    d = {}

    # if the previous char is a \\, then don't check the next one. \\ counts as 1 char
    backslash_state = False
    for i, c in enumerate(text):
        if c == '\\':
            backslash_state = True
        elif backslash_state:
            backslash_state = False
        if c == open:
            if not backslash_state:  # if the previous char isn't \\
                istart.append(i)
            elif c != '\\':  # turn it back to false, UNLESS c == \\
                backslash_state = False
        if c == close:
            if not backslash_state:
                try:
                    # prior_istart_len = len(istart)
                    kc = istart.pop()
                    if len(istart) == 0:  # only when capturing outermost brackets
                        d[kc] = i
                except IndexError:
                    print('Too many closing parentheses')
            elif c != '\\':
                backslash_state = False
    if istart:  # check if stack is empty afterwards
        print('Too many opening parentheses')
    return d


# def remove_enumerated_headers(txt: str) -> str:
#    arg1 = '\\def\\labelenumi{\\arabic{enumi}.}'
#    x = re.sub(arg1, '', txt)
#    return x


# def list_each_char(txt: str) -> list[str]:
#    return [x for x in txt]
def file_name_file_path(name: str) -> str:
    """Please stop
    """
    name_list = name.split('\\')
    return name_list[-1]


# def process_main(mode: int, directory_path: Optional[str]) -> None:
#     """Single document branch
#     """
#     # the_file_name = ' '.join(sys.argv[1:])
#     if directory_path is not None:
#         the_file_name = directory_path
#     else:
#         the_file_name = input('type the name of the docx file you want to work with: ')
#     if mode == 2:
#         citation_file = easygui.fileopenbox(msg='Select the *.txt citation file you want to open:',
#                                             filetypes=["*.txt"])
#     else:
#         citation_file = ''
#
#     if ' ' in the_file_name:
#         print('Your file has a space in it or a folder the file it is in has.')
#     # if len(the_file_name) < 5 or not (len(the_file_name) >= 5 and
#     #                                  the_file_name[len(the_file_name) - 5:] == '.docx'):
#     #    # case where cmd input does not end with docx, add docx
#     #    the_file_name = the_file_name + '.docx'
#     the_file_name = file_name_file_path(directory_path)
#     output_name = 'temp_latex_processor_output_1.tex'
#     output_tex_filename = the_file_name[:len(the_file_name) - 5] + '-latex_processed.tex'
#     output_tex_pdf = the_file_name[:len(the_file_name) - 5] + '-latex_processed.pdf'
#     media_path = '--extract-media=images_' + the_file_name[:len(the_file_name) - 5]
#     command_string = 'cmd /c "pandoc ' + media_path + ' -s ' + directory_path + ' -o ' + output_name
#     os.system(command_string)
#     time.sleep(0.2)
#     if mode == 0 or mode == 2:
#         work_with_file(output_name, output_tex_filename, citation_file)
#         # time.sleep(0.2)
#     if mode == 1:
#         second_file_name = easygui.fileopenbox(msg='Select the *.tex file you want to open',
#                                                filetypes=["*.tex"])
#         work_with_multiple_files(output_name, second_file_name, output_tex_filename)
#     # now we compile
#     command_string_2 = 'cmd /c "pdflatex ' + output_tex_filename
#     command_string_3 = 'cmd /c "' + output_tex_pdf
#     # os.system(command_string_2)
#     os.system(command_string_2)
#     os.system(command_string_3)
#     print('Finished!')
