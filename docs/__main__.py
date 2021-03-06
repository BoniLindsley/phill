# Standard libraries.
import inspect
import pathlib
import shutil
import sys

# External dependencies.
import sphinx.cmd.build

if __name__ == "__main__":
    # Figure out where the source file is, regardless of PWD.
    script_path_string = inspect.getsourcefile(lambda: None)
    if script_path_string is None:
        raise RuntimeError("Unable to determine script path.")
    assert script_path_string is not None
    script_file_path = pathlib.Path(script_path_string)
    docs_directory_path = script_file_path.resolve().parent
    build_directory_path = docs_directory_path / "_build"
    # Process the command line arguments the same way `Makefile` does.
    # Use `-M` to indicate it is a `Makefile`.
    # Forward all arguments to `main`.
    # Only one argument is expected, and it defaults to `help`.
    arguments = sys.argv.copy()
    arguments[0] = "-M"
    if len(arguments) == 1:
        arguments.append("help")
    # And then append documentation source and build directories.
    arguments.append(str(docs_directory_path))
    arguments.append(str(build_directory_path))
    # This lets us run Sphinx without `Makefile`.
    return_value = sphinx.cmd.build.main(arguments)
    # Clean up auto-generated files if build output is empty.
    if build_directory_path.is_dir():
        # pylint: disable=invalid-name
        is_build_directory_empty = False
        try:
            next(build_directory_path.iterdir())
        except StopIteration:
            is_build_directory_empty = True
        if is_build_directory_empty:
            generate_directory = (
                docs_directory_path / "autosummary_generate"
            )
            try:
                shutil.rmtree(generate_directory)
            except FileNotFoundError:
                pass
    sys.exit(return_value)
