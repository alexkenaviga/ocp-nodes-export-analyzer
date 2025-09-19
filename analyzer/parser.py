import re
import json

from array import ArrayType
from pathlib import Path


class ContentParser:

    @staticmethod
    def parse_cpu(cpu_value: str):
        if cpu_value is None:
            return None
        if cpu_value.endswith("m"):
            return int(cpu_value[:-1])
        return int(cpu_value) * 1000

    @staticmethod
    def parse_mem(mem_value: str):
        if mem_value is None:
            return None
        if mem_value.endswith("G"):
            return f"{int(mem_value[:-1]) * 1000}M"
        if mem_value.endswith("Gi"):
            return f"{int(mem_value[:-2]) * 1024}Mi"
        if mem_value.endswith("K"):
            return f"{round(int(mem_value[:-1]) / 1024)}Mi"
        if mem_value.endswith("Ki"):
            return f"{round(int(mem_value[:-2]) / 1024)}Mi"
        return mem_value

    def __init__(self, matcher):
        self.matcher = matcher

    def parse(self, content: ArrayType):
        raise NotImplementedError()


class AllocatedResourcesParser(ContentParser):
    __RES_RE__ = re.compile(r"^(cpu|memory)")

    def __init__(self):
        super().__init__("Allocated resources")

    def parse(self, content: ArrayType):
        out = {}
        for line in content:
            match = self.__RES_RE__.match(line)
            if match is not None:
                tokens = line.split()
                out[tokens[0]] = {"Requests": tokens[1], "Limits": tokens[3]}
        return out


class NonTerminatedPodsParser(ContentParser):
    __SKIP_RE__ = re.compile(r"^(Namespace|-+)")

    def __init__(self):
        super().__init__("Non-terminated Pods")

    def parse(self, content: ArrayType):
        out = {}
        for line in content:
            if not self.__SKIP_RE__.match(line):
                tokens = line.split()
                namespace = tokens[0]
                pod = re.sub(r"-[^-]*$", "", tokens[1])
                if not out.get(namespace):
                    out[namespace] = {}

                cpu_requests = self.parse_cpu(tokens[2])
                cpu_limits = self.parse_cpu(tokens[4])
                memory_requests = self.parse_mem(tokens[6])
                memory_limits = self.parse_mem(tokens[8])

                out[namespace][pod] = {
                    "CPU Requests": cpu_requests,
                    "CPU Limits": cpu_limits,
                    "Memory Requests": memory_requests,
                    "Memory Limits": memory_limits
                }

        return out


class CapacityParser(ContentParser):
    __RES_RE__ = re.compile(r"^(cpu|memory)")

    def __init__(self):
        super().__init__("Capacity")

    def parse(self, content: ArrayType):
        out = {}
        for line in content:
            match = self.__RES_RE__.match(line)
            if match is not None:
                tokens = line.split()
                if tokens[0] == "cpu:":
                    out[tokens[0][:-1]] = f"{self.parse_cpu(tokens[1])}m"
                else:
                    out[tokens[0][:-1]] = self.parse_mem(tokens[1])
        return out


class Parser:

    __ITEM_RE__ = re.compile(r"^([A-Za-z].+?):(.*)")

    __PARSERS__ = [ AllocatedResourcesParser(), NonTerminatedPodsParser(), CapacityParser() ]

    def __init__(self):
        pass

    def parse(self, path: Path):
        if path.is_dir():
            raise ValueError(f"{path} is a directory")

        with open(path) as file:
            parsed = {}

            current_item = None

            for line in file:
                match = self.__ITEM_RE__.match(line)

                if match is not None:
                    current_item = match.group(1)

                    value = match.group(2).strip()
                    if len(value) == 0 or value == "<none>":
                        value = None

                    parsed[current_item] = {
                        "value": value,
                        "raw_content": []
                    }

                else:
                    parsed[current_item]["raw_content"].append(line.strip())

            for key, value in parsed.items():
                for parser in self.__PARSERS__:
                    if parser.matcher == key:
                        parsed[key]["content"] = parser.parse(value["raw_content"])

            # print(json.dumps(parsed, indent=2))
            out = {}
            for topic, data in parsed.items():
                if "content" in data or data["value"] is not None:
                    out[topic] = {}
                    if "content" in data is not None:
                        out[topic]["content"] = data["content"]
                    if data["value"] is not None:
                        out[topic]["value"] = data["value"]

            return out


if __name__ == "__main__":
    p = Parser()
    parsed = p.parse(Path("../test/resources/test-report.txt"))
    print(json.dumps(parsed, indent=2))