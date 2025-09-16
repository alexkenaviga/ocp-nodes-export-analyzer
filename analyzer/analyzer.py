import click
from pathlib import Path

def common_options(f):
    """
    Decorate the command with common args and options
    """
    f = click.option(
        "-f",
        "--folder",
        is_flag=False,
        show_default=True,
        default="./resources",
        help="Folder containing files to analyze",
    )(f)

    return f


@click.group()
def cli():
    """Main entry point for the CLI."""


@cli.command(name="analyze", help="Get a list of datasources")
@common_options
def analyze(folder):
    target_directory = Path(folder)

    if not  target_directory.is_dir():
        raise click.BadParameter(f"Folder {target_directory} is not a directory")
    else:
        print(f"Analyzing files in {folder}:")

        export_paths = [item for item in target_directory.iterdir() if item.is_file() and item.suffix == '.txt']

        for export_path in export_paths:
            print(f" - {export_path}")

