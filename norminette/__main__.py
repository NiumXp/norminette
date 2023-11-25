import glob
import os
import sys
from importlib.metadata import version

import argparse
from norminette.lexer import TokenError
from norminette.exceptions import CParsingError
from norminette.registry import Registry
from norminette.context import Context
from norminette.tools.colors import colors
from norminette.file import File

from pathlib import Path

import subprocess


has_err = False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "file",
        help="File(s) or folder(s) you wanna run the parser on. If no file provided, runs on current folder.",
        nargs="*",
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="count",
        help="Debug output (-dd outputs the whole tokenization and such, used for developping)",
        default=0,
    )
    parser.add_argument(
        "-o",
        "--only-filename",
        action="store_true",
        help="By default norminette displays the full path to the file, this allows to show only filename",
        default=False,
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version="norminette " + version("norminette"),
    )
    parser.add_argument(
        "--cfile",
        action="store",
        help="Store C file content directly instead of filename",
    )
    parser.add_argument(
        "--hfile",
        action="store",
        help="Store header file content directly instead of filename",
    )
    parser.add_argument(
        "--filename",
        action="store",
        help="Stores filename if --cfile or --hfile is passed",
    )
    parser.add_argument(
        "--use-gitignore",
        action="store_true",
        help="Parse only source files not match to .gitignore",
    )
    parser.add_argument("-R", nargs=1, help="compatibility for norminette 2")
    args = parser.parse_args()
    registry = Registry()
    has_err = None

    files = []
    debug = args.debug
    if args.cfile is not None or args.hfile is not None:
        filename = args.filename or (args.cfile and "file.c") or (args.hfile and "file.h")
        file = File(filename, args.cfile or args.hfile)
        files.append(file)
    else:
        paths = []
        bases = [''] if not args.file else []
        for arg in args.file:
            if not os.path.exists(arg):
                return print(f"Error: '{arg}' no such file or directory")
            if os.path.isdir(arg):
                bases.append(arg.rstrip('/') + '/')
            if os.path.isfile(arg):
                paths.append(arg)
        for base in bases:
            result = glob.glob(base + "**/*.[ch]", recursive=True)
            paths.extend(result)
        for filepath in paths:
            if not os.access(filepath, os.R_OK):
                print("Error: File could not be read")
                return 1
            if filepath[-2:] not in (".c", ".h"):
                return print(f"Error: {filepath} is not valid C or C header file")
            with open(filepath, mode='r') as stream:
                if args.only_filename:
                    filepath = Path(filepath).name
                file = File(filepath, stream.read())
                files.append(file)

    if args.use_gitignore:
        tmp_targets = []
        for file in files:
            command = ["git", "check-ignore", "-q", file.path]
            exit_code = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode
            """
            see: $ man git-check-ignore
            EXIT STATUS
                  0: One or more of the provided paths is ignored.
                  1: None of the provided paths are ignored.
                128: A fatal error was encountered.
            """
            if exit_code == 0:
                pass
            elif exit_code == 1:
                tmp_targets.append(file)
            elif exit_code == 128:
                print(f'Error: something wrong with --use-gitignore option {file.path}')
                sys.exit(0)
        files = tmp_targets
    for file in files:
        try:
            context = Context(file, debug, args.R)
            registry.run(context)
            has_err = bool(context.errors)
        except (TokenError, CParsingError) as e:
            print(file.path + f": Error!\n\t{colors(e.msg, 'red')}")
            return 1
        except KeyboardInterrupt:
            return 1
    return int(has_err or 0)


if __name__ == "__main__":
    sys.exit(main())
