"""This is used for generating environments.
"""
import time


def input_environment_entries(env_name: str) -> str:
    """Input all environment entries.
    """
    print(f'Your environment name is {env_name}\n')
    extra_args_string = input('An environment may have extra arguments to it that can be\n'
                              ' specified in MS Word. Should'
                              ' it be wrapped in [brackets] \nor {braces}? Input brackets/braces/none,'
                              ' default is brackets.\n')
    extra_args_type = 'brace' if extra_args_string.startswith('brace') else 'bracket'
    no_extra_args = extra_args_string.startswith('none')
    if not no_extra_args:
        print(f'You entered {extra_args_type}')
    else:
        print('You entered no extra args\n')
    if not no_extra_args:
        middle_fix = input('Does your environment have optional commands that must be called\n'
                           ' everytime it appears in the LaTeX file? For example, you might\n'
                           ' always want an environment declaration to start like this:\n'
                           ' \\begin{sample}[size=15]. If so, enter it here, or\n'
                           ' leave BLANK to avoid. Your answer should be wrapped \n'
                           'in square brackets. If you don\'t, then it will be\n'
                           ' discarded.\n')
        print(f'You entered {middle_fix}')
        if middle_fix == '':
            print('You didn\'t state one, so it will not be applied here. \n')
        elif not (middle_fix.startswith('[') and middle_fix.endswith(']')):
            print('You didn\'t enter something wrapped with square [] brackets, so it \nis'
                  ' being discarded.')
            middle_fix = ''
        if middle_fix != '' and extra_args_type == 'bracket':
            print('Becuase your extra argument type is set to [bracket] and you have also set up\n'
                  ' an optional environment, all arguments specified in MS Word will be discarded.')
    else:
        middle_fix = ''
        print('All extra arguments for this environment will be\n discarded if stated '
              'in Microsoft Word.\n')
    start_alt = input('Would you like alias this environment? This will change how it is\n '
                      'called in Microsoft word, but the declaration will remain\n'
                      ' the same in LaTeX. Leave BLANK to avoid.\n')
    if '!' in start_alt:
        print('You entered something with an !, so we are discarding it.\n')
        start_alt = ''
    elif start_alt.strip() != '':
        print(f'You entered {start_alt}\n')
        start_alt += '!'
    else:
        print('You did not state an alias.\n')

    suffix = input('Do you want to add text after an environment declaration? This is useful\n'
                   ' if there are more than one mandatory argument for the environment\n'
                   ' you are dealing with. If so, state it here, or leave it blank otherwise.\n')

    return create_environment_entry(env_name, extra_args_type, start_alt, middle_fix, suffix)


def create_environment_entry(env_name: str, extra_args_type: str, start_alt: str, middle_fix: str,
                             suffix: str) -> str:
    """The inverse function to unpack_environment_list.
    Inputs:
        - env_name
        - extra_args_type
        - start_alt
        - middle_fix
    """
    extra_args_type = '[]' if extra_args_type == 'bracket' else '{}'
    return start_alt + env_name + middle_fix + extra_args_type + suffix


if __name__ == '__main__':
    env_name_main = input('What is the name of your environment?\n')
    print('The text to add to the list of environments is stated below.')
    print(input_environment_entries(env_name_main))
    print('\n This program will close in 10 seconds. Copy what was shown above.')
    time.sleep(10)
