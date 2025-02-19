import argparse
import os
import re
import xxhtools.file_utils.file_utils as fu


def add_to_list_dict(dict: dict, key: str, value: list[str]) -> None:
    """
    The `dict` is a dictionary in which the keys are strings and the values are
    lists of strings. If `key` is already in the dictionary, the `value` is
    appended to the list of values of that key, but only if the `value` is not
    already in the list. If the `key` is not in the dictionary, a new key is
    created with the `value` as the first element of the list.
    """
    if key in dict:
        if value not in dict[key]:
            dict[key].append(value)
    else:
        dict[key] = [value]


def build_hash_dict(cache_dict: dict[str, list[str]],
                    path1: str,
                    path2: str,
                    is_recursive: bool,
                    is_verbose: bool) -> dict[str, list[str]]:
    current_bytes: int = 0
    current_file: int = 0
    total_bytes: int = 0
    total_files: int = 0
    files_set: set[str] = set()
    hash_dict: dict[str, list[str]] = {}
    for path in [path1, path2]:
        files_set.clear()
        if not fu.is_readable_path(path):
            fu.print_error(f"build_hash_dict: the path '{dir}' doesn't "
                           "exist or is not readable", True)
            continue
        abs_file_path = os.path.abspath(path)
        if fu.is_readable_file(abs_file_path):
            files_set.add(abs_file_path)
        elif fu.is_readable_dir(abs_file_path):
            files_set.update(fu.all_files_in_directory(abs_file_path,
                                                       is_recursive))
    total_files += len(files_set)
    total_bytes += sum(os.path.getsize(file) for file in files_set)
    for file in files_set:
        current_bytes += os.path.getsize(file)
        current_file += 1
        if is_verbose:
            fu.show_status(current_bytes, current_file,
                            total_bytes, total_files)
        if not fu.is_readable_file(file):
            fu.print_error(f"compute_hash_dict: the file '{file}' doesn't "
                            "exist or is not readable")
            continue
        if file in cache_dict:
            xhh_hash = cache_dict[file]
        else:
            xhh_hash = fu.xxh(file)
        add_to_list_dict(hash_dict, xhh_hash, file)
    return hash_dict


def get_hashes_from_cache(cache_file: str) -> dict[str, list[str]]:
    """
    Extract the paths and respective hashes from the `cache_file` and return a
    dictionary in which keys are the files and the values are the hashes.
    """
    file_dict: dict[str, str] = dict()
    RE_LINE = re.compile(r"^(?P<hash>[0-9a-f]{16}) {2}(?P<path>.+)$")
    if not fu.is_readable_file(cache_file):
        fu.print_error(f"the cache file '{cache_file}' "
                        "doesn't exist or is not readable", True)
    with open(cache_file, "r") as f:
        for line in f:
            match: re.Match = re.match(RE_LINE, line)
            if match:
                xhh_hash = match.group("hash")
                file_path = match.group("path")
                abs_file_path = os.path.abspath(file_path)
                file_dict[abs_file_path] = xhh_hash
    return file_dict


def print_dict(dictionary: dict[str, list[str]], indent: int = 2) -> None:
    """
    Print the keys and values of the dictionary `dictionary`. First print the
    open curly bracket. Then the keys are  solely printed in a line together w
    ith the opening bracket (example:
    'a1b2c3d4e5f6h8: ['). Then each value of the list is printed in a separate
    line. Finally, the closing bracket is printed. Each line is indented by
    `indent` spaces.
    """
    print("{")
    for key, value in dictionary.items():
        print(f"{' ' * indent}'{key}': [")
        for path in value:
            print(f"{' ' * (indent * 2)}'{path}',")
        print(f"{' ' * indent}]")
    print("}")


def print_path_comparison(hash_dict: dict[str, list[str]],
                          path1: str,
                          path2: str,
                          common: set[str],
                          exclusive1: set[str],
                          exclusive2: set[str],
                          is_verbose: bool) -> None:
    """
    Print the comparison output of the paths `path1` and `path2`. The
    dictionaries `exclusive1`, `exclusive2` and `common` are the result of the
    comparison of the files in the paths by their xxHash64 hashes.
    """
    common_dict: dict[str, list[str]] = {k: v for k, v in hash_dict.items()
                                            if k in common}
    exclusive1_dict: dict[str, list[str]] = {k: v for k, v in hash_dict.items()
                                            if k in exclusive1}
    exclusive2_dict: dict[str, list[str]] = {k: v for k, v in hash_dict.items()
                                            if k in exclusive2}
    if is_verbose:
        print(f"Exclusive hashes in '{path1}' (total = {len(exclusive1):,})")
    print("<", end="")
    print_dict(exclusive1_dict)
    if is_verbose:
        print(f"Exclusive hashes in '{path2}' (total = {len(exclusive2):,})")
    print(">", end="")
    print_dict(exclusive2_dict)
    if is_verbose:
        print(f"Common hashes (total = {len(common):,})")
    print("=", end="")
    print_dict(common_dict)
    if is_verbose:
        if exclusive1 and not exclusive2:
            print(f"All files in '{path2}' are in '{path1}'.")
        elif exclusive2 and not exclusive1:
            print(f"All files in '{path1}' are in '{path2}'.")
        elif not exclusive1 and not exclusive2:
            print(f"All files in '{path1}' are in '{path2}' and vice-versa.")
        elif common:
            print(f"Some files in '{path1}' are not in '{path2}' "
                   "and vice-versa.")
        else:
            print(f"The files in '{path1}' and '{path2}' are "
                   "completely different.")


def read_args() -> argparse.Namespace:
    """
    Read the arguments provided by the user and return them.
    """
    arg_parser: argparse.ArgumentParser = argparse.ArgumentParser(
        prog="xxdiff",
        description=("Compare two paths, `path1` and `path2`, and show a "
                     "comparison of their files. The paths can be two files "
                     "or two directories. If the paths are directories, the "
                     "files inside them are compared. If the paths are files, "
                     "the hash of the files is calculated and compared. The "
                     "paths are compared by their 64-bit xxHash3. Only "
                     "non-link and readable paths are processed."),
        epilog="written by Rodrigo Viana Rocha")
    arg_parser.add_argument(
        "path1",
        help="path to a file or directory")
    arg_parser.add_argument(
        "path2",
        help="path to a file or directory, to be compared with `path1`. It "
             "must be of the same type as `path1`.")
    arg_parser.add_argument(
        "-c",
        "--cachefile",
        help="Use precomputed hashes from CACHEFILE to speed up the "
             "comparison. Each line in CACHEFILE must have the format: "
             "'<hex_hash>  <path>'. "
             "Example: 'a1b2c3d4e5f6a7b8  /path/to/file'. The quotes are "
             "not part of the format.")
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
        help="show headers for each section of the comparison output.")
    return arg_parser.parse_args()


def standard_output(hash_dict: dict[str, list[str]],
                    path1: str,
                    path2: str,
                    is_verbose: bool) -> None:
    """
    Compare the files in the paths `path1` and `path2` by their
    xxHash64 hashes and print the comparison output, considering that
    `hash_dict` has all files of both paths.
    First step: Show a dict with hashes that exclusively belong to `dir1`. For
    each hash, show as values all the paths that have that hash. Show the
    number of such hashes.
    Second step: Show a dict with hashes that exclusively belong to `dir2`. For
    each hash, show as values all the paths that have that hash. Show the
    number of such hashes.
    Third step: Show a dict with hashes that belong to both `dir1` and `dir2`.
    For each hash, show as values all the paths that have that hash. Show the
    number of such hashes.
    Fourth step: State , if possible, all files of `dir1' are also in `dir2`
    and vice-versa.
    """
    abs_path1: str = os.path.abspath(path1)
    abs_path2: str = os.path.abspath(path2)
    hash1: set[str] = set()
    hash2: set[str] = set()
    for hash, files in hash_dict.items():
        for file in files:
            if file.startswith(abs_path1):
                hash1.add(hash)
            if file.startswith(abs_path2):
                hash2.add(hash)
    common: set[str] = hash1.intersection(hash2)
    exclusive1: set[str] = hash1.difference(hash2)
    exclusive2: set[str] = hash2.difference(hash1)
    print_path_comparison(hash_dict,
                          path1,
                          path2,
                          common,
                          exclusive1,
                          exclusive2,
                          is_verbose)


def main(args: argparse.Namespace | None = None) -> None:
    if not args:
        args = read_args()

    cache_dict: dict[str, list[str]]
    if args.cachefile:
        cache_dict = get_hashes_from_cache(args.cachefile)
    else:
        cache_dict = {}

    hash_dict: dict[str, list[str]]
    both_files: bool = (fu.is_readable_file(args.path1) and
                        fu.is_readable_file(args.path2))
    both_dirs: bool = (fu.is_readable_dir(args.path1) and
                       fu.is_readable_dir(args.path2))
    if not (both_files or both_dirs):
        fu.print_error("the paths provided must be of the same type (both "
                       "files or both directories) and must be readable", True)
    hash_dict = build_hash_dict(cache_dict, args.path1, args.path2,
                               args.recursive, args.verbose)
    standard_output(hash_dict, args.path1, args.path2, args.verbose)


if __name__ == "__main__":
    main()
