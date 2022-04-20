# Quick word to LaTeX
A Microsoft Word to LaTeX converter which extends Pandoc 
by adding a lot of useful features and removes quirks 
that pandoc produces.

## Usage
Make sure Python 3.10 is installed on your computer.
**No external packages are required,** but pandoc
and LaTeX should be installed on your computer.
I suggest using TeX Live. I cannot guarantee
that this will work for any other LaTeX distributions.

**I've only tested this for Windows 10.** I am unsure
how this works for macOS.

1. Run `main.py`. Either through your IDE or with python directly, by opening the `.py` file with python.
2. Choose the Word file you want to convert when
prompted to.
3. The program will convert it and output
a PDF in the same directory as `main.py`.

You should look at the [Wiki](https://github.com/ICPRplshelp/Quick-word-to-LaTeX-4/wiki)
if you want to make the most use of this program.

## CAUTION!!!
Everything from this page should be placed in its own folder. This program is able to read and write files without any save-as dialogue.
A good practice is to never drag anything directly into the folder where this program resides. You only really need to listen to this warning if you plan to drag `.pdf` or `.tex` files from this folder that were not created by this program by itself. 

## Conventions for creating MS Word documents that work well with this tool

- Always use MS Word's built-in styles. Do not attempt to create fake headers by **bolding the text**.
- Consider using the WordTeX template or the Pandoc docx template if you want inline or source code
- Read the *common reasons for errors*
- 1x1 tables will automatically be `\begin{framed}` by this program, but you should avoid creating tables that are 2 or more columns long with only one row, due to how it will be formatted by this program.

## Common reasons of errors
If the program breaks midway without compiling the ``.tex`` file,
it means something wrong happened when fixing the ``.tex`` file.
Try to trace to where that error occurred, and submit an issue.

If the program is able to attempt to compile the ``.tex`` file
into a PDF, and the PDF compiler breaks midway, check to see
if your `*.docx` has the following, because these prevent
proper compilation:

- Unicode characters not in equations
- Equations in headings
- Using **CTRL+B** or *CTRL+I* in the equation editor (please don't do that, use "quotation marks" to ``\text{...}`` things in equations)
- Images that aren't inline
