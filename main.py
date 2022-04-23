import json
import os
import tkinter
from typing import Any

import converter as conv
from tkinter import Button, Label, StringVar, OptionMenu, Tk, BooleanVar, Checkbutton

NEEDED_CONFIG_VARS = ['forbid_images', 'table_of_contents']


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


def read_json(json_dir: str) -> tuple[str, dict[str, Any]]:
    with open(json_dir) as json_file:
        data = json.load(json_file)
    data_dict = dict(data)
    description = data_dict.get('description', 'No description provided.')
    return description, data_dict


def update_desc(*args) -> dict[str, Any]:
    """Also return the config!!!
    """
    sv = variable.get()
    np = 'config_modes\\' + sv
    desc, data = read_json(np)
    lim = 60
    if len(desc) > lim:
        times = 1
        while True:

            nl = desc.find(' ', lim * times)
            if nl != -1:
                desc = desc[:nl] + '\n' + desc[nl:]
                times += 1
            else:
                break
    var2.set(desc)

    return data  # we don't actually need this


def initial(data: dict[str, Any]) -> dict[str, BooleanVar]:
    """Data is what was returned from update_desc
    """
    data_filtered = filter_keys(NEEDED_CONFIG_VARS, data)
    return checkbox_variables(data_filtered)


def filter_keys(allowed: list[str], keys: dict[str, Any]) -> dict[str, Any]:
    """Only keep the keys in allowed, for the dictionary we are
    talking about.
    """
    return {k: keys[k] for k in keys if k in allowed}


def checkbox_variables(keys: dict[str, Any]) -> dict[str, BooleanVar]:
    """Some variables are changed
    so commonly that I'd rather put a yes/no
    to this right now.

    key - variable name
    value - default value

    These are based off the config that has been selected.
    If I can't find these values in the config then they will be false
    by default. Oftentimes, false things WILL be those of inaction.

    Preconditions:
        - root has been set up

    Return the dictionary when finished.
    """
    cur_dict = {}
    for key, value in keys.items():
        print(key)
        print(value)
        if value is not None or not isinstance(value, bool):
            continue
        cur_dict[key] = tkinter.BooleanVar()
        if value is None:
            value = False

        cur_dict[key].set(value)
        check_btn = Checkbutton(root, text=key, variable=cur_dict[key], onvalue=True, offvalue=False)
        check_btn.pack()
    return cur_dict


def click() -> None:
    sv = variable.get()
    root.destroy()

    np = 'config_modes\\' + sv
    np2 = 'config_modes/' + sv
    print(np)
    write_file(np2, 'mode.txt')
    preamble_changes = {'forbid_images': zero_one_tf(hide_images_state.get()),
                        'pdf_engine': options[rd.get()]}
    print(preamble_changes)
    conv.main(np)


def zero_one_tf(num: int) -> bool:
    return num == 1


if __name__ == '__main__':

    current_directory = os.getcwd()
    cfg_modes = current_directory + '\\config_modes'
    mt = open_file('mode.txt', True).strip()
    if mt == '':
        mt = ' '
    cur_config = mt.split('/')[-1]
    directory_files = os.listdir(cfg_modes)

    cfgs = [df for df in directory_files if df.endswith('.json') and df.startswith('config')]

    if cur_config not in cfgs:
        cur_config = cfgs[0] if 'config_standard.json' not in cfgs else 'config_standard.json'
    root = Tk()

    root.title('Quick Word to LaTeX')

    root.geometry("500x300")
    # choices = ['GB', 'MB', 'KB']
    variable = StringVar(root)
    variable.set(cur_config)

    my_label = Label(root, text='Choose a configuration mode, then press submit.')
    my_label.pack()
    var2 = StringVar()
    options = OptionMenu(root, variable, *cfgs, command=update_desc)
    options.pack()
    starting_config = update_desc()
    # initt = initial(starting_config)

    my_label_2 = Label(root, textvariable=var2)
    my_label_2.pack()
    hide_images_state = tkinter.IntVar()
    check_btn = Checkbutton(root, text='Hide images?', variable=hide_images_state, onvalue=1, offvalue=0)
    check_btn.pack()
    # {'forbid_images': zero_one_tf(hide_images_state.get()), 'pdf_engine': options[rd.get()]}
    # pdf engine
    rd = tkinter.IntVar()
    rd.set(2)
    # rdt = lambda: print(rd.get())

    my_label_6 = Label(root, text='Choose a LaTeX compiler. Use XeLaTeX or LuaTeX if your Word file\n'
                                  'has unusual unicode characters outside equations.')
    my_label_6.pack()

    options = ['pdflatex', 'luatex', 'xelatex']
    for index in range(len(options)):
        radiobutton = tkinter.Radiobutton(root, text=options[index], value=index,
                                          variable=rd)
        radiobutton.pack()

    button = Button(root, text='Submit', command=click)
    button.pack()


    root.mainloop()
