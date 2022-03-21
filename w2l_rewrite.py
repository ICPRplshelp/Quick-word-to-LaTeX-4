"""A rewrite of the primary w2l processor.
"""
import logging
import time
from dataclasses import dataclass, fields
from typing import Optional, Any, Union
import json
import os

# import easygui
from tkinter.filedialog import askopenfile

import w2l_primary as w2l
import double_processor as dbl

TEMP_TEX_FILENAME = 'temp.tex'
REPLAC = {'α': r'\alpha', 'β': r'\beta', 'γ': r'\gamma', 'δ': r'\delta', 'ϵ': r'\epsilon',
          'λ': r'\lambda', 'θ': r'\theta', 'ϑ': r'vartheta', 'π': r'\pi', 'Ω': r'\Omega', 'ε': r'\varepsilon',
          'Λ': r'\Lambda', 'Δ': r'\Delta', 'μ': r'\mu', 'ν': r'\nu', 'ξ': r'\xi', 'ρ': r'\rho'}
# REPLAC = {'α'}
ALLOWED_LATEX_COMPILERS = {'pdflatex', 'xelatex'}


def open_file(file: str) -> str:
    """Return file contents of any plain text file in the directory file.
    """
    with open(file, encoding='UTF-8') as f:
        file_text = f.read()
    return file_text


def write_file(text: str, filename: str) -> None:
    """Write file with given name.
    """
    with open(filename, 'w', encoding='UTF-8') as f:
        f.write(text)


def check_suffix(dir_path: str, suffix: str) -> bool:
    """Return True if the file path has the suffix.
    The suffix may NOT include the leading dot.

    >>> check_suffix('filename.txt','txt')
    True
    >>> check_suffix('filename.docx','txt')
    False
    >>> check_suffix('filename.docx','docx')
    True
    """
    return len(dir_path) >= len(suffix) + 1 and dir_path[-len(suffix):] == suffix


class InvalidFileTypeError(Exception):
    """Exception raised when selecting a file that does not end with
    a filetype the program specifies."""

    def __str__(self) -> str:
        """Return a string representation of this error."""
        return 'invalid file type.'


class SpaceError(Exception):
    """Exception raised when selecting a file where the directory
    path to it has a space character in it."""

    def __str__(self) -> str:
        """Return a string representation of this error."""
        return 'file directory has a space character in it.'


@dataclass
class Preferences:
    """A custom data type that represents the preferences for a word document.
    All preferences are set to false by default.

    Instance Attributes:
        - allow_proofs: this is still very broken, so keep it false.
        - allow_citations
        - allow_no_longtable
        - allow_alignments
        - exclude_preamble
        - citation_mode: the citation mode.
    """
    preamble_path: Union[str, list[str]] = 'preamble_0.txt'  # path of the preamble.
    allow_proofs: bool = False  # Enable the proofs module.
    allow_citations: bool = False  # Enable the citation module.
    allow_no_longtable: bool = False  # convert all long tables to regular tables. Tables must be plain to work
    allow_alignments: bool = False  # align equations.
    exclude_preamble: bool = False  # prevent the preamble from being included with the document. Blocks pdf exports
    citation_mode: str = 'apa2'  # changes how citations are typed. Should always be set to apa2.
    disallow_figures: bool = False  # prevent images and tables from being figured.
    forbid_images: bool = False  # prevent any images from appearing.
    disable_repair: bool = False  # set to True if you just want this to be a latex compiler and nothing else
    hypertarget_remover: bool = True  # sections now look like real sections with this
    fix_vectors: bool = True  # make vectors work
    dollar_sign_equations: bool = True  # equation wrappers are now $ instead of \[ and \(
    center_images: bool = True  # disabling this prevents figures
    fix_prime_symbols: bool = True  # prevents prime symbols from looking ugly
    allow_environments: bool = False  # enable the environment module.
    prevent_pdf_exports: bool = False  # prevents compiling of the tex file this program generates
    fix_derivatives: bool = True  # prevents dy/dx from looking weird
    replace_font: bool = False  # if True, you can change the font using preamble_0.txt
    fix_unicode: bool = False  # prevents backslash text weirdness in equations
    autodetect_align_symbols: bool = True  # if False, &s are always put at the start for each align region
    pdf_engine: str = 'xelatex'  # what tex engine is used to combine
    max_line_length: int = 110  # max. relative length for equations. set this to a negative number to disable
    max_line_align: bool = True  # whether to enforce this in preexisting alignment envs
    fix_texttt: bool = False  # whether to fix every quirk with inline code.
    combine_aligns: bool = True  # whether to combine separate align sections if nothing is between
    special_proofs: bool = False  # whether proofs use the tcolorbox environment
    start_of_doc_text: str = ''  # text to append at the start right after the document begins
    verbatim_lang: str = ''  # the language of every code block in the document. Blank for don't even try.

    replacement_marker: str = 'TODO'  # the replacement marker in when using replacement mode

    table_of_contents: bool = False  # whether to include a table of contents.
    header_level: int = 0  # headers to shift by. 0 means no, 1 means L1 -> L2, -1 means L2 -> L1
    export_file_name_suffix: str = 'LTP'  # name of the exported tex and pdf file; no suffix
    media_folder_name: str = 'TEXIMAGE_'  # name of the image folder if any images are present

    override_title: bool = True  # override the title in the replacement mode by the title in the Word doc
    override_author: bool = True  # override the author in the replacement mode by the author in the Word doc
    # to define an author in a Word doc it must be defined in the style "author".
    erase_pandoc_preamble: bool = False  # Allows erasing of the original Pandoc preamble. Some other modules must
    # be active for this to work.

    replacement_mode: bool = False  # whether replacement mode is on or off.
    environments: Optional[dict] = None  # information relating to environments.

    eqn_comment_mode: str = ''  # how comments in equations should be handled.
    remove_spaces_from_eqns: bool = True  # whether long spaces should be removed from equations.

    no_secnum: bool = True  # omit section numbering


DEFAULT_PREF = Preferences('preamble_0.txt', False, False, False, False, False)
CITE_PREF = Preferences('preamble_0.txt', False, True, False, False, False)


def process_permissive_list(lst: list[tuple[str, bool]]) -> list[str]:
    """Format:
    [(str, cond),] and so on.
    """
    return [x[0] for x in lst if x[1]]


class WordFile:
    """A custom data type that represents data for a word document, that is to be
    converted.

    Instance attributes:
        - word_file_path: the path of the word file.
        - word_file_nosuffix: name of the word file.
        - preferences: the preferences of this word file.
        - output_path: the final output path of this word file.
        - text: the text contents of this word file.
    """
    word_file_path: str
    word_file_nosuffix: str
    preferences: Preferences
    output_path: str
    text: str  # our latex converted stuff
    citation_path: str  # must ALWAYS be a valid .txt file
    bib_path: Optional[str]  # not a directory; just the name of the bib file
    raw_text: str
    original_tex: bool
    erase_pandoc_preamble: bool  # erase the pandoc preamble.

    _temp_tex_file: str
    _disallow_pdf: bool

    def __init__(self, word_file_path: str, preferences: Preferences = DEFAULT_PREF) -> None:
        """Initialize a new WordFile object.

        Raise an InvalidFileTypeError if word_file_path is not a Microsoft word file.
        Raise a SpaceError if word_file_path has a space character in it.
        """
        if word_file_path[-5:] != '.docx' and word_file_path[-4:] != '.tex':
            raise InvalidFileTypeError
        if ' ' in word_file_path:
            pass  # raise SpaceError
        self.word_file_path = word_file_path
        starter_name_directory_index = self.word_file_path.rfind('\\') + 1
        if starter_name_directory_index == -1:
            starter_name_directory_index = 0
        self.word_file_nosuffix = word_file_path[starter_name_directory_index:-5]
        self.preferences = preferences
        self._temp_tex_file = TEMP_TEX_FILENAME
        export_suffix = self.preferences.export_file_name_suffix + '.tex'
        self.output_path = self.word_file_nosuffix + export_suffix
        if word_file_path[-5:] == '.docx':
            self.text = self.open_word_file()
            self.original_tex = False
            self._disallow_pdf = False
        else:
            self.text = open_file(word_file_path)
            self.original_tex = True
            self._disallow_pdf = True
        self.raw_text = self.text
        self.citation_path = 'placeholder'
        self.bib_path = ''
        self._recalculate_erase_preamble()
        if preferences.allow_citations:
            # self.citation_path = easygui.fileopenbox(
            #     msg='Select the *.txt citation file you want to open:',
            #     filetypes=["*.txt"])
            print('Opening the bib document file open box. If noting opens, consider re-running this program.')
            file_info = askopenfile(mode='r', title='Open the bib file you want to combine',
                                    filetypes=[('Bib Files', '*.bib')])
            self.bib_path = file_info.name.replace("/", "\\") if file_info is not None else None
            if self.bib_path is None:
                print('You did not specify a bib path, so we\'re assuming you\'re not citing anything')
        if self.preferences.prevent_pdf_exports:
            self._disallow_pdf = True

    def _recalculate_erase_preamble(self) -> None:
        """Determine whether the pandoc preamble should be removed based on preferences."""
        self.erase_pandoc_preamble = all([self.preferences.allow_no_longtable, self.preferences.erase_pandoc_preamble])

    def sequence(self) -> None:
        """Completely process and export the word file to tex."""
        if self.preferences.exclude_preamble:
            self.preferences._disallow_pdf = True
        if not self.preferences.disable_repair:  # if disable repair is FALSE
            self.latex_repair()
        self.export()

    def open_word_file(self) -> str:
        """Return tex code of WordFile."""
        media_path = '--extract-media=' + self.preferences.media_folder_name + self.word_file_nosuffix
        dquote = '"'
        # toc = '--toc'
        # these are writer options
        # tuple index 0 is the string; tuple index 1 is the condition
        filter_list = [
            ('-s', True),
            (f'--shift-heading-level-by={self.preferences.header_level}', self.preferences.header_level != 0),
            ('--toc', self.preferences.table_of_contents)
        ]
        # if self.preferences.table_of_contents:
        #     filter_list.append('--toc')

        filters_1 = ' '.join(process_permissive_list(filter_list))

        # command_string = 'cmd /c "pandoc ' + media_path + ' -s ' + \
        #                 self.word_file_path + ' -o ' + self._temp_tex_file

        # self.preferences.pdf_engine

        pdf_engine_str = '--pdf-engine=xelatex '  # f'--pdf-engine={self.preferences.pdf_engine} ' if self.preferences.pdf_engine != 'pdflatex' else ''
        command_string = f'pandoc {dquote}{media_path}{dquote} {filters_1} {dquote}{self.word_file_path}{dquote} {pdf_engine_str}-o {self._temp_tex_file}'
        os.system(command_string)
        return open_file(self._temp_tex_file)

    def latex_repair(self) -> None:
        """Repair generated latex file.
        """
        text = self.text
        start = '\\begin{document}'
        end = '\\end{document}'
        text, start, end = w2l.find_between(text, start, end)
        if self.preferences.hypertarget_remover:
            text = w2l.hypertarget_eliminator(text)
        if self.preferences.fix_vectors:
            text = w2l.fix_vectors(text)
            text = w2l.fix_vectors_again(text)
        # if True:
        #    text = dbl.longtable_backslash_add_full(text)

        eqn_comment = {'comment_type': self.preferences.eqn_comment_mode}
        if self.preferences.remove_spaces_from_eqns:
            text = dbl.bad_backslash_replacer(text)
            text = dbl.bad_backslash_replacer(text, '\\(', '\\)')
        if self.preferences.allow_alignments:  # alignments must always run first
            while True:
                max_line = self.preferences.max_line_length if self.preferences.max_line_align else -1
                text, stat = w2l.replace_align_region(text, self.preferences.allow_proofs,
                                                      self.preferences.autodetect_align_symbols,
                                                      max_line, extra_info=eqn_comment)
                # print('stat')
                if stat:
                    break
        if self.preferences.max_line_length >= 1:
            text = dbl.split_all_equations(text, self.preferences.max_line_length)
            while True:
                text, stat = w2l.replace_align_region(text, self.preferences.allow_proofs,
                                                      self.preferences.autodetect_align_symbols)
                if stat:
                    break
        if self.original_tex:
            text, self._disallow_pdf = dbl.truncate_path(text, self._disallow_pdf)
        if self.preferences.forbid_images:
            text = dbl.remove_images(text)
            logging.warning('Removing images')
        elif self.preferences.center_images:
            text = dbl.detect_include_graphics(text, self.preferences.disallow_figures)
        if self.preferences.fix_prime_symbols:
            text = w2l.prime_dealer(text)
        if self.preferences.fix_derivatives:
            text = dbl.dy_fixer(text)
        if self.preferences.allow_proofs:
            text = dbl.qed(text, self.preferences.special_proofs)
        if self.preferences.allow_environments and self.preferences.environments is not None:
            text = dbl.work_with_environments(text, self.preferences.environments)
        if self.preferences.allow_no_longtable:
            text = dbl.eliminate_all_longtables(text, self.preferences.disallow_figures)  # EPIC FAIL!!!
        if self.preferences.dollar_sign_equations:
            text = w2l.dollar_sign_equations(text)
        if self.preferences.fix_unicode:
            # print(text)
            text = dbl.text_bound_fixer(text, REPLAC)
        if self.preferences.fix_texttt:
            text = dbl.fix_all_textt(text)
        if self.preferences.combine_aligns:
            text = dbl.combine_environments(text, 'align*')
        if self.preferences.verbatim_lang != '':
            text = dbl.verbatim_to_listing(text, self.preferences.verbatim_lang)
        # text = text.replace('…', '...')  # only occurs in verbatim envs
        if self.preferences.allow_citations and self.citation_path \
                is not None and self.bib_path is not None:
            bib_data = open_file(self.bib_path)
            text = dbl.do_citations(text, bib_data, self.preferences.citation_mode)
            text = text + '\\medskip\n\\printbibliography'
        if not self.preferences.exclude_preamble:  # if preamble is included
            self.text = w2l.deal_with_preamble(self.raw_text[:start],
                                               remove_default_font=self.preferences.replace_font,
                                               preamble_path=self.preferences.preamble_path,
                                               erase_existing_preamble=self.erase_pandoc_preamble,
                                               omit_section_numbering=self.preferences.no_secnum) \
                        + '\n' + self.preferences.start_of_doc_text + '\n' + text + '\n' + \
                        self.raw_text[end:]
        else:
            self.text = text
        # else do nothing

    def export(self) -> None:
        """Export everything in self.text
        """
        # try:
        #     os.mkdir('export')
        # except FileExistsError:
        #     pass
        # self.output_path = 'export\\' + self.output_path
        latex_engine = self.preferences.pdf_engine
        if latex_engine not in ALLOWED_LATEX_COMPILERS:
            latex_engine = 'xelatex'
        dq = '"'
        write_file(self.text, self.output_path)
        if not self._disallow_pdf:
            command_string_2 = latex_engine + ' "' + self.output_path + '"'
            command_string_3 = '"' + self.output_path[:-4] + '.pdf' '"'
            # os.system(command_string_2)
            os.system(command_string_2)  # compile the pdf
            # if citations are on OR (figures are on AND center images / long table eliminators are on)
            if (self.preferences.allow_citations and self.bib_path is not None) or (
                    not self.preferences.disallow_figures and (
                    self.preferences.allow_no_longtable or self.preferences.center_images)):
                os.system(command_string_2)  # compile it again
            os.system(command_string_3)
        else:
            command_string_4 = f'{dq}self.output_path{dq}'
            print('You inputted a .tex file that contains images, so we aren\'t compiling')
            os.system(command_string_4)
        print('Finished!')


class WordFileCombo(WordFile):
    """Used for LaTeX combos.
    """
    corresponding_tex_file: str
    alt_text: str
    author: Optional[str]
    doc_title: Optional[str]

    def __init__(self, word_file_path: str, preferences: Preferences = DEFAULT_PREF) -> None:
        super().__init__(word_file_path, preferences)
        print('Opening the replacement tex file open box. If nothing opens, consider re-running this program.')
        file_info = askopenfile(mode='r', title='Open the word file you want to combine',
                                filetypes=[('Tex Files', '*.tex')])
        self.corresponding_tex_file = file_info.name.replace("/", "\\") if file_info is not None else None
        # self.corresponding_tex_file = easygui.fileopenbox(msg='Select the corresponding *.tex '
        #                                                       'file you'
        #                                                       'want to open.', filetypes=["*.tex"],
        #                                                   default='*.tex')
        self.preferences.exclude_preamble = True  # the preamble is always excluded here
        self.alt_text = ''
        self._disallow_pdf = False  # PDFs will always compile

        self.author = None
        self.doc_title = None

    def sequence(self) -> None:
        """Process
        """
        # file_text_1 = self.text
        self.alt_text = open_file(self.corresponding_tex_file)
        try:
            self.author = dbl.find_author(self.text, 'author')
        except ValueError:
            pass
        try:
            self.doc_title = dbl.find_author(self.text, 'title')
        except ValueError:
            pass
        logging.warning(f'author name is {self.author} and title name is {self.doc_title}')

        self.latex_repair()
        # self.text = dbl.strip_regular_sections(self.text)
        new_file_text_2, new_file_start, new_file_end = w2l.document_extract(self.alt_text)
        preamble_mode = dbl.deduce_preamble_mode(new_file_text_2)
        new_file_start = dbl.insert_in_preamble(new_file_start, preamble_mode)
        new_file_text_3 = dbl.many_instances(self.text, new_file_text_2, self.preferences.replacement_marker)
        new_file_text_4 = new_file_start + new_file_text_3 + new_file_end
        if self.preferences.override_author and isinstance(self.author, str):
            new_file_text_4 = dbl.swap_author(new_file_text_4, self.author, 'author')
        if self.preferences.override_title and isinstance(self.doc_title, str):
            new_file_text_4 = dbl.swap_author(new_file_text_4, self.doc_title, 'title')
        self.text = new_file_text_4
        print(new_file_text_4)
        self.export()


def check_config(json_path: str) -> tuple[Preferences, bool]:
    """Return Preferences based on configurations.
    """
    with open(json_path) as json_file:
        data = json.load(json_file)
    try:
        # temp_data = dict(data)
        field_names = set(f.name for f in fields(Preferences))
        cur_prefs = Preferences(**{k: v for k, v in data.items() if k in field_names})
        # this works perfectly
    except KeyError:
        cur_prefs = Preferences()
        logging.warning('The config file is broken, so defaulting to all defaults.')
    return cur_prefs, data["replacement_mode"]


def main() -> None:
    """Run this file.
    """
    try:
        print('Opening the word document file open box. If noting opens, consider re-running this program.')
        main_file_mfn = askopenfile(mode='r', title='Open the word file you want to convert',
                                    filetypes=[('Word Files', '*.docx'), ('Tex Files', '*.tex')])
        path_mfn = main_file_mfn.name.replace("/", "\\") if main_file_mfn is not None else None
        if path_mfn is None:
            print('You didn\'t select anything')
            exit()
        print(path_mfn)
        json_dir_mfn = open_file('mode.txt')
        prefs_mfn, replacement_mode_mfn = check_config(json_dir_mfn.strip())
        if replacement_mode_mfn:
            print('We are in replacement mode')
            word_file_mfn = WordFileCombo(path_mfn, prefs_mfn)
        else:
            word_file_mfn = WordFile(path_mfn, prefs_mfn)
        word_file_mfn.sequence()
    finally:
        print('Ending program. If a PDF was never compiled, it means something\'s wrong with'
              ' the file you\'ve chosen.')
        time.sleep(2)


if __name__ == '__main__':

    try:
        print('Opening the word document file open box. If noting opens, consider re-running this program.')
        main_file = askopenfile(mode='r', title='Open the word file you want to convert',
                                filetypes=[('Word Files', '*.docx'), ('Tex Files', '*.tex')])
        path = main_file.name.replace("/", "\\") if main_file is not None else None
        if path is None:
            print('You didn\'t select anything')
            exit()
        print(path)
        json_dir = open_file('mode.txt')
        prefs, replacement_mode = check_config(json_dir.strip())
        if replacement_mode:
            print('We are in replacement mode')
            word_file = WordFileCombo(path, prefs)
        else:
            word_file = WordFile(path, prefs)
        word_file.sequence()
    finally:
        print('Ending program. If a PDF was never compiled, it means something\'s wrong with'
              ' the file you\'ve chosen.')
        time.sleep(2)
