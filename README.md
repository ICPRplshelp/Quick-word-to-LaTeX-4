# Quick word to LaTeX
A Microsoft Word to LaTeX converter which extends Pandoc 
by adding a lot of useful features and removes quirks 
that pandoc produces.

## Usage
Make sure Python 3.10 is installed on your computer.
No external packages are required, but pandoc
and LaTeX should be installed on your computer.

I've only tested this for Windows 10. I am unsure
how this works for macOS.

1. Run `main.py`.
2. Choose the Word file you want to convert when
prompted to.
3. The program will convert it and output
a PDF in the same directory as `main.py`.

You should look at the [Wiki](https://github.com/ICPRplshelp/Quick-word-to-LaTeX-4/wiki)
if you want to make the most use of this program.

## Common reasons of errors
If the program breaks midway without compiling the ``.tex`` file,
it means something wrong happened when fixing the ``.tex`` file.
Try to trace to where that error occurred, and submit an issue.

If the program is able to attempt to compile the ``.tex`` file
into a PDF, and the PDF compiler breaks midway, check to see
if your `*.docx` has the following, because these prevent
proper compilation:

- Nested tables
- Lists in tables if config is set to strict
- Unicode characters not in equations, if the compiler is pdfLaTeX
- Equations in headings
- Footnotes in tables, if the config is set to strict
- Images that aren't inline
- Underbars or any under-accent in equations