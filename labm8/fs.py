"""High level filesystem interface.
"""
import contextlib
import os
import os.path
import pathlib
import re
import shutil
import tempfile
import typing
from glob import iglob

from humanize import naturalsize
from send2trash import send2trash

from labm8 import labtypes


class Error(Exception):
  pass


class File404(Error):
  pass


def path(*components):
  """
  Get a file path.

  Concatenate all components into a path.
  """
  _path = os.path.join(*components)
  _path = os.path.expanduser(_path)

  return _path


def must_exist(*components):
  """
  Ensure path exists.

  Arguments:
      *components (str[]): Path components.

  Returns:
      str: File path.

  Raises:
      File404: If path does not exist.
  """
  _path = path(*components)
  if not exists(_path):
    raise File404(_path)
  return _path


def abspath(*components):
  """
  Get an absolute file path.

  Concatenate all components into an absolute path.
  """
  return os.path.abspath(path(*components))


def basename(*components):
  """
  Return the basename of a given file path.
  """
  return os.path.basename(path(*components))


def dirname(*components):
  """
  Return the directory name of a given file path.
  """
  return os.path.dirname(path(*components))


def is_subdir(child, parent):
  """
  Determine if "child" is a subdirectory of "parent".

  If child == parent, returns True.
  """
  child_path = os.path.realpath(child)
  parent_path = os.path.realpath(parent)

  if len(child_path) < len(parent_path):
    return False

  for i in range(len(parent_path)):
    if parent_path[i] != child_path[i]:
      return False

  return True


# Directory history.
_cdhist = []


def cd(path):
  """
  Change working directory.

  Returns absolute path to new working directory.
  """
  _cdhist.append(pwd())  # Push to history.
  path = abspath(path)
  os.chdir(path)
  return path


def cdpop():
  """
  Return the last directory.

  Returns absolute path to new working directory.
  """
  if len(_cdhist) >= 1:
    old = _cdhist.pop()  # Pop from history.
    os.chdir(old)
    return old
  else:
    return pwd()


def pwd():
  """
  Return the path to the current working directory.
  """
  return os.getcwd()


def exists(*components):
  """
  Return whether a file exists.
  """
  return os.path.exists(path(*components))


def isfile(*components):
  """
  Return whether a path exists, and is a file.
  """
  return os.path.isfile(path(*components))


def isexe(*components):
  """
  Return whether a path is an executable file.

  Arguments:
    path (str): Path of the file to check.

  Examples:
    >>> isexe("/bin/ls")
    True

    >>> isexe("/home")
    False

    >>> isexe("/not/a/real/path")
    False

  Returns:
      bool: True if file is executable, else false.
  """
  _path = path(*components)
  return isfile(_path) and os.access(_path, os.X_OK)


def isdir(*components):
  """
  Return whether a path exists, and is a directory.
  """
  if components:
    return os.path.isdir(path(*components))
  else:
    return False


def ls(root: typing.Union[str, pathlib.Path] = ".",
       abspaths=False,
       recursive=False):
  """
  Return a list of files in directory.

  Directory listings are sorted alphabetically. If the named
  directory is a file, return it's path.

  Examples:
    >>> ls("foo")
    ["a", "b", "c"]

    >>> ls("foo/a")
    ["foo/a"]

    >>> ls("foo", abspaths=True)
    ["/home/test/foo/a", "/home/test/foo/b", "/home/test/foo/c"]

    >>> ls("foo", recursive=True)
    ["a", "b", "b/d", "b/d/e", "c"]

  Arguments:
    root (str): Path to directory. Can be relative or absolute.
    abspaths (bool, optional): Return absolute paths if true.
    recursive (bool, optional): Recursively list subdirectories if
      true.

  Returns:
    list of str: A list of paths.

  Raises:
    OSError: If root directory does not exist.
  """

  def _expand_subdirs(file):
    if isdir(path(root, file)):
      return [file
             ] + [path(file, x) for x in ls(path(root, file), recursive=True)]
    else:
      return [file]

  if isfile(root):
    # If argument is a file, return path.
    return [abspath(root)] if abspaths else [basename(root)]
  elif abspaths:
    # Get relative names.
    relpaths = ls(root, recursive=recursive, abspaths=False)
    # Prepend the absolute path to each relative name.
    base = abspath(root)
    return [path(base, relpath) for relpath in relpaths]
  elif recursive:
    # Recursively expand subdirectories.
    paths = ls(root, abspaths=abspaths, recursive=False)
    return labtypes.flatten([_expand_subdirs(file) for file in paths])
  else:
    # List directory contents.
    return list(sorted(os.listdir(root)))


def lsdirs(root=".", **kwargs):
  """
  Return only subdirectories from a directory listing.

  Arguments:

      root (str): Path to directory. Can be relative or absolute.
      **kwargs: Any additional arguments to be passed to ls().

  Returns:

      list of str: A list of directory paths.

  Raises:

      OSError: If root directory does not exist.
  """
  paths = ls(root=root, **kwargs)
  if isfile(root):
    return []
  return [_path for _path in paths if isdir(path(root, _path))]


def lsfiles(root: typing.Union[str, pathlib.Path] = ".", **kwargs):
  """
  Return only files from a directory listing.

  Arguments:

      root (str): Path to directory. Can be relative or absolute.
      **kwargs: Any additional arguments to be passed to ls().

  Returns:

      list of str: A list of file paths.

  Raises:

      OSError: If root directory does not exist.
  """
  paths = ls(root=root, **kwargs)
  if isfile(root):
    return paths
  return [_path for _path in paths if isfile(path(root, _path))]


def rm(*components, **kwargs):
  """
  Remove a file or directory.

  If path is a directory, this recursively removes the directory and
  any contents. Non-existent paths are silently ignored.

  Supports Unix style globbing by default (disable using
  glob=False). For details on globbing pattern expansion, see:

      https://docs.python.org/2/library/glob.html

  Arguments:
      *components (string[]): path to the file or directory to remove. May be
        absolute or relative. May contain unix glob
      **kwargs: if "glob" is True, perform Unix style pattern expansion of
        paths (default: True).
  """
  _path = path(*components)
  glob = kwargs.get("glob", True)
  paths = iglob(_path) if glob else [_path]

  for file in paths:
    if isfile(file):
      os.remove(file)
    elif exists(file):
      shutil.rmtree(file, ignore_errors=False)


def rmtrash(*components):
  """
  Move a file or directory to trash.

  If file does not exist, nothing happens.

  Examples:

      >>> rmtrash("foo", "bar")

      >>> rmtrash("/home/labm8/file.txt")

  Arguments:
      *components (string[]): path to the file or directory.
  """
  _path = path(*components)
  if exists(_path):
    send2trash(_path)


def cp(src, dst):
  """
  Copy a file or directory.

  If source is a directory, this recursively copies the directory
  and its contents. If the destination is a directory, then this
  creates a copy of the source in the destination directory with the
  same basename.

  If the destination already exists, this will attempt to overwrite
  it.

  Arguments:

      src (string): path to the source file or directory.
      dst (string): path to the destination file or directory.

  Raises:

      IOError: if source does not exist.
  """
  if isdir(src):
    # Overwrite an existing directory.
    if isdir(dst):
      rm(dst)
    shutil.copytree(src, dst)
  elif isfile(src):
    shutil.copy(src, dst)
  else:
    raise IOError("Source '{0}' not found".format(src))


def mv(src, dst):
  """
  Move a file or directory.

  If the destination already exists, this will attempt to overwrite
  it.

  Arguments:

      src (string): path to the source file or directory.
      dst (string): path to the destination file or directory.

  Raises:

      File404: if source does not exist.
      IOError: in case of error.
  """
  if not exists(src):
    raise File404(src)

  try:
    shutil.move(src, dst)
  except Exception as e:
    raise IOError(str(e))


def mkdir(*components, **kwargs):
  """
  Make directory "path", including any required parents. If
  directory already exists, do nothing.
  """
  _path = path(*components)
  if not isdir(_path):
    os.makedirs(_path, **kwargs)
  return _path


def mkopen(p, *args, **kwargs):
  """
  A wrapper for the open() builtin which makes parent directories if needed.
  """
  dir = os.path.dirname(p)
  mkdir(dir)
  return open(p, *args, **kwargs)


def read(*components, **kwargs):
  """
  Read file and return a list of lines. If comment_char is set, ignore the
  contents of lines following the comment_char.

  Raises:

      IOError: if reading path fails
  """
  rstrip = kwargs.get("rstrip", True)
  comment_char = kwargs.get("comment_char", None)

  ignore_comments = comment_char is not None

  file = open(path(*components))
  lines = file.readlines()
  file.close()

  # Multiple definitions to handle all cases.
  if ignore_comments:
    comment_line_re = re.compile("^\s*{char}".format(char=comment_char))
    not_comment_re = re.compile("[^{char}]+".format(char=comment_char))

    if rstrip:
      # Ignore comments, and right strip results.
      return [
          re.match(not_comment_re, line).group(0).rstrip()
          for line in lines
          if not re.match(comment_line_re, line)
      ]
    else:
      # Ignore comments, and don't strip results.
      return [
          re.match(not_comment_re, line).group(0)
          for line in lines
          if not re.match(comment_line_re, line)
      ]
  elif rstrip:
    # No comments, and right strip results.
    return [line.rstrip() for line in lines]
  else:
    # Just a good old-fashioned read!
    return lines


def du(*components, **kwargs):
  """
  Get the size of a file in bytes or as a human-readable string.

  Arguments:

      *components (str[]): Path to file.
      **kwargs: If "human_readable" is True, return a formatted string,
        e.g. "976.6 KiB" (default True)

  Returns:
      int or str: If "human_readble" kwarg is True, return str, else int.
  """
  human_readable = kwargs.get("human_readable", True)

  _path = path(*components)
  if not exists(_path):
    raise Error("file '{}' not found".format(_path))
  size = os.stat(_path).st_size
  if human_readable:
    return naturalsize(size)
  else:
    return size


def write_file(path, contents):
  """
  Write string to file.

  Arguments:
      path (str): Destination.
      contents (str): Contents.
  """
  with mkopen(path, 'w') as outfile:
    outfile.write(contents)


def read_file(path):
  """
  Read file to string.

  Arguments:
      path (str): Source.
  """
  with open(must_exist(path)) as infile:
    r = infile.read()
  return r


def files_from_list(*paths):
  """
  Return a list of all file paths from a list of files or directories.

  For each path in the input: if it is a file, return it; if it is a
  directory, return a list of files in the directory.

  Arguments:
      paths (list of str): List of file and directory paths.

  Returns:
      list of str: Absolute file paths.

  Raises:
      File404: If any of the paths do not exist.
  """
  ret = []
  for path in paths:
    if isfile(path):
      ret.append(abspath(path))
    elif isdir(path):
      ret += [f for f in ls(path, abspaths=True, recursive=True) if isfile(f)]
    else:
      raise File404(path)
  return ret


def directory_is_empty(directory: pathlib.Path) -> bool:
  """Return if a directory is empty.

  A directory which does not exist is considered empty (returns True). A
  directory containing only subdirectories but no files is considered not empty
  (returns False).

  Args:
    directory: The path of a directory.

  Returns:
    True if directory is empty, else False.
  """
  for _, subdirs, files in os.walk(path(directory)):
    if subdirs or files:
      return False
  return True


@contextlib.contextmanager
def chdir(directory: typing.Union[str, pathlib.Path]) -> pathlib.Path:
  """A context manager which allows you to temporarily change working directory.

  Args:
    directory: The directory to change to.

  Returns:
    The directory which has been changed to.

  Raises:
    OSError: If the given directory does not exist.
    NotADirectoryError: If the given path is a file.
  """
  previous_directory = pathlib.Path.cwd()
  os.chdir(str(directory))
  try:
    yield pathlib.Path(directory)
  finally:
    os.chdir(str(previous_directory))


@contextlib.contextmanager
def TemporaryWorkingDir(prefix: str = 'phd_') -> pathlib.Path:
  """A context manager which provides a temporary working directory.

  This creates an empty temporary directory, and changes the current working
  directory to it. Once out of scope, the directory and all it's contents are
  removed.

  Args:
    prefix: A prefix for the temporary directory name.

  Returns:
    The directory which has been changed to.
  """
  # getcwd() will raise FileNotFoundError if the current workind directory
  # does not exist.
  old_directory = None
  try:
    old_directory = os.getcwd()
  except FileNotFoundError:
    pass
  # Create a temporary directory, change to it, and return the path to the user.
  with tempfile.TemporaryDirectory(prefix=prefix) as d:
    os.chdir(d)
    yield pathlib.Path(d)
  # Rever to previous working directory, if there was one.
  if old_directory:
    os.chdir(old_directory)
