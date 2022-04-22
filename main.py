import json
import os
import converter as conv
from tkinter import Button, Label, StringVar, OptionMenu, Tk


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


def read_json(json_dir: str) -> str:
    with open(json_dir) as json_file:
        data = json.load(json_file)
    data_dict = dict(data)
    description = data_dict.get('description', 'No description provided.')
    return description


def update_desc(*args) -> None:
    sv = variable.get()
    np = 'config_modes\\' + sv
    desc = read_json(np)
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


def click() -> None:
    sv = variable.get()
    root.destroy()

    np = 'config_modes\\' + sv
    np2 = 'config_modes/' + sv
    print(np)
    write_file(np2, 'mode.txt')
    conv.main(np)


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

    root.geometry("500x200")
    # choices = ['GB', 'MB', 'KB']
    variable = StringVar(root)
    variable.set(cur_config)

    my_label = Label(root, text='Choose a configuration mode, then press submit.')
    my_label.pack()
    var2 = StringVar()
    options = OptionMenu(root, variable, *cfgs, command=update_desc)
    options.pack()
    update_desc()

    my_label_2 = Label(root, textvariable=var2)

    button = Button(root, text='Submit', command=click)
    button.pack()
    my_label_2.pack()

    root.mainloop()
