import re
import json
from array import ArrayType

from pathlib import Path

class ContentParser:

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
                out[namespace][pod] = {"CPU Requests": tokens[2], "CPU Limits": tokens[4], "Memory Requests": tokens[6], "Memory Limits": tokens[8]}
        return out

class Parser:

    __ITEM_RE__ = re.compile(r"^([A-Za-z].+?):(.*)")

    __PARSERS__ = [ AllocatedResourcesParser(), NonTerminatedPodsParser() ]

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