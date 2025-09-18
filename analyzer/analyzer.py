import click
import json

from pathlib import Path
from analyzer import Parser


ANALYSIS_HEADER = ["NAMESPACE","DEPLOYMENT","INSTANCES","CPU REQUESTS[m]","CPU LIMITS[m]",
                   "MEMORY REQUESTS","MEMORY LIMITS","MULTIPLE RESOURCES"]


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
@click.option(
    "-j",
    "--json-format",
    is_flag=True,
    show_default=True,
    default=False,
    help="Use JSON format, default is TSV"
)
def analyze(folder, include_openshift_ns, json_format):
    target_directory = Path(folder)

    if not  target_directory.is_dir():
        raise click.BadParameter(f"Folder {target_directory} is not a directory")
    else:
        # print(f"Analyzing files in {folder}:")

        export_paths = [item for item in target_directory.iterdir() if item.is_file() and item.suffix == '.txt']

        parser = Parser()
        output_data = {}

        for export_path in export_paths:
            # print(f" - {export_path}")

            parsed = parser.parse(export_path)

            non_terminated_pods = parsed["Non-terminated Pods"]["content"]
            for namespace in non_terminated_pods:
                # Include only non-openshift namespace unless flag `include_openshift_ns` requires them
                if include_openshift_ns or not namespace.startswith("openshift"):

                    # print(f"    - {export_path} -> {namespace}")
                    if namespace not in output_data:
                        output_data[namespace] = {}

                    for pod_name in non_terminated_pods[namespace]:
                        if pod_name not in output_data[namespace]:
                            output_data[namespace][pod_name] = {"count": 1, "resources": []}
                        else :
                            output_data[namespace][pod_name]["count"] += 1

                        if non_terminated_pods[namespace][pod_name] not in output_data[namespace][pod_name]["resources"]:
                            output_data[namespace][pod_name]["resources"].append(non_terminated_pods[namespace][pod_name])

        if not json_format:
            print('\t'.join(ANALYSIS_HEADER))
            for namespace, output_data in output_data.items():
                for pod in output_data:
                    resources = [str(value) for value in output_data[pod]["resources"][0].values()]
                    print(f"{namespace}\t{pod}\t{output_data[pod]["count"]}\t{'\t'.join(resources)}\t{len(output_data[pod]["resources"])>1}")
        else:
            print(json.dumps(output_data, indent=4))


