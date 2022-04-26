"""
Move all useless files to a new folder
"""
import os
import logging
from typing import Iterable, Optional


REMOVE_IMAGES = False


def new_folder(folder_name: str) -> str:
    """Create a new directory in the same directory as this .py file, and return its path.
    """
    if ' ' in folder_name:
        raise IOError
    current_directory = os.getcwd()
    final_directory = os.path.join(current_directory, folder_name)
    if not os.path.exists(final_directory):
        os.makedirs(final_directory)
    else:
        pass
        # logging.warning('cannot create new folder due to existing folder')
    return current_directory + '\\' + folder_name


def __obtain_files_to_move() -> list[str]:
    """Return a list of filenames from a directory, and then
    only include images within the allowed formats.
    """
    current_directory = os.getcwd()
    suffixes = [
        '.aux',
        '.idx',
        '.lof',
        '.log',
        '.lot',
        '.fls',
        '.toc',
        '.out',
        '.toc',
        '.fmt',
        '.fot',
        '.cb',
        '.cb2',
        '.lb',
        '.bbl',
        '.bcf',
        '.blg',
        '-blx.aux',
        '-blx.bib',
        '.run.xml',
        '.fdb_latexmk',
        '.synctex',
        '.synctex(busy)',
        '.synctex.gz',
        '.synctex.gz(busy)',
        '.pdfsync',
        '.thm'
    ]
    additional_suffixes = ['.tex', '.pdf']
    ipt = input('Would you like to clear TEX and PDF files also? '
                '(Type YES in all caps to do so, or anything else to NOT): ')
    if ipt == 'YES':
        suffixes.extend(additional_suffixes)
    prefixes = ['TEXIMAGEF_', 'TEXIMAGE_', 'latex_images_', '_minted-']
    directory_files = os.listdir(current_directory)
    passing_files = [file for file in directory_files
                     if __filter_suffix(file, suffixes) ^ __filter_prefix(file, prefixes)]
    return passing_files


def __filter_prefix(filename: str, prefixes: Iterable) -> bool:
    """Return True if filename starts with any prefix listed.
    """
    for pre in prefixes:
        if filename[:len(pre)] == pre:
            return True
    return False


def __filter_suffix(filename: str, suffixes: Iterable) -> bool:
    """Return True if filename ends with any suffix listed.
    """
    for suf in suffixes:
        if filename[-len(suf):] == suf:
            return True
    return False


def __main() -> None:
    """This is the main branch.
    """
    folder_name = 'TRASH_LATEX_FILES'
    new_folder_path = new_folder(folder_name)
    logging.warning('TARGET FOLDER IS' + new_folder_path)
    file_move_list = __obtain_files_to_move()
    print(file_move_list)
    for file in file_move_list:
        logging.warning('REPLACED ' + file)
        try:
            os.replace(file, new_folder_path + '\\' + file)
        except PermissionError:
            pass


def move_useless_files_away(file_name: str, additional_files: Optional[list[str]] = None) -> None:
    """Move all temp. tex related files into the trash folder.
    This does overwrite!!
    """
    if additional_files is None:
        additional_files = []
    current_directory = os.getcwd()
    forbidden_filetypes = ['.aux', '.bcf', '.log', '.run.xml', '.bbl', '.blg', '.fdb_latexmk',
                           '.fls', '.synctex.gz', '-blx.bib']
    folder_name = 'TRASH_LATEX_FILES'

    image_directory = 'latex_images_'
    minted_directory = '_minted-'

    directory_files = os.listdir(current_directory)
    new_folder_path = new_folder(folder_name)
    # logging.warning('TARGET FOLDER IS' + new_folder_path)
    files_to_move = [file_name + x for x in forbidden_filetypes if file_name + x in directory_files]
    if REMOVE_IMAGES and image_directory + file_name in directory_files:
        files_to_move.append(image_directory + file_name)
    if minted_directory + file_name in directory_files:
        files_to_move.append(minted_directory + file_name)
    files_to_move.extend(additional_files)
    for fm in files_to_move:
        # logging.warning('REPLACED ' + fm)
        try:
            os.replace(fm, new_folder_path + '\\' + fm)
        except PermissionError:
            print(f'Cannot move file {fm}')


WARNING_STR = f"""
================ WARNING ==================
THIS WILL MOVE ALL LATEX-RELATED FILES INTO
A FOLDER NAMED "TRASH_LATEX_FILES". THE
FOLDER WILL BE LOCATED IN THE SAME
DIRECTORY AS THE FILE YOU CLICKED ON.

IF A FOLDER NAMED "TRASH_LATEX_FILES" DOES
NOT EXIST IN THE CURRENT DIRECTORY, ONE WILL
BE CREATED.

IF "TRASH_LATEX_FILES" EXISTS IN THE CURRENT
DIRECTORY, ANY FILES THAT ARE MOVED INTO
SAID FOLDER WILL REPLACE ANY EXISTING FILES
WITH THE SAME NAME.

THIS SHOULD ONLY BE RUN ON WINDOWS
COMPUTERS.

YOUR CURRENT DIRECTORY IS {os.getcwd()}

DO YOU WISH TO PROCEED?

TYPE "YES" IN ALL CAPS TO PROCEED, OR
ANYTHING ELSE TO CANCEL.
==========================================
"""


if __name__ == '__main__':
    str_input = input(WARNING_STR)
    if str_input == 'YES':
        __main()
