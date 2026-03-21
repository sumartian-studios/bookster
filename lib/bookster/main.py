# Bookster: A simple command-line tool to manage book writing projects, including chapter organization and compilation using Pandoc.

import os
import re
import pathlib
import sys
import argparse
import shlex
import subprocess
import shutil

from contextlib import contextmanager, nullcontext
from importlib import resources

FILENAME_PATTERN = re.compile(r"chapter-(\d+)\.md")


def get_asset_path(filename):
    """Locates bundled data files inside the package."""
    pkg_resource = resources.files("bookster").joinpath("data").joinpath(filename)
    with resources.as_file(pkg_resource) as path:
        return str(path)


def get_chapter_files(target_dir):
    """Return a sorted list of (chapter_number, filename) tuples."""
    files = []
    if not os.path.isdir(target_dir):
        print(f"Error: Directory '{target_dir}' not found.")
        sys.exit(1)

    for f in os.listdir(target_dir):
        match = FILENAME_PATTERN.match(f)
        if match:
            files.append((int(match.group(1)), f))

    files.sort(key=lambda x: x[0])
    return files


def run_shift(target_dir, pivot, step, create_new=False, confirm=True, dry_run=False):
    files = get_chapter_files(target_dir)
    reverse_sort = True if step > 0 else False
    files.sort(key=lambda x: x[0], reverse=reverse_sort)

    to_rename = []
    for num, filename in files:
        should_shift = (num >= pivot) if step > 0 else (num > pivot)
        if should_shift:
            new_filename = f"chapter-{num + step}.md"
            to_rename.append((filename, new_filename))

    if not to_rename and not create_new:
        print("Nothing to shift.")
        return

    print(f"\nTarget: {os.path.abspath(target_dir)}")
    for old, new in to_rename:
        print(f"  {old} -> {new}")
    if create_new:
        print(f"  [NEW] -> chapter-{pivot}.md")

    if dry_run:
        print("\nDry run; no changes applied.")
        return

    if confirm and input("\nConfirm changes? (y/n): ").lower() != "y":
        return

    for old, new in to_rename:
        os.rename(os.path.join(target_dir, old), os.path.join(target_dir, new))

    if create_new:
        new_path = os.path.join(target_dir, f"chapter-{pivot}.md")
        with open(new_path, "w") as f:
            f.write(f"# Chapter {pivot}\n")
    print("Done.")


@contextmanager
def pushd(path):
    """Temporarily change working directory."""
    prev = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev)


def show_stats(target_dir):
    chapters = get_chapter_files(target_dir)
    total_words = 0
    print(f"{'Chapter':<12} | {'Words':<10}")
    print("-" * 25)
    for num, path in chapters:
        with open(os.path.join(target_dir, path), "r") as f:
            text = f.read()
            # Simple regex to count words, ignoring MD syntax
            words = len(re.findall(r"\w+", text))
            total_words += words
            print(f"Chapter {num:<4} | {words:<10}")
    print("-" * 25)
    print(f"Total Word Count: {total_words}")


def ensure_parent_directories(file_path):
    path = pathlib.Path(file_path)
    parent = path.parent

    if not parent.exists() and str(parent) != ".":
        print(f"Warning: The directory structure '{parent}' does not exist.")
        print("If you proceed without creating it, the file write operation will fail.")

        choice = input(f"Would you like to create the directories now? (y/n): ").lower()

        if choice == "y":
            try:
                parent.mkdir(parents=True, exist_ok=True)
                print(f"Success: Directories created at {parent.absolute()}")
            except OSError as e:
                print(f"Error: Could not create directories. {e}")
                sys.exit(1)
        else:
            print(
                "Proceeding without creating directories. Note: The script will likely crash on write."
            )


def compile_manuscript(
    target_dir,
    output_file,
    metadata_file,
    book_dir=None,
    lua_filter=None,
    latex_template=None,
    verbose=False,
):
    prev_cwd = os.getcwd()

    output_file = os.path.abspath(os.path.join(prev_cwd, output_file))
    ensure_parent_directories(output_file)

    if metadata_file:
        metadata_file = os.path.abspath(os.path.join(prev_cwd, metadata_file))

    if lua_filter:
        lua_filter = os.path.abspath(os.path.join(prev_cwd, lua_filter))
    if latex_template:
        latex_template = os.path.abspath(os.path.join(prev_cwd, latex_template))

    if book_dir:
        book_dir = os.path.abspath(book_dir)
        if not os.path.isdir(book_dir):
            print(f"Error: Book directory '{book_dir}' not found.")
            return

    if shutil.which("pandoc") is None:
        print(
            "Error: 'pandoc' was not found in PATH. Please install pandoc or ensure it's on your PATH."
        )
        return

    try:
        with pushd(book_dir) if book_dir else nullcontext():
            chapters = get_chapter_files(target_dir)
            if not chapters:
                print("No chapters found to compile.")
                return

            lua_filter = lua_filter or get_asset_path("template.lua")
            latex_template = latex_template or get_asset_path("template.tex")

            if not os.path.isfile(lua_filter):
                print(f"Error: Lua filter '{lua_filter}' not found.")
                return

            if not os.path.isfile(latex_template):
                print(f"Error: LaTeX template '{latex_template}' not found.")
                return

            chapter_paths = [
                os.path.join(target_dir, filename) for _, filename in chapters
            ]

            cmd = [
                "pandoc",
                os.devnull,  # /dev/null is a workaround to ensure pandoc treats the input as coming from a file. We pass the actual chapter files via the custom --include-body metadata field instead of as direct input.
                "--from=Markdown",
                "--toc=true",
                "--toc-depth=1",
                "--listings",  # Use LaTeX listings for code blocks
                "--top-level-division=chapter",
                "--pdf-engine=lualatex",
                "--lua-filter",
                lua_filter,
                "--template",
                latex_template,
                "-o",
                output_file,
                "-M",
                "chapter-dir=" + target_dir,
            ]

            if metadata_file:
                if not os.path.isfile(metadata_file):
                    print(f"Error: Metadata file '{metadata_file}' not found.")
                    return
                cmd.extend(["--metadata-file", metadata_file])

            if verbose:
                cmd.extend(["--verbose"])
                print("Running command:")
                print(" ".join(shlex.quote(part) for part in cmd))

            print(f"Compiling {len(chapters)} chapters into {output_file}...")
            subprocess.run(cmd, check=True)
            print("Compilation successful.")
    except subprocess.CalledProcessError as e:
        print(f"Pandoc Error: {e}")
        sys.exit(1)


def clear_cache():
    try:
        subprocess.run(["luaotfload-tool", "--update"], check=True)
        print("Font database refreshed.")
    except FileNotFoundError:
        print("Warning: luaotfload-tool not found.")


def main():
    parser = argparse.ArgumentParser(
        description="Bookster: Book Writing Manager",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--add-chapter",
        type=int,
        metavar="N",
        help="Add a new chapter at position N (shifts existing chapters up)",
    )
    group.add_argument(
        "--remove-chapter",
        type=int,
        metavar="N",
        help="Remove chapter at position N (shifts existing chapters down)",
    )
    group.add_argument(
        "--compile", action="store_true", help="Compile the book using Pandoc"
    )

    group.add_argument(
        "--clear-cache", action="store_true", help="Clear the font cache"
    )

    group.add_argument(
        "--stats",
        "--show-stats",
        action="store_true",
        help="Print word counts per chapter",
    )

    parser.add_argument(
        "--chapter-dir",
        default=".",
        help="Directory of chapters (relative to --book-dir)",
    )
    parser.add_argument(
        "--book-dir", default=None, help="Directory to switch to before running pandoc"
    )
    parser.add_argument("--output", default="book.pdf", help="Output filename")
    parser.add_argument(
        "--metadata", default="book.yml", help="Path to a YAML metadata file"
    )
    parser.add_argument(
        "--lua-filter",
        help="Path to a pandoc Lua filter (defaults to builtin data/template.lua)",
    )
    parser.add_argument(
        "--latex-template",
        help="Path to a pandoc LaTeX template (defaults to builtin data/template.tex)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print verbose information including the pandoc command",
    )
    parser.add_argument(
        "--yes", "-y", action="store_true", help="Skip confirmation prompts"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without making any changes",
    )

    args = parser.parse_args()

    chapter_dir = os.path.abspath(args.chapter_dir)
    if args.book_dir:
        chapter_dir = os.path.abspath(os.path.join(args.book_dir, args.chapter_dir))

    metadata_file = os.path.abspath(args.metadata)
    if args.book_dir:
        metadata_file = os.path.abspath(os.path.join(args.book_dir, args.metadata))

    if args.compile:
        compile_manuscript(
            chapter_dir,
            args.output,
            metadata_file,
            book_dir=args.book_dir,
            lua_filter=args.lua_filter,
            latex_template=args.latex_template,
            verbose=args.verbose,
        )
    elif args.stats:
        show_stats(chapter_dir)
    elif args.clear_cache:
        clear_cache()
    elif args.add_chapter:
        run_shift(
            chapter_dir,
            args.add_chapter,
            1,
            True,
            confirm=not args.yes,
            dry_run=args.dry_run,
        )
    elif args.remove_chapter:
        run_shift(
            chapter_dir,
            args.remove_chapter,
            -1,
            False,
            confirm=not args.yes,
            dry_run=args.dry_run,
        )


if __name__ == "__main__":
    main()
