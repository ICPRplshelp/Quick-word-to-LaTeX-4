# Quick word to LaTeX

A Microsoft Word to LaTeX converter which extends Pandoc 
by adding a lot of useful features and removes quirks 
that pandoc produces. The LaTeX document produced should look
**very** similar to your MS Word document.

This is **NOT** a Pandoc filter. If you want a Pandoc filter that ports some features
from this repo, click [Here](https://github.com/ICPRplshelp/MS-Word-Pandoc-Filters).

As a warning, Heading 4s are treated 
as ``\paragraph{...}``s instead of ``\subsubsubsection{...}``s and are not
affected by the change heading level in the config.

## Requirements and Dependencies

- Make sure Python 3.10 is installed on your computer.
The best place to install python is through the
Python official website. Things can go wrong if you install Python through the Windows 10 store.
- You should also have Pandoc and LaTeX installed
on your computer. I strongly recommend using
**TeX Live** as your LaTeX distribution - search
it up.
- You also need some Python packages. Run
these commands once Python is installed:

```
pip install pygments
```

(Note: Sometimes, you may have PATH variables mixed up. The best way to fix them is by reinstalling python from the python website.)

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

You should look at the [documentation](https://github.com/ICPRplshelp/Quick-word-to-LaTeX-4/tree/master/documentation)
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

- Nested tables (not used for environments)
- Images in tables (not used for environments)

## Features shorthand

### Environments

On a new paragraph, if you type something with this syntax (where only the words `Definition`, `Term` and `The definition of the term.` can be switched out):

> **Definition.** (Term). The definition of the term.

It will translate to the following in LaTeX:

```tex
\begin{definition}[Term]
    The definition of the term.
\end{definition}
```

The environment stops on the next paragraph. If the next paragraph is an equation, the environment will stop at the paragraph after the equation. However,
if the first character of the next paragraph, excluding leading spaces, is lowercase, then the next paragraph will be included in the environment (and so on). Lists will not stop environments, and will end after the list.

**Only certain environments will work with this.**  The ones I know that will work is *Definition, Theorem, and Lemma.* You should check the [wiki](https://github.com/ICPRplshelp/Quick-word-to-LaTeX-4/wiki/Proofs-and-Environments) if you want to know what environments are supported.

### Numbering equations

Equations numbered/commented in Microsoft Word that are **flushed-right** will be accounted for. ``#`` is the delimiter to number equations - just type `#` and your comment, and press space. Your comment should be wrapped in (circular brackets). If you don't, this program will add it for you.

**Equation numbering/comments must be alphanumeric and must work in `\label` (the comment will be dropped if it isn't), though you may wrap equation text in "quotes" to unitalicize them.** To reference equations, just type ``equation <##>`` where `<##>` is your comment (Equation is not case-sensitive) without circular brackets wrapped around it. The numbering you type in MS Word will be
the one that shows up in your LaTeX document, though there is a configuration option available to have them always numbered in order.

### Figures and Numbering tables

**[READ THE WIKI FOR INFORMATION ON THIS](https://github.com/ICPRplshelp/Quick-word-to-LaTeX-4/wiki/Figure-and-Table-numbering)**


### Proofs

Proofs work differently from environments. **READ THE [WIKI](https://github.com/ICPRplshelp/Quick-word-to-LaTeX-4/wiki/Proofs-and-Environments)!!!**
