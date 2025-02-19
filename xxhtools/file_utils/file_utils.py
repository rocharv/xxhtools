import os
from xxhash import xxh3_64


def all_files_in_directory(path: str, is_recursive: bool) -> set[str]:
    """
    Return a list with all files in the `path` provided and its subdirectories
    (if `is_recursive` is True).
    """
    all_files: set[str] = set()
    for root, _, files in os.walk(path):
        for file in files:
            all_files.add(os.path.join(root, file))
        if not is_recursive:
            break
    return all_files


def bytes_to_human_str(bytes: int) -> str:
    """
    Return a human readable string of the number of `bytes` provided.
    """
    prefix: list[str] = ["K", "M", "G", "T"]
    multiplier: list[int] = [1_048_576, 1_073_741_824,
                             1_099_511_627_776, 1_125_899_906_842_624]
    if bytes < 1024:
            return f"{bytes:,} B"
    for i, m in enumerate(multiplier):
        if bytes < m:
            return f"{bytes / (multiplier[i] / 1_024):,.1f} {prefix[i]}B"
    return f"{bytes / multiplier[-1]:,.1f} PB"


def is_appendable_file(file_name: str) -> bool:
    """
    Check if the `file_name` can be read, written and is not a symbolic link.
    """
    is_file: bool = os.path.isfile(file_name)
    file_is_link: bool = os.path.islink(file_name)
    file_is_readble: bool = os.access(file_name, os.R_OK)
    file_is_writable: bool = os.access(file_name, os.W_OK)
    return (
        is_file and not file_is_link and
        file_is_readble and file_is_writable)


def is_readable_dir(dir_name: str) -> bool:
    """
    Check if the `file_name` can be read and is not a symbolic link.
    """
    is_dir: bool = os.path.isdir(dir_name)
    dir_is_link: bool = os.path.islink(dir_name)
    dir_is_readble: bool = os.access(dir_name, os.R_OK)
    return is_dir and not dir_is_link and dir_is_readble


def is_readable_file(file_name: str) -> bool:
    """
    Check if the `file_name` can be read and is not a symbolic link.
    """
    is_file: bool = os.path.isfile(file_name)
    file_is_link: bool = os.path.islink(file_name)
    file_is_readble: bool = os.access(file_name, os.R_OK)
    return is_file and not file_is_link and file_is_readble


def is_readable_path(path: str) -> bool:
    """
    Check if the `path` can be read and is not a symbolic link.
    """
    path_is_link: bool = os.path.islink(path)
    path_is_readble: bool = os.access(path, os.R_OK)
    return not path_is_link and path_is_readble


def paths_info(paths: str,
               exclude_set: set[str] = [],
               is_recursive: bool = True) -> dict[str, int | list[str]]:
    """
    Return a dictionary with the following information (keys) about the
    `paths` provided and its subdirectories (if `is_recursive` is True):
    - `files`: list of all files in the paths, excluding the ones in the
               `exclude_set`
    - `file_count`: total number of files in the paths
    - `total_bytes`: total size of all files in the paths
    """
    info: dict[str, int] = {"files": set(), "file_count": 0, "total_bytes": 0}
    for path in paths:
        if not is_readable_path(path):
            print_error(f"paths_info: the path '{path}' doesn't exist or "
                         "is not readable")
            continue
        if os.path.isfile(path):
            info["files"].add(path)
            info["file_count"] += 1
            info["total_bytes"] += os.path.getsize(path)
        else:
            for file in all_files_in_directory(path, is_recursive):
                if not is_readable_file(file) or file in exclude_set:
                    continue
                info["files"].add(file)
                info["file_count"] += 1
                info["total_bytes"] += os.path.getsize(file)
    return info


def print_error(message: str, halt: bool = False) -> None:
    """
    Print an error message and return False.
    """
    print(f"Error: {message}.")
    if halt:
        raise SystemExit(1)


def show_status(current_bytes: int,
                current_file: int,
                total_bytes: int,
                total_files: int,
                each_file: int = 100) -> None:
    """
    Print, every `each_file` files, a status with the current number of files
    processed, the total bytes processed and the percentage of total bytes
    processed.
    """
    if current_file == 1:
        print(f"Files to process: {total_files:,}")
        print("Bytes to process: ", end="")
        print(bytes_to_human_str(total_bytes))
    if total_files // each_file > 0:
        trigger: bool = current_file % (total_files // each_file) == 0
    else:
        trigger: bool = False
    if trigger:
        print(f"Processed: {current_file:,} files, "
            f"{bytes_to_human_str(current_bytes)} "
            f"({(current_bytes / total_bytes):.1%})       ", end="\r")


def xxh(file_name: str) -> str:
    """
    Return the xxHash64 hash of the file `file_name`.
    """
    if is_readable_file(file_name):
        hash_object: xxh3_64 = xxh3_64()
        with open(file_name, "rb") as f:
            for chunk in iter(lambda: f.read(1024), b""):
                hash_object.update(chunk)
        return hash_object.hexdigest()
    print_error(f"xxh: the target file, '{file_name}', doesn't exist,"
                 "or is not a file")
    return ""
