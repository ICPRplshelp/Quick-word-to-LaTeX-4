"""This file chooses which modules to include when converting files.
"""
import json
import logging
import os
import platform
import time
from dataclasses import dataclass, fields, asdict

from tkinter.filedialog import askopenfile
from typing import Optional, Union, Any
import subprocess

from helper_files import helpers as dbl, alignments as w2l
import cleanup

has_pygments = True

try:
    pass
    # import pygments
except ModuleNotFoundError:
    logging.warning('pygments isn\'t installed, meaning'
                    ' code blocks will not be highlighted,'
                    ' and some text from the preamble will be'
                    ' omitted.')
    has_pygments = False

USE_SUBPROCESSES = True

TEMP_TEX_FILENAME = 'temp.tex'
REPLAC = {'α': R'\alpha', 'β': R'\beta', 'γ': R'\gamma', 'δ': R'\delta', 'ϵ': R'\epsilon',
          'λ': R'\lambda', 'θ': R'\theta', 'ϑ': R'vartheta', 'π': R'\pi', 'Ω': R'\Omega', 'ε': R'\varepsilon',
          'Λ': R'\Lambda', 'Δ': R'\Delta', 'μ': R'\mu', 'ν': R'\nu', 'ξ': R'\xi', 'ρ': R'\rho'}
# REPLAC = {'α'}
ALLOWED_LATEX_COMPILERS = {'pdflatex', 'xelatex', 'luatex'}
FOLDER_TO_RUN_IN = 'export'  # the folder to run it.
FOLDER_TO_RUN_IN_SLASH = FOLDER_TO_RUN_IN + '\\'


def open_file(file: str, allow_exceptions: bool = False) -> str:
    """Return file contents of any plain text file in the directory file.
    """
    if not allow_exceptions:
        with open(file, encoding='UTF-8') as f:
            file_text = f.read()
        return file_text
    else:
        try:
            with open(file, encoding='UTF-8') as f:
                file_text = f.read()
            return file_text
        except FileNotFoundError:
            return ''


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


class AttemptedFilePromptError(Exception):
    """Exception raised when a file dialogue would open up
    when that is not allowed to happen."""


class WordFileNotSpecified(Exception):
    """Exception raised when a Word file is not
    specified when it really has to."""


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
    preamble_path: Union[str, list[str]] = 'preamble.txt'  # path of the preamble.
    allow_proofs: bool = True  # Enable the proofs module.
    allow_citations: bool = True  # Enable the citation module.
    allow_no_longtable: bool = False  # convert all long tables to regular tables. Tables must be plain to work
    allow_alignments: bool = True  # align equations.
    exclude_preamble: bool = False  # prevent the preamble from being included with the document. Blocks pdf exports
    citation_mode: str = 'apa2'  # changes how citations are typed. Should always be set to apa2.
    disallow_figures: bool = False  # prevent images and tables from being figured.
    forbid_images: bool = False  # prevent any images from appearing.
    disable_repair: bool = False  # set to True if you just want this to be a latex compiler and nothing else
    hypertarget_remover: bool = True  # sections now look like real sections with this. Also prevents
    # some modules from breaking.
    fix_vectors: bool = True  # make vectors work
    dollar_sign_equations: bool = False  # equation wrappers are now $ instead of \[ and \(
    center_images: bool = True  # disabling this prevents figures
    fix_prime_symbols: bool = True  # prevents prime symbols from looking ugly
    allow_environments: bool = True  # enable the environment module.
    disable_legacy_environments: bool = True  # disable the legacy way to define environments.
    prevent_pdf_exports: bool = False  # prevents compiling of the tex file this program generates
    fix_derivatives: bool = True  # prevents dy/dx from looking weird
    replace_font: bool = True  # if True, remove font declarations in the pandoc preamble
    fix_unicode: bool = True  # prevents backslash text weirdness in equations
    autodetect_align_symbols: bool = True  # if False, &s are always put at the start for each align region
    pdf_engine: str = 'xelatex'  # what tex engine is used to combine
    max_line_length: int = 110  # max. relative length for equations. set this to a negative number to disable
    max_line_align: bool = True  # whether to enforce this in preexisting alignment envs
    fix_texttt: bool = True  # whether to fix every quirk with inline code.
    combine_aligns: bool = True  # whether to combine separate align sections if nothing is between
    special_proofs: bool = False  # whether proofs use the tcolorbox environment
    start_of_doc_text: str = ''  # text to append at the start right after the document begins
    verbatim_lang: str = ''  # the language of every code block in the document. Blank for don't even try.
    verbatim_plugin: str = 'minted'  # the plugin used for verbatim syntax highlighting. minted or lstlisting

    replacement_marker: str = 'TODO'  # the replacement marker in when using replacement mode

    table_of_contents: bool = False  # whether to include a table of contents.
    header_level: int = 0  # headers to shift by. 0 means no, 1 means L1 -> L2, -1 means L2 -> L1.
    # Keep in mind htat header level 4s in the Word Document are always paragraphs and will
    # not be affected by this setting.
    export_file_name_suffix: str = ''  # name of the exported tex and pdf file; no suffix
    media_folder_name: str = 'latex_images_'  # name of the image folder if any images are present
    # This should always be set to 'latex_images_' to prevent bugs.
    override_title: bool = True  # override the title in the replacement mode by the title in the Word doc
    override_author: bool = True  # override the author in the replacement mode by the author in the Word doc
    # to define an author in a Word doc it must be defined in the style "author".
    erase_pandoc_preamble: bool = False  # Allows erasing of the original Pandoc preamble. Some other modules must
    # be active for this to work.

    replacement_mode: bool = False  # whether replacement mode is on or off.
    environments: Optional[Union[dict, list[str]]] = None  # information relating to environments.

    eqn_comment_mode: str = 'tag'  # how comments in equations should be handled.
    label_equations: bool = True  # whether equations can be referenced
    auto_numbering: bool = False  # if this is true, label equations will be set to true and
    # comment mode will be set to "hidden" - meaning equations will be automatically numbered.

    remove_spaces_from_eqns: bool = False  # whether long spaces should be removed from equations.

    no_secnum: bool = False  # omit section numbering. This may affect how environments are numbered.
    conceal_verbatims: bool = True  # prevent verbatim environments from being affected,
    # unless a module specifically affects verbatim environments. This should always
    # be kept on.
    citation_brackets: bool = False  # whether brackets should wrap citations. Default for APA citations.
    bibtex_def: str = '\\usepackage{biblatex}'  # this is useless.
    citation_keyword: str = 'cite'  # the citation keyword, with no backslash at the end.
    cleanup: bool = True  # whether aux, bcf, log, and run.xml files should be removed only if
    # a successful export occurs. Image files will not be removed.
    disable_table_figuring: bool = False  # if set to true, prevents tables from being figured
    # no matter what.
    modify_tables: bool = True  # determine whether tables should be modified.
    # if false, longtable eliminator and table labeling will not work.
    document_class: str = '\\documentclass[12pt]{article}'  # the document class, or '' if it should not be changed.
    # Either the name of the document class, or the document class command (it's a command if it has a
    # backslash.)
    subsection_limit: int = -1  # the subsection limit. anything deeper will fallback to the limit.
    # -1 disable
    bibliography_keyword: str = 'Bibliography'  # The first section with this name will be treated
    hide_comments: bool = True  # hide comments in the preamble
    # as the Bibliography.
    allow_abstract: bool = True  # determine whether abstracts are allowed.
    small_margins: bool = True  # whether big margins should be used.
    latexing: bool = False  # LaTeX to \LaTeX. This is very buggy and should be kept off.
    headings: bool = False  # Whether headings should be included. This is redundant.

    conditional_preamble: bool = True  # whether to enable the conditional preamble.
    big_text: bool = True  # whether text should be large.
    _has_lang: bool = False  # private; do not modify.
    sty_cls_files: Optional[list[str]] = None  # a list of paths to .sty, .cls, .bst, or .def files,
    # relative to main.py. This is only needed if these files exist in a sub-folder. If a config
    # uses a preamble that requires custom sty, cls, bst, or def files, you should
    # state them here.
    hide_sty_cls_files: bool = False  # If sty_cls_files has entries, and this is set to true,
    # get rid of the sty, cls, bst, and def files after compiling the LaTeX document.
    image_float: str = 'H'  # the specifier used to place images. Remember that if this is
    # 'H', then \usepackage{float} is mandatory in your preamble.
    default_date: str = ''  # the default date, if none is stated. Empty if none.
    default_author: str = ''  # the default author, if none is stated. Empty if none.
    verbatim_options: str = ''  # options passed to minted and lstlisting used for
    # code blocks
    max_page_length: int = 35  # for use with the long table eliminator module, how long
    # a page is, in EM units.
    disable_bib_prompts: bool = True  # prevent biblio files from being asked at all.
    html_output: bool = False  # render an HTML file as well. Not affected by
    # whether the PDF file should not be rendered.
    force_shell_escape: bool = False  # force
    image_extra_commands: str = ''

    to_replace: Optional[dict[str, str]] = None
    tufte: bool = False  # am I using the tufte style?
    replacement_mode_skip: int = 0  # the number of headings in your Word File to skip when
    # using replacement mode.
    open_after_export: bool = True  # open the PDF file after exporting.
    # Requires that the OS is windows.
    export_folder: bool = False
    no_quotes_in_lists: bool = True
    no_unicode_fractions: bool = True
    center_tikz: bool = True

    def recalculate_invariants(self) -> None:
        """Recalculate some of its
        instance attributes.
        """
        if self.auto_numbering:  # auto numbering disallows comments
            self.label_equations = True
            self.eqn_comment_mode = 'hidden'
        if self.verbatim_lang != '' and self.verbatim_plugin == 'minted':
            self._has_lang = True
        if self.sty_cls_files is None:
            self.sty_cls_files = []
        if not has_pygments:
            self.verbatim_plugin = ''


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
    output_path: str  # in the form filename.tex
    text: str  # our latex converted stuff
    citation_path: str  # must ALWAYS be a valid .txt file
    bib_path: Optional[str]  # not a directory; just the name of the bib file
    raw_text: str
    original_tex: bool
    erase_pandoc_preamble: bool  # erase the pandoc preamble.
    citations_enabled: bool
    contains_longtable: bool
    disable_file_prompts: bool

    _temp_tex_file: str
    _disallow_pdf: bool

    def __init__(self, word_file_path: str, preferences: Preferences = DEFAULT_PREF,
                 disable_file_prompts: bool = False) -> None:
        """Initialize a new WordFile object.

        Raise an InvalidFileTypeError if word_file_path is not a Microsoft word file.
        The only IO function allowed here is to open the Word file and create temp.tex
        """
        self.disable_file_prompts = disable_file_prompts
        self.contains_longtable = False
        self.citations_enabled = False
        if word_file_path[-5:] != '.docx' and word_file_path[-4:] != '.tex':
            raise InvalidFileTypeError
        if ' ' in word_file_path:
            pass  # raise SpaceError
        self.word_file_path = word_file_path
        self.word_file_nosuffix = os.path.basename(word_file_path)[:-5]
        self.preferences = preferences
        self.preferences.recalculate_invariants()
        self._temp_tex_file = TEMP_TEX_FILENAME
        export_suffix = self.preferences.export_file_name_suffix + '.tex'
        self.output_path = self.word_file_nosuffix + export_suffix
        if word_file_path[-5:] == '.docx':
            self.text = self.open_word_file()
            # print(self.text)
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
        # if preferences.allow_citations:
        #     print('Opening the bib document file open box. If noting opens, consider re-running this program.')
        #     file_info = askopenfile(mode='r', title='Open the bib file you want to combine',
        #                             filetypes=[('Bib Files', '*.bib')])
        #     self.bib_path = file_info.name.replace("/", "\\") if file_info is not None else None
        #     if self.bib_path is None:
        #         print('You did not specify a bib path, so we\'re assuming you\'re not citing anything')
        if self.preferences.prevent_pdf_exports:
            self._disallow_pdf = True

        # remove all spaces from document
        self.word_file_path = self.word_file_path.replace(' ', '_')  # .replace('LaTeX', 'Latex')
        self.word_file_nosuffix = self.word_file_nosuffix.replace(' ', '_')  # .replace('LaTeX', 'Latex')
        self.output_path = self.output_path.replace(' ', '_')  # .replace('LaTeX', 'Latex')

    def _demand_citations(self) -> None:
        """Ask for citations. Should only be called if we want citations.
        """
        # pass
        if not self.preferences.disable_bib_prompts:
            if self.disable_file_prompts:
                raise AttemptedFilePromptError
            else:
                print('Opening the bib document file open box. If nothing opens, consider re-running this program.')
                file_info = askopenfile(mode='r', title='Open the bib file you want to combine',
                                        filetypes=[('Bib Files', '*.bib')])
                self.bib_path = file_info.name.replace("/", "\\") if file_info is not None else None
                if self.bib_path is None:
                    print('You did not specify a bib path, so we\'re assuming you\'re not citing anything')
                else:
                    self.bib_path = os.sep.join(self.bib_path.split('\\'))
        else:
            print('The document does contain a bibliography section, but we will not ask for it'
                  ' as it is forced disabled.')

    def _recalculate_erase_preamble(self) -> None:
        """Determine whether the pandoc preamble should be removed based on preferences."""
        force = True
        if force:
            self.erase_pandoc_preamble = self.preferences.erase_pandoc_preamble
        else:
            self.erase_pandoc_preamble = all(
                [self.preferences.allow_no_longtable, self.preferences.erase_pandoc_preamble])

    def sequence(self) -> None:
        """Completely process and export the word file to tex."""
        if self.preferences.exclude_preamble:
            self.preferences._disallow_pdf = True
        if not self.preferences.disable_repair:  # if disable repair is FALSE
            self.latex_repair()
        self.export()

    def open_word_file(self) -> str:
        """Return tex code of WordFile."""
        using_command_prompt = not USE_SUBPROCESSES
        if using_command_prompt:
            raise ValueError("Branch NOT to be ran at all. Command prompt"
                             " is not to be used.")
            # media_path = '--extract-media=' + self.preferences.media_folder_name + \
            #              self.word_file_nosuffix.replace(' ', '_')
            # dquote = '"'
            # # toc = '--toc'
            # # these are writer options
            # # tuple index 0 is the string; tuple index 1 is the condition
            # filter_list = [
            #     ('-s', True),
            #     (f'--shift-heading-level-by={self.preferences.header_level}', self.preferences.header_level != 0),
            #     ('--toc', self.preferences.table_of_contents)
            # ]
            # # if self.preferences.table_of_contents:
            # #     filter_list.append('--toc')
            #
            # filters_1 = ' '.join(process_permissive_list(filter_list))
            #
            # # command_string = 'cmd /c "pandoc ' + media_path + ' -s ' + \
            # #                 self.word_file_path + ' -o ' + self._temp_tex_file
            #
            # # self.preferences.pdf_engine
            #
            # pdf_engine_str = '--pdf-engine=xelatex '
            # # f'--pdf-engine={self.preferences.pdf_engine} ' if self.preferences.pdf_engine != 'pdflatex' else ''
            # command_string = f'pandoc {dquote}{media_path}{dquote} {filters_1} {dquote}{self.word_file_path}{dquote} ' \
            #                  f'{pdf_engine_str}-o {self._temp_tex_file}'
            # os.system(command_string)
            # return open_file(self._temp_tex_file)
        else:
            media_path = '--extract-media=' + self.preferences.media_folder_name + \
                         self.word_file_nosuffix.replace(' ', '_')
            # dquote = '"'
            # toc = '--toc'
            # these are writer options
            # tuple index 0 is the string; tuple index 1 is the condition
            # pdf_engine_str = '--pdf-engine=xelatex '
            command_list_raw = [
                ('pandoc', True),
                (media_path, True),
                ('-s', True),
                (f'--shift-heading-level-by={self.preferences.header_level}', self.preferences.header_level >= 1),
                # ('--toc', self.preferences.table_of_contents), TABLE OF CONTENTS IS HANDLED OTHERWISE
                # ('--top-level-division=chapter', self.preferences.document_class in ['book', 'tufte-book']),
                (self.word_file_path, True),  # FILTERS END HERE
                ('--pdf-engine=xelatex', False),
                ('-o', True),
                (self._temp_tex_file, True)
            ]
            command_list = process_permissive_list(command_list_raw)
            subprocess.run(command_list)
            return open_file(self._temp_tex_file)

    def latex_repair(self) -> None:
        """Repair generated latex file.
        """
        dataclass_dict = {}
        p_start = open_multiple_files(self.preferences.preamble_path)

        text = self.text
        text = text + '\n\n\n\n\n\nò÷öæ🬵🬶	🬷'
        # some additional text to prevent abrupt document ends.
        # as an invariant, the unicode mess above must remain untouched.
        start = '\\begin{document}'
        end = '\\end{document}'
        text, start, end = w2l.find_between(text, start, end)
        dict_info_hide_verb = {}

        if self.preferences.table_of_contents:
            text = dbl.toc_detector(text, min(self.preferences.header_level, 0))

        # PUSH HEADER LEVELS, IF APPLICABLE
        if -2 <= self.preferences.header_level <= -1:
            text = dbl.make_chapter(text, depth=self.preferences.header_level)
        # CONCEAL ALL VERBATIMS
        if self.preferences.conceal_verbatims:
            text, dict_info_hide_verb = dbl.hide_verbatims(text, self.preferences.bibliography_keyword,
                                                           self.preferences.verbatim_plugin)
        if self.preferences.hypertarget_remover:
            text = w2l.hypertarget_eliminator(text)
        if self.preferences.forbid_images:
            logging.warning('About to remove images')
            text = dbl.remove_images(text)
        # text = dbl.include_graphics_failsafe(text)
        if self.preferences.fix_vectors:
            text = w2l.fix_vectors(text)
            text = w2l.fix_vectors_again(text)
            text = dbl.fix_accents(text)
        if self.preferences.allow_abstract:
            text = dbl.abstract_wrapper(text)
        if self.preferences.latexing:
            text = dbl.latexing(text)
        if self.preferences.allow_environments and self.preferences.environments is not None:
            text = dbl.framed(text)
            text = dbl.work_with_environments(text, self.preferences.environments,
                                              self.preferences.disable_legacy_environments)

        if self.preferences.allow_proofs:
            text = dbl.qed(text, self.preferences.special_proofs)
        # if True:
        #    text = dbl.longtable_backslash_add_full(text)

        if self.preferences.modify_tables:  # LONGTABLE ELIMINATOR
            disallow_tab_f = self.preferences.disable_table_figuring or self.preferences.disallow_figures
            text = dbl.eliminate_all_longtables(text, disallow_tab_f,
                                                self.preferences.allow_no_longtable,
                                                float_type=self.preferences.image_float,
                                                max_page_len=self.preferences.max_page_length)

        eqn_comment = {'comment_type': self.preferences.eqn_comment_mode, 'label_equations':
            self.preferences.label_equations}
        # if self.preferences.remove_spaces_from_eqns:
        #     # TODO: after text, prevent messing with commands
        #     text = dbl.bad_backslash_replacer(text)
        #     text = dbl.bad_backslash_replacer(text, '\\(', '\\)')

        if self.preferences.to_replace is not None:
            for r_key, r_value in self.preferences.to_replace.items():
                text = text.replace(r_key, r_value)

        labels_so_far = []
        if self.preferences.allow_alignments:  # alignments must always run first
            while True:
                max_line = self.preferences.max_line_length if self.preferences.max_line_align else -1
                text, stat, labbs = w2l.replace_align_region(text,
                                                             self.preferences.autodetect_align_symbols,
                                                             max_line, extra_info=eqn_comment)
                # print('stat')
                labels_so_far.extend(labbs)
                if stat:
                    break
        auto_labeling = self.preferences.label_equations and self.preferences.eqn_comment_mode == 'hidden'
        # eqn_comment['second_time'] = True
        if self.preferences.max_line_length >= 1:
            text, labels_split_so_far = dbl.split_all_equations(text, self.preferences.max_line_length,
                                                                label_equations=self.preferences.label_equations,
                                                                tag_equations=not auto_labeling)
            labels_so_far.extend(labels_split_so_far)
            if len(set(labels_so_far)) != len(labels_so_far):
                logging.warning('Some equations have duplicate labels.')
            while True:
                # the second time alignment replacement is used.
                # this time, discard all labels.
                text, stat, _ = w2l.replace_align_region(text,
                                                         self.preferences.autodetect_align_symbols)
                if stat:
                    break

        # use refs, which work in a very similar way to how it is implemented in tables
        if self.preferences.label_equations:
            text = dbl.bulk_labeling(text, labels_so_far, 'equation', 'ref', 'eq')
        if self.original_tex:
            text, self._disallow_pdf = dbl.truncate_path(text, self._disallow_pdf)

            logging.warning('Removing images')
        elif self.preferences.center_images:
            text = dbl.detect_include_graphics(text, self.preferences.disallow_figures, self.preferences.image_float,
                                               self.preferences.tufte)

        if self.preferences.fix_prime_symbols:
            text = w2l.prime_dealer(text)
        if self.preferences.fix_derivatives:
            text = dbl.dy_fixer(text)

        if self.preferences.dollar_sign_equations:
            text = w2l.dollar_sign_equations(text)
        if self.preferences.fix_unicode:
            # print(text)
            text = dbl.text_bound_fixer(text, REPLAC)
        if self.preferences.fix_texttt:
            text = dbl.fix_all_textt(text)
        if self.preferences.combine_aligns:
            text = dbl.combine_environments(text, 'align*', ' \\\\')
        # combines matrices. This is forced.
        text = dbl.aug_matrix_spacing(text)
        if self.preferences.verbatim_plugin in ('lstlisting', 'minted'):
            text, lang_converted = dbl.verbatim_to_listing(text, self.preferences.verbatim_lang, self.preferences.verbatim_plugin,
                                                           self.preferences.verbatim_options)
            # no language??
            if not lang_converted and self.preferences.verbatim_plugin == "minted":
                print('No language declarations.')
                self.preferences.verbatim_plugin = "NOTHING"
            # I might have to change this if I ever decide to use auto
            # language detection
        # text = text.replace('…', '...')  # only occurs in verbatim envs
        has_bib_file = False
        if self.preferences.center_tikz:
            text = dbl.center_tikz(text, self.preferences.image_float)
        if self.preferences.allow_citations:  # if citations are allowed
            proceed_citations, temp_text_here, bib_ind = dbl.detect_if_bib_exists(text,
                                                                                  self.preferences.bibliography_keyword)
            bib_text = dict_info_hide_verb.get('BIBLO', '')
            if proceed_citations:
                if bib_text == '':
                    self._demand_citations()
                else:
                    self.bib_path = 'DO NOT OPEN!!!!?'
                if self.bib_path is not None:
                    if self.bib_path != 'DO NOT OPEN!!!!?':
                        bib_data = open_file(self.bib_path)
                    else:
                        bib_data = bib_text
                        self.bib_path = self.word_file_nosuffix + '-citations.bib'
                    # position the print bibilo first
                    # bib_style = 'unsrt'
                    # bib_final = '\\bibliographystyle{' + bib_style + '}\n\\medskip\n\\bibliography{' + \
                    #     self.bib_path + '}'

                    # temp_text_here = temp_text_here[:bib_ind] + bib_final + \
                    #     temp_text_here[bib_ind:]
                    bib_num = '[heading=bibnumbered]' if not self.preferences.no_secnum else ''
                    cite_properties = {'bibtex_def': self.preferences.bibtex_def, 'citation_kw':
                                        self.preferences.citation_keyword}
                    temp_text_here = temp_text_here[:bib_ind] + '\\medskip\n\\printbibliography' + bib_num + \
                        temp_text_here[bib_ind:]
                    # then replace the citations
                    text = dbl.do_citations(temp_text_here, bib_data, self.preferences.citation_mode,
                                            self.preferences.citation_brackets, cite_properties)
                    last_dbl_backslash = self.bib_path.replace('/', '\\').rfind('\\')
                    if last_dbl_backslash == -1:
                        has_bib_file = self.bib_path
                        # last_dbl_backslash -= 1
                    else:
                        has_bib_file: Union[bool, str] = self.bib_path[last_dbl_backslash + 1:]
                    self.citations_enabled = True
                    assert has_bib_file.endswith('.bib')
                    # rewrite the bib file in the same directory as this .py file
                    # ensure that the bib file is written as well in the same location
                    write_file(bib_data, has_bib_file)
                    # check if we have used bibtex
                    # modify the preamble to add the bibtex module specified in the config
                    # if self.preferences.bibtex_def != '':
                    # p_start = dbl.check_bibtex(p_start, self.preferences.bibtex_def)
        # if self.preferences.allow_citations and self.citation_path \
        #         is not None and self.bib_path is not None:
        #     bib_data = open_file(self.bib_path)
        #     text = dbl.do_citations(text, bib_data, self.preferences.citation_mode)
        #     text = text + '\\medskip\n\\printbibliography'
        if self.preferences.subsection_limit >= 1:
            text = dbl.subsection_limit(text, self.preferences.subsection_limit, 6)
        if self.preferences.no_unicode_fractions:
            text = dbl.remove_unicode_fractions(text)
        if self.preferences.no_quotes_in_lists:
            text = dbl.no_quotes_in_itemize_enumerate(text)
        if self.preferences.conceal_verbatims:
            text = dbl.show_verbatims(text, dict_info_hide_verb)
        # always on
        text = dbl.verbatim_regular_quotes(text)
        text = text.replace('ò÷öæ🬵🬶	🬷', '')

        if '\\begin{longtable}' in text:  # check if text has a longtable
            self.contains_longtable = True  # and set contains longtable to true.

        if self.preferences.conditional_preamble:  # if this is off, everything shows up.
            dataclass_dict = asdict(self.preferences)
            dataclass_dict['_citations_enabled'] = self.citations_enabled
            dataclass_dict['_contains_longtable'] = self.contains_longtable
            # for the conditional preamble module,
            # if a value is not detected then it is
            # always true by default. it will
            # not show up if it is false.
            p_start = dbl.conditional_preamble(p_start, dataclass_dict)

        if not self.preferences.exclude_preamble:  # if preamble is included

            preamble = w2l.deal_with_preamble(text=self.raw_text[:start],
                                              has_bib_file=has_bib_file,
                                              remove_default_font=self.preferences.replace_font,
                                              preamble_path=p_start,
                                              erase_existing_preamble=self.erase_pandoc_preamble,
                                              omit_section_numbering=self.preferences.no_secnum,
                                              dataclass_dict=dataclass_dict)

            if self.preferences.hide_comments:
                preamble = dbl.remove_comments_from_document(preamble)

            text = preamble + '\n' + self.preferences.start_of_doc_text + '\n\n' + text + '\n\n' + \
                self.raw_text[end:]
        # else do nothing
        if self.preferences.document_class != '':
            text = dbl.change_document_class(text, self.preferences.document_class)
        if self.preferences.default_date != '':
            text = text.replace('\\date{}', '\\date{' + self.preferences.default_date + '}', 1)
        if self.preferences.default_author != '':
            text = text.replace('\\author{}', '\\author{' + self.preferences.default_author + '}', 1)
        self.text = text

    def export(self) -> None:
        """Export everything in self.text
        """
        subprocesses = USE_SUBPROCESSES
        if subprocesses:
            # try:
            #     os.mkdir('export')
            # except FileExistsError:
            #     pass
            # self.output_path = 'export\\' + self.output_path
            if self.preferences.hide_sty_cls_files:
                sty_cls = move_sty_cls_files(self.preferences.sty_cls_files)
            else:
                move_sty_cls_files(self.preferences.sty_cls_files)
                sty_cls = []
            latex_engine = self.preferences.pdf_engine
            if latex_engine not in ALLOWED_LATEX_COMPILERS:
                latex_engine = 'xelatex'
            dq = '"'
            write_file(self.text, self.output_path)
            if self._disallow_pdf or self.preferences.prevent_pdf_exports:
                print('No PDF to be exported here.')
                return
            if self.preferences.html_output:
                html_command = [
                    'pandoc',
                    self.output_path,
                    '-f',
                    'latex',
                    '-t',
                    'html',
                    '--katex',
                    '-s'
                    '-o',
                    self.output_path[:-4] + '.html'
                ]
                if self.citations_enabled:
                    print(f'citations are enabled and will read {self.bib_path}')
                    html_command.append('--citeproc')
                    html_command.append(f'--bibliography={self.bib_path}')
                print('exporting HTML...')
                subprocess.run(html_command)

            if not self._disallow_pdf:
                output_dir_command = "-output-directory=export" if self.preferences.export_folder else ""
                if self.preferences.force_shell_escape or '\\usepackage{minted}' in self.text:
                    latex_compile_command = [latex_engine, output_dir_command, '-shell-escape', self.output_path]
                else:
                    latex_compile_command = [latex_engine, output_dir_command, self.output_path]
                latex_compile_command = [w for w in latex_compile_command if w != '']
                # latex_output_path = self.output_path[:-4] + '.pdf'
                subprocess.run(latex_compile_command)

                # running biblatex on the file
                # this is broken.

                if self.citations_enabled:
                    biblatex_command = ['bibtex8', '--wolfgang', self.output_path[:-4]]
                    print(biblatex_command)
                    subprocess.run(biblatex_command)

                # export it a second time
                subprocess.run(latex_compile_command)

                # command_string_2 = latex_engine + ' "' + self.output_path + '"'
                command_string_3 = '"' + self.output_path[:-4] + '.pdf' '"'
                print(f'opening {self.output_path[:-4]}.pdf.')
                if self.preferences.open_after_export and platform.system() == 'Windows':
                    os.system(command_string_3)
                # os.system(command_string_2)  # compile the pdf

                # if citations are on OR (figures are on AND center images / long table eliminators are on)
                # if (self.preferences.allow_citations and self.bib_path is not None) or (
                #         not self.preferences.disallow_figures and (
                #         self.preferences.allow_no_longtable or self.preferences.center_images)):
                #     subprocess.run(latex_compile_command)

                # subprocess.run(['open', latex_output_path])
            else:
                command_string_4 = f'{dq}{self.output_path}{dq}'
                print('You inputted a .tex file that contains images, so we aren\'t compiling')
                if self.preferences.open_after_export:
                    os.system(command_string_4)

            self.output_path = os.path.basename(self.output_path)
            print('Finished!')
            assert self.output_path[-4:] == '.tex'
            if self.preferences.cleanup:
                print('removing all unneeded files in 2 seconds')
                time.sleep(2)
                output_nameless = self.output_path[:-4]
                cleanup.move_useless_files_away(output_nameless, sty_cls)

        else:
            raise ValueError("Brach NOT to be reached.")
            # try:
            #     os.mkdir('export')
            # except FileExistsError:
            #     pass
            # self.output_path = 'export\\' + self.output_path
            # ----------- UNCOMMENT BELOW IF NEEDED -----------
            # latex_engine = self.preferences.pdf_engine
            # if latex_engine not in ALLOWED_LATEX_COMPILERS:
            #     latex_engine = 'xelatex'
            # dq = '"'
            # write_file(self.text, self.output_path)
            # if not self._disallow_pdf:
            #     command_string_2 = latex_engine + ' "' + self.output_path + '"'
            #     command_string_3 = '"' + self.output_path[:-4] + '.pdf' '"'
            #     # os.system(command_string_2)
            #     os.system(command_string_2)  # compile the pdf
            #     # if citations are on OR (figures are on AND center images / long table eliminators are on)
            #     if (self.preferences.allow_citations and self.bib_path is not None) or (
            #             not self.preferences.disallow_figures and (
            #             self.preferences.allow_no_longtable or self.preferences.center_images)):
            #         os.system(command_string_2)  # compile it again
            #     os.system(command_string_3)
            # else:
            #     command_string_4 = f'{dq}self.output_path{dq}'
            #     print('You inputted a .tex file that contains images, so we aren\'t compiling')
            #     os.system(command_string_4)
            #
            # print('Finished!')
            # assert self.output_path[-4:] == '.tex'
            # if self.preferences.cleanup:
            #     print('removing all unneeded files')
            #     output_nameless = self.output_path[:-4]
            #     cleanup.move_useless_files_away(output_nameless)


class WordFileCombo(WordFile):
    """Used for LaTeX combos.
    """
    corresponding_tex_file: str
    alt_text: str
    author: Optional[str]
    doc_title: Optional[str]

    def __init__(self, word_file_path: str, preferences: Preferences = DEFAULT_PREF,
                 disable_file_prompts: Optional[bool] = None,
                 corresponding_tex_file: Optional[str] = None) -> None:
        super().__init__(word_file_path, preferences, disable_file_prompts)
        print('Opening the replacement tex file open box. If nothing opens, consider re-running this program.')

        if corresponding_tex_file is None:
            if self.disable_file_prompts:
                raise AttemptedFilePromptError
            else:
                file_info = askopenfile(mode='r', title='Open the TeX file you want to combine',
                                        filetypes=[('Tex Files', '*.tex')])
                self.corresponding_tex_file = file_info.name.replace("\\", "/") if file_info is not None else None
                self.corresponding_tex_file = os.sep.join(self.corresponding_tex_file.split('/'))  # ensures multi os
                # compatible
        else:
            self.corresponding_tex_file = corresponding_tex_file
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
        self.author = dbl.find_author(self.text, 'author')
        self.doc_title = dbl.find_author(self.text, 'title')

        logging.warning(f'author name is {self.author} and title name is {self.doc_title}')

        self.latex_repair()
        # self.text = dbl.strip_regular_sections(self.text)
        new_file_text_2, new_file_start, new_file_end = w2l.document_extract(self.alt_text)
        # preamble_mode = dbl.deduce_preamble_mode(new_file_text_2)
        file_text = open_multiple_files(self.preferences.preamble_path)
        new_file_start = dbl.insert_in_preamble(new_file_start, file_text)
        new_file_text_3 = dbl.many_instances(self.text, new_file_text_2, self.preferences.replacement_marker,
                                             self.preferences.replacement_mode_skip)
        new_file_text_4 = new_file_start + new_file_text_3 + new_file_end
        # if self.preferences.override_author and isinstance(self.author, str):
        #     new_file_text_4 = dbl.swap_author(new_file_text_4, self.author, 'author')
        # if self.preferences.override_title and isinstance(self.doc_title, str):
        #     new_file_text_4 = dbl.swap_author(new_file_text_4, self.doc_title, 'title')
        self.text = new_file_text_4
        # print(new_file_text_4)
        self.export()


def open_multiple_files(files: Union[list[str], str]) -> str:
    """Open multiple files in order. If an error occurs opening
    a file, don't open anything.
    """
    if isinstance(files, str):
        try:
            with open(files) as f:
                prestart = f.read()
        except FileNotFoundError:
            print('you specified a file that did not exist')
            prestart = ''
    else:
        preamble_text_list = []
        for pr_path in files:
            try:
                with open(pr_path) as f:
                    preamble_text_list.append(f.read())
            except FileNotFoundError:
                print('you specified a preamble that did not exist')
                pass
        prestart = '\n'.join(preamble_text_list)
    return prestart


def move_sty_cls_files(files: list[str]) -> list[str]:
    """Copy all files specified in the list of files to
    the same directory as this .py file.

    Copy means literally taking the text contents of the file.

    Return the list of files that were copied.
    """
    files_moved = []
    for file in files:
        f_contents = open_file(file)

        last_dbl = file.rfind('\\')
        last_b = file.rfind('/')
        if last_dbl == -1 and last_b == -1:
            target = -1
        elif last_dbl == -1 and last_b != -1:
            target = last_b
        elif last_dbl != -1 and last_b == -1:
            target = last_dbl
        else:
            assert last_dbl != -1 and last_b != -1
            target = max(last_dbl, last_b)
        file_name = file[target + 1:]
        allowed_extensions = ['.sty', '.cls', '.def', '.bst']
        if not any(file.endswith(x) for x in allowed_extensions):
            raise ValueError('sty-cls files can ONLY end with .sty, .cls, .bst, or .def.')
        else:
            # print(f_contents + ' ' + file_name)
            # write_file(f_contents, file_name)
            if len(file) != len(file_name):
                # add to the list only if the file is in a sub-directory
                write_file(f_contents, file_name)
                files_moved.append(file_name)
    return files_moved


def check_config(json_path: str, overrides: dict[str, Any]) -> tuple[Preferences, bool]:
    """Return Preferences based on configurations.
    """
    with open(json_path) as json_file:
        data = json.load(json_file)
    try:
        # temp_data = dict(data)

        for t_key, t_value in overrides.items():
            data[t_key] = t_value
        field_names = set(f.name for f in fields(Preferences))
        cur_prefs = Preferences(**{k: v for k, v in data.items() if k in field_names})
        # this works perfectly
    except KeyError:
        cur_prefs = Preferences()
        logging.warning('The config file is broken, so defaulting to all defaults.')
    return cur_prefs, data["replacement_mode"]


def main(config: str = '', overrides: Optional[dict] = None,
         path_to_wordfile: Optional[str] = None,
         replacement_mode_path: Optional[str] = None,
         disable_file_prompts: bool = False) -> None:
    """The main method of this module.

    All paths are relative to main.py.
    Parameters
    ----------

    config
        the path to the config used. leave blank to take what is in mode.txt, if it exists.
    overrides
        the key-value pairs passed in overrides will override any config value.
    path_to_wordfile
        the path to the wordfile or any plain text file. If it's a word file, it will
        open the document in the MS Word way. Otherwise, it will treat it as if
        a plain-text file was being opened.
    replacement_mode_path
        the path to the other .tex file used in replacement mode, or None if that
        should be prompted. Do nothing if not in replacement mode.
    disable_file_prompts
        if this is set to true, if a file prompt comes up
        an error will be thrown.

    Returns
    -------
        Nothing
    """
    if overrides is None:
        overrides = {}

    # invariants must be met

    try:
        print('Opening the word document file open box. If nothing opens, consider re-running this program.')
        if path_to_wordfile is None:
            if disable_file_prompts:
                raise AttemptedFilePromptError('A word file prompt would have shown here.')
            else:
                main_file_mfn = askopenfile(mode='r', title='Open the word file you want to convert',
                                            filetypes=[('Word Files', '*.docx'), ('Tex Files', '*.tex')])
            path_mfn = main_file_mfn.name.replace("\\", "/") if main_file_mfn is not None else None
        else:
            path_mfn = path_to_wordfile.replace("\\", "/")
        if path_mfn is None:
            print('You didn\'t select anything')
            exit()
        print(path_mfn)
        path_mfn = os.sep.join(path_mfn.split('/'))  # ensure that the os is always consistent
        if config == '':
            json_dir_mfn = open_file('mode.txt')
        else:
            json_dir_mfn = config
        json_dir_mfn = os.sep.join(json_dir_mfn.replace('\\', '/').strip().split('/'))
        prefs_mfn, replacement_mode_mfn = check_config(json_dir_mfn, overrides)

        # determines whether replacement mode is on or off
        if replacement_mode_mfn:
            print('We are in replacement mode')
            word_file_mfn = WordFileCombo(path_mfn, prefs_mfn,
                                          corresponding_tex_file=replacement_mode_path,
                                          disable_file_prompts=disable_file_prompts)
        else:
            word_file_mfn = WordFile(path_mfn, prefs_mfn, disable_file_prompts=disable_file_prompts)

        # process and export the file.
        word_file_mfn.sequence()
    finally:
        print('Ending program. If a PDF was never compiled, it means something\'s wrong with'
              ' the file you\'ve chosen. Press ENTER to quit if the program will not quit\n'
              'by itself.')
        # time.sleep(2)


def list_get(lst: list[Any], index: int, default: Any = None) -> Any:
    """Grab the list at index, or default otherwise.

    Parameters
    ----------
    lst
        the list
    index
        the index
    default
        if index DNE

    Returns
    -------
        item at index or default if index DNE
    """
    if index < 0:
        index = len(lst) - index
    if 0 <= index < len(lst):
        return lst[index]
    else:
        return default


if __name__ == '__main__':
    import sys
    full_command = sys.argv[1:]
    if len(full_command) != 0:
        main_path_to_wordfile = full_command[0]
        config_mode = list_get(full_command, 1, os.path.join('config_modes', 'config_standard.json'))  # default: config_standard.json
        main_replacement_mode_path = list_get(full_command, 2)  # default: None
        main_disable_file_prompts: bool = True  # always True
        print('Make sure you include the folder the config files are in!!')
        main(config_mode, {}, main_path_to_wordfile, main_replacement_mode_path, main_disable_file_prompts)
    else:
        print('No word file specified! Doing nothing.')
