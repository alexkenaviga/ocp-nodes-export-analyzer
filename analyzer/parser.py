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
    __RES_RE__ = re.compile(r"^(cpu|memory)( +)(\d+[A-Za-z]*)( +)(\(.+?\))( +)(\d+[A-Za-z]*)( +)")

    def __init__(self):
        super().__init__("Allocated resources")

    def parse(self, content: ArrayType):
        out = {}
        for line in content:
            match = self.__RES_RE__.match(line)
            if match is not None:
                out[match.group(1)] = (match.group(3), match.group(7))
        return out

class NonTerminatedPodsParser(ContentParser):
    __SKIP_RE__ = re.compile(r"^(Namespace|-+)")
    __POD_RE__ = re.compile(r"^(.+?)( +)(.+?)( +)")

    def __init__(self):
        super().__init__("Non-terminated Pods")

    def parse(self, content: ArrayType):
        out = {}
        for line in content:
            if not self.__SKIP_RE__.match(line):
                match = self.__POD_RE__.match(line)
                if match is not None:
                    namespace = match.group(1).strip()
                    pod = re.sub(r"-[^-]*$", "", match.group(3).strip())
                    if not out.get(namespace):
                        out[namespace] = []
                    out[namespace].append(pod)
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
                    if len(value) == 0:
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
            print(json.dumps(out, indent=2))


if __name__ == "__main__":
    p = Parser()
    p.parse(Path("../test/resources/test-report.txt"))