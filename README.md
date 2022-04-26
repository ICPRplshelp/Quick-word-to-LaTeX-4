# Quick word to LaTeX
A Microsoft Word to LaTeX converter which extends Pandoc 
by adding a lot of useful features and removes quirks 
that pandoc produces. The LaTeX document produced should look
**very** similar to your MS Word document.

As a warning, Heading 4s are treated 
as ``\paragraph{...}``s instead of ``\subsubsubsection{...}``s and are not
affected by the change heading level in the config.

## Requirements and Dependencies
- Make sure Python 3.10 is installed on your computer.
The best place to install python is through the
Python official website.
- You should also have Pandoc and LaTeX installed
on your computer. I strongly recommend using
**TeX Live** as your LaTeX distribution - search
it up.
- You also need some Python packages. Run
these commands once Python is installed:

```
pip install pygments
```

## Usage
Make sure Python 3.10 is installed on your computer.
Pandoc and LaTeX should be installed on your computer.
I suggest using TeX Live. I cannot guarantee
that this will work for any other LaTeX distributions.

**I've only tested this for Windows 10.** I am unsure
how this works for macOS.

1. Run `main.py`. Either through your IDE or with python directly, by opening the `.py` file with python.
2. Choose the Word file you want to convert when
prompted to.
3. The program will convert it and output
a PDF in the same directory as `main.py`.

You should look at the [documentation](https://github.com/ICPRplshelp/Quick-word-to-LaTeX-4/tree/master/Documentation)
if you want to make the most use of this program.

## CAUTION!!!
Everything from this page should be placed in its own folder. This program is able to read and write files without any save-as dialogue.
A good practice is to never drag anything directly into the folder where this program resides. You only really need to listen to this warning if you plan to drag `.pdf` or `.tex` files from this folder that were not created by this program by itself. 

## Conventions for creating MS Word documents that work well with this tool

**These are recommendations, but are not required.**

- Always use MS Word's built-in styles. Do not attempt to create fake headers by **bolding the text**.
- Consider using the WordTeX template or the Pandoc docx template if you want inline or source code
- 1x1 tables will automatically be `\begin{framed}` by this program, but you should avoid creating tables that are 2 or more columns long with only one row, due to how it will be formatted by this program. It will look ugly.
- This program can't tell the difference between colored text and non-colored text. Coloring will not show up.

## Common reasons of errors

**Avoid doing or having these in your Word document at all costs.**

- If the compiler is pdfLaTeX, Unicode characters not in equations
- Using **CTRL+B** or *CTRL+I* in the equation editor (please don't do that, use "quotation marks" to ``\text{...}`` things in equations, and use `\funcapply` to unslant functions.)
- **Nesting tables within other tables, or placing images within tables, UNLESS they are tables used to make environments.**
- Placing aligned equations in tables not used for environments

Everything else shouldn't break this program.


If the program breaks midway without compiling the ``.tex`` file,
it means something wrong happened when fixing the ``.tex`` file.
Try to trace to where that error occurred, and submit an issue.

If the program is able to attempt to compile the ``.tex`` file
into a PDF, and the PDF compiler breaks midway, check to see
if your `*.docx` has the following, because these prevent
proper compilation:
