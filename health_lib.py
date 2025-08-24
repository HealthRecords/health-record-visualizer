""""
This library provides a way to explore your health information.

Design note: This is an exploration tool, not a product. As I don't have documentation for the file formats,
I try to put assertions in, to verify my assumptions, like "A referenceRange only has one value". That's the only case
I have seen, but there are probably millions of cases I have not seen, yet. It's better to hit an assertion and fix
it, than to silently hide information.
"""
import json
import sys
from pathlib import Path
from typing import Iterable, Optional
import re

from dataclasses import dataclass
from collections import Counter


@dataclass
class StatInfo:
    category_name: str
    name: str


@dataclass
class ValueQuantity:
    """
    Represents a "valueQuantity", from an Observation. It provides a value, a unit and optionally a name.

    We are combining two objects from the documentation.

    "referenceRange" seems to use the same schema as valueQuantity, once for min and once for max, so we'll
    use valueQuantity for this as well.

    For Observations with a single value, the Observation contains one valueQuantity object.
    For Observations with multiple values, like blood pressure, there is a "component", which contains a valueObject
    and "code" with a name for each individual value.
    a name field (single valued fields use the category text).

    We ignore system, and the duplication with "code" and "unit".

    "valueQuantity" : {
        "code" : "mg/dL",
        "value" : 0.90,
        "system" : "http://unitsofmeasure.org",
        "unit" : "mg/dL"
    },

    Just found, this, and don't handle it yet. I think this current will just be treated like a value of 60. TODO
    "valueQuantity" : {
        "code" : "mL/min",
        "value" : 60,
        "comparator" : ">",
        "system" : "http://unitsofmeasure.org",
        "unit" : "mL/min"
    },
    """
    value: float
    unit: str
    name: str


reference_range_pattern = re.compile(r"[<=>]+")
@dataclass
class ReferenceRange:
    """
    The normal or "referenceRange" from the Observation file.

    "referenceRange" : [
    {
        "low" : {
            "code" : "K/uL",
            "value" : 140,
            "system" : "http://unitsofmeasure.org",
            "unit" : "K/uL"
        },
        "high" : {
            "code" : "K/uL",
            "value" : 400,
            "system" : "http://unitsofmeasure.org",
            "unit" : "K/uL"
        },
        "text" : "140 - 400 K/uL"
    }
    ],

    But there are about 10% that don't have explicit or any numeric values:
        [{"text":"<=1.34"}]
        [{"text":"<=0"}]
        [{"text":"---"}]
        [{"text":"NEGATIVE"}]
        [{"text":"YELLOW"}]
        [{"text":"ABSENT"}]
        [{"text":"CLEAR"}]
        [{"text":"NEGATIVE"}]
        [{"text":"NON REAC"}]
        [{"text":"NORMAL"}]

        also      "text" : "6.0 - 7.7 g/dL"

    The "<" or "<=" could be parsed, and are the most common format. Odd, and annoying that they have something that
    could be expressed with "low" and "high", but aren't.
    """
    low: Optional[ValueQuantity]
    high: Optional[ValueQuantity]
    text: str
    def get_range(self):
        """
        we need to have get range, because we can try to extract the range from the text field, if there
        are not an explicit low and high.
        :return: low: float, high: float
        """
        if self.low is not None:
            assert self.low.value is not None
            assert self.high is not None
            assert self.high.value is not None
            return self.low.value, self.high.value
        if self.text is not None:
            operators = reference_range_pattern.findall(self.text)
            if not operators:
                return None
            assert len(operators) == 1
            op = operators[0]
            value = self.text[len(op):]
            assert value
            value = float(value)
            # TODO what do I return for high for ">10", max int? max value on the graph? None?
            # TODO: Just found: text: "6.0 - 7.7 g/dL
            match op:
                case "<" | "<=":
                    return -sys.maxsize, value
                case ">" | ">=":
                    return value, sys.maxsize
                case "=":
                    return value, value

        return None  # TODO extract from text field, where possible.

@dataclass(kw_only=True)
class Observation:
    """
    This holds data from one file, which records an observation, such as height or blood pressure.
    """
    name: str
    date: str = None
    data: list[ValueQuantity] = None
    range: Optional[ReferenceRange] = None
    filename: Path = None


def convert_units(v, u):
    # TODO this should be optional, but we are parsing US data.
    if u == "kg":
        v = v * 2.2
        u = "lb"
    elif u == "Cel":
        v = v * 9.0 / 5.0 + 32.0
        u = "Fah"
    return v, u

def get_value_quantity(val: dict, test_name) -> ValueQuantity:
    v = val["value"]
    if 'unit' not in val:
        u = "NoUnit"  # Ratios actually have no unit.
    else:
        u = val["unit"]
        v, u = convert_units(v, u)
    vq = ValueQuantity(v, u, test_name)
    return vq

def get_reference_range(rl: list) -> ReferenceRange:
    assert 1 == len(rl) # I've never seen a refernef
    r = rl[0]
    # if len(r) != 3
    # assert 3 == len(r)
    if "low" in r:
        low = get_value_quantity(r["low"], "low")
        high = get_value_quantity(r["high"], "high")
    else:
        low = None
        high = None
    text = r['text']
    return ReferenceRange(low, high, text)


value_strings_seen = set()
def extract_value_helper(*, filename: str, condition: dict, stat_info) -> Optional[Observation]:
    """

    :param filename: Just for printing error messages
    :param condition: Could be a condition, an observation, etc. The contents of the file we are parsing now.
    :param stat_info: contains
        category_name: Filtering to this category, like "lab" or "Vital Sign"
        name:  The name of the stat / vital sign we are looking for
    :return: Optional[Observation]
    """
    category_name, sign_name = stat_info.category_name, stat_info.name
    category_info = condition['category']
    assert isinstance(category_info, list)
    for ci in category_info:
        if ci['text'] != category_name:
            continue
        if condition['code']['text'] != sign_name:
            continue
        t = sign_name
        d = condition['effectiveDateTime']
        # It turns out that blood pressure, which has two values, like 144/100,
        # has a slightly different format. First find "component", then each has
        # its own "valueQuantity"
        # TODO There is a get_value_quantity function that duplicates this with different errors. Combine!
        if "valueQuantity" in condition:
            v = condition["valueQuantity"]["value"]
            if "unit" not in condition["valueQuantity"]:
                verbose = False
                if verbose:
                    print("Debug: no units in valueQuantity. ", sign_name, v, filename)
                    u = "NoUnits"
                else:
                    u = ""
            else:
                u = condition["valueQuantity"]["unit"]
                v, u = convert_units(v, u)
            vq = ValueQuantity(v, u, sign_name)
            if "referenceRange" in condition:
                rr = get_reference_range(condition["referenceRange"])
            else:
                rr = None
            return Observation(name=t, date=d, data=[vq], range=rr, filename=Path(filename))

        elif "component" in condition:
            sub_values = []
            for component in condition["component"]:
                val = component["valueQuantity"]["value"]
                unit = component["valueQuantity"]["unit"]
                text = component["code"]["text"]
                val, unit = convert_units(val, unit)
                vq = ValueQuantity(val, unit, text)

                sub_values.append(vq)
                reference_range = None
            return Observation(name=t, date=d, data=sub_values)
        elif "valueString" in condition:
            # TODO Do we even need to check this? I see only two that could possibly graph, and both are ranges:
            #      "    >60", and "1-2", maybe add a verbose option to print these. For now, they don't matter.
            verbose = False
            if verbose:
            # val = condition["valueString"]
            # global value_strings_seen
            # if val not in value_strings_seen:
            #     print(F"We don't handle 'valueString' yet: value is '{val}'")
            #     value_strings_seen.add(val)
                pass
            return None
        else:
            print(F"*** No value found in {filename} ***")
    return None

def extract_value(file: str, stat_info) -> Observation | None:
    """
    Processes one file and extracts the value of a vital sign or other test, from it.
    :param file:
    :param stat_info: contains the sign_name ("Spo2") and the category, like "Lab"
    :return: Optional[Observation
    """
    with open(file) as f:
        condition = json.load(f)
    return extract_value_helper(filename=file, condition=condition, stat_info=stat_info)

def yield_observation_files(dir_path: Path) -> Iterable[str]:
    for p in dir_path.glob("Observation*.json"):
        yield p

def filter_category(observation_files: Iterable[str], category: str) -> Iterable[dict]:
    """
    Filters observations, only passing on those with a category['text'] = category
    :param observation_files: Source for file names
    :param category: The name of the category to keep, like 'Vital Signs'
    :return:
    """
    for file in observation_files:
        with open(file) as f:
            observation = json.load(f)
            category_info = observation['category']
            assert isinstance(category_info, list)
            for ci in category_info:
                if ci['text'] == category:
                    yield observation

def extract_all_values(observation_files: Iterable[str], *, stat_info: StatInfo) -> list[Observation]:
    """
sign_name: str, *, category_name
    :param observation_files: iterable of files to read. Only Obser
    :param stat_info: contains
        category_name: Filtering to this category, like "lab" or "Vital Sign"
        name:  The name of the stat / vital sign we are looking for
    :return: Instance of class Observation or None
    """
    values = []
    for p in observation_files:
        value = extract_value(p, stat_info)
        if value is not None:
            values.append(value)
        else:
            pass
    values = sorted(values, key=lambda x: x.date)
    return values


def list_vitals(observation_files: Iterable[str], category: str) -> Counter:
    vitals = Counter()
    signs_found = filter_category(observation_files, category)
    for observation in signs_found:
        code_name = observation['code']['text']
        vitals[code_name] += 1
    return vitals

def list_prefixes(dir_path: Path) -> Counter:
    extensions = Counter()
    for p in dir_path.glob("*.json"):
        name = p.stem
        parts = name.split("-")
        prefix = parts[0]
        extensions[prefix] += 1
    return extensions


def list_categories(dir_path: Path, only_first, *, one_prefix) -> (list[tuple], Counter, int):
    """
    The schema of this data is not well-designed. I have seen category expressed FOUR ways so far.

    "category":
        "CAT_NAME"

    "category": [
        "CAT_NAME",
        "CAT_NAME2"
    ]

    # Procedure-9EBC73F9-2883-416C-8C39-259B394A953D.json
    "category" : {
         "text" : "CAT_NAME",
    }

    # Observation-6A188217-E5D4-4A52-A762-7194900720FB.json
    category: [
        {
            "text":"CAT_NAME"
        }
    ]

    :param one_prefix: There are different kinds of documents, that start with "Observation" or "MedicationRequest"
    :                  For example, set this to "Observation" to only see categories from Observation files,
                       or set to None for all files.
    :param dir_path: Path of the directory to scan.
    :param only_first:  Only take the first category in a file. This is so we can see if there are any files without
                        categories.
    :return: c_sorted, counter, count
    """
    counter = Counter()
    count = 0
    wildcard = "*.json"
    if one_prefix:
        wildcard = one_prefix + wildcard

    for p in dir_path.glob(wildcard):
        with open(p) as f:
            count += 1
            observation_data = json.load(f)
            cat_top = observation_data["category"]
            if isinstance(cat_top, str):
                counter[cat_top] += 0.1
            elif isinstance(cat_top, dict):
                assert 'text' in ci
                assert isinstance(cat_top['text'], str)
                counter[cat_top['text']] += 1
            elif isinstance(cat_top, list):
                for ci in cat_top:
                    if isinstance(ci, str):
                        counter[ci] += 1
                    elif isinstance(ci, dict):
                        assert 'text' in ci
                        counter[ci['text']] += 1
                    if only_first:
                        break
            else:
                raise ValueError(F"File {p} has no category", p)

    c_sorted = sorted(counter, key=lambda x: counter[x], reverse=True)
    return c_sorted, counter, count
