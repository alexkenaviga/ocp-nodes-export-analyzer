import click
import json

from pathlib import Path
from analyzer import Parser


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
    f = click.option(
        "-z",
        "--include-openshift-ns",
        is_flag=True,
        show_default=True,
        default=False,
        help="Include evaluation of openshift ns",
    )(f)
    return f


@click.group()
def cli():
    """Main entry point for the CLI."""


@cli.command(name="analyze", help="Get a list of datasources")
@common_options
def analyze(folder, include_openshift_ns):
    target_directory = Path(folder)

    if not  target_directory.is_dir():
        raise click.BadParameter(f"Folder {target_directory} is not a directory")
    else:
        # print(f"Analyzing files in {folder}:")

        export_paths = [item for item in target_directory.iterdir() if item.is_file() and item.suffix == '.txt']

        parser = Parser()
        pods = {}
        resources = {}

        for export_path in export_paths:
            # print(f" - {export_path}")

            parsed = parser.parse(export_path)

            for namespace in parsed["Non-terminated Pods"]["content"]:
                if include_openshift_ns or not namespace.startswith("openshift"):
                    # print(f"    - {export_path} -> {namespace}")
                    if namespace not in pods:
                        pods[namespace] = {}
                    for pod in parsed["Non-terminated Pods"]["content"][namespace]:
                        if pod not in pods[namespace]:
                            pods[namespace][pod] = 1
                        else :
                            pods[namespace][pod] += 1

        print("NAMESPACE\tDEPLOYMENT\tINSTANCES")
        for namespace, pods in pods.items():
            for pod in pods:
                print(f"{namespace}\t{pod}\t{pods[pod]}")


