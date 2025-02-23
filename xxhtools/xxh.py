import argparse
import xxhtools.file_utils.file_utils as fu
import os
import re
import time


def file_output(path: str,
                fileoutput_name: str,
                is_recursive: bool,
                is_verbose: bool) -> None:
    """
    Create a file (`fileoutput_name`) with the output of the xxHash64 hashes
    of the files in the paths provided by the user.
    """
    starting_time: float = time.time()
    hashed_files: set[str] = previously_hashed_files(fileoutput_name)
    paths = fu.paths_info(path, hashed_files, is_recursive)
    if os.path.exists(fileoutput_name):
        if not fu.is_appendable_file(fileoutput_name):
            fu.print_error("file_output: "
                           f"the path '{fileoutput_name}' "
                            "exists and is not appendable", True)
        file_handler_type: str = "a"
    else:
        file_handler_type: str = "w"
    with open(fileoutput_name, file_handler_type) as file_handler:
        current_bytes: int = 0
        current_file: int = 0
        total_bytes: int  = paths["total_bytes"]
        total_files: int = paths["file_count"]
        absolute_path: str = ""
        for file in paths["files"]:
            absolute_path = os.path.abspath(file)
            current_file += 1
            current_bytes += os.path.getsize(file)
            if file in hashed_files:
                continue
            file_handler.write(f"{fu.xxh(file)}  {absolute_path}\n")
            fu.show_status(current_bytes, current_file,
                           total_bytes, total_files)
        if is_verbose:
            end_time: float = time.time()
            verbose_report(end_time - starting_time,
                           current_file, current_bytes)


def fileoutput_report(file_name: str = "",
                      file_count: int = 0,
                      total_bytes:int = 0) -> None:
    """
    Print a report with the file name where the output is being written, the
    total number of files to process and the total bytes to process.
    """
    if file_name:
        print(f"Writing output to file: {file_name}")
    print(f"Total files to process: {file_count:,}")
    print("Total bytes to process: ", end="")
    print(fu.bytes_to_human_str(total_bytes))


def previously_hashed_files(file_name: str) -> set[str]:
    """
    Return a set with the files that have already been hashed in the file
    `file_name`.
    """
    RE_HASH: str = r"^[0-9a-f]{16}  "
    hashed_files: set = set()
    if fu.is_readable_file(file_name):
        with open(file_name, "r") as f:
            for line in f:
                if re.match(RE_HASH, line):
                    hashed_files.add(line[16:].strip())
    return hashed_files


def read_args() -> argparse.Namespace:
    """
    Read the arguments provided by the user and return them.
    """
    arg_parser: argparse.ArgumentParser = argparse.ArgumentParser(
        prog="xxh",
        description=("Calculate the 64-bit xxHash3 of a file "
                     "or all files in a directory. Only non-link and readable "
                     "paths are processed."),
        epilog="written by Rodrigo Viana Rocha")
    arg_parser.add_argument(
        "path",
        help="path to file(s) and/or directory(ies).",
        nargs="+")
    arg_parser.add_argument(
        "-f",
        "--fileoutput",
        help="output the result to file FILEOUTPUT. If the file already "
             "exists, it will append the result to the end of the file, "
             "skipping existing already calculated hashes in it. Paths in "
             "the file are stored as absolute paths.")
    arg_parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="calculate the hash of every file belonging in the directory "
             "path provided (and its subdirectories). If the path is a file, "
             "this option is ignored.")
    arg_parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="show a report of elapsed time and total processed files and "
             " bytes at the end.")
    return arg_parser.parse_args()


def standard_output(path: str,
                    is_recursive: bool,
                    is_verbose: bool) -> None:
    """
    Create an output of the xxHash64 hashes of the files in the paths provided
    by the user.
    """
    starting_time: float = time.time()
    paths = fu.paths_info(path, set(), is_recursive)
    current_bytes: int = 0
    current_file: int = 0
    for file in paths["files"]:
        current_bytes += os.path.getsize(file)
        current_file += 1
        print(f"{fu.xxh(file)}  {file}")
    if is_verbose:
        end_time: float = time.time()
        verbose_report(end_time - starting_time,
                       current_file, current_bytes)


def verbose_report(elapsed_time: int,
                   total_files: int,
                   total_bytes: int) -> None:
    """
    Print a report with the elapsed time, total processed files and total
    processed bytes.
    """
    print("-" * 40)
    print(f"Elapsed time to process: {elapsed_time:.3f} second(s)")
    print(f"Total processed files  : {total_files:,}")
    print("Total processed bytes  : ", end="")
    print(fu.bytes_to_human_str(total_bytes))
    print("-" * 40)


def main(args: argparse.Namespace | None = None) -> None:
    if not args:
        args = read_args()
    if args.fileoutput:
        file_output(args.path, args.fileoutput, args.recursive, args.verbose)
    else:
        standard_output(args.path, args.recursive, args.verbose)


if __name__ == "__main__":
    main()
