"""
Some apple health data comes in xml files.There are two, export.xml, and export_cda.xml. I haven't fully
determined what is in these files. I can see data that is sourced from an apple watch, and that is sourced
from third party devices that write to apple health.

All top level tags from export.xml:
    {'WorkoutEvent', 'Record', 'MetadataEntry', 'InstantaneousBeatsPerMinute', 'ActivitySummary',
    'HeartRateVariabilityMetadataList', 'ClinicalRecord', 'ExportDate', 'Workout', 'HealthData',
    'WorkoutStatistics', 'FileReference', 'WorkoutRoute', 'Me'}

All tags from export_cda.xml:

{'{urn:hl7-org:v3}high', '{urn:hl7-org:v3}sourceName', '{urn:hl7-org:v3}unit', '{urn:hl7-org:v3}component',
'{urn:hl7-org:v3}patient', '{urn:hl7-org:v3}effectiveTime', '{urn:hl7-org:v3}type', '{urn:hl7-org:v3}templateId',
'{urn:hl7-org:v3}realmCode', '{urn:hl7-org:v3}administrativeGenderCode', '{urn:hl7-org:v3}statusCode',
'{urn:hl7-org:v3}key', '{urn:hl7-org:v3}organizer', '{urn:hl7-org:v3}ClinicalDocument', '{urn:hl7-org:v3}text',
'{urn:hl7-org:v3}value', '{urn:hl7-org:v3}low', '{urn:hl7-org:v3}entry', '{urn:hl7-org:v3}id', '{urn:hl7-org:v3}typeId',
'{urn:hl7-org:v3}sourceVersion', '{urn:hl7-org:v3}recordTarget', '{urn:hl7-org:v3}observation',
'{urn:hl7-org:v3}confidentialityCode', '{urn:hl7-org:v3}title', '{urn:hl7-org:v3}device', '{urn:hl7-org:v3}patientRole',
'{urn:hl7-org:v3}interpretationCode', '{urn:hl7-org:v3}name', '{urn:hl7-org:v3}metadataEntry', '{urn:hl7-org:v3}code',
'{urn:hl7-org:v3}birthTime'}


Using https://realpython.com/python-xml-parser/#xmletreeelementtree-a-lightweight-pythonic-alternative

# TODO Add plotting

"""
import argparse
import unicodedata
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from collections import Counter
from datetime import datetime
from math import log10
from typing import Optional, Generator

from health_lib import Observation, ValueQuantity

@dataclass
class Pattern:
    path: list[str]
    attr: str | None  # None mean get text under tag.

def find(stack: list[str], target: list[str]) -> bool:
    """
    A very limited XQuery. Just matches the last N tags in stack, where N is the length of target
    :param stack:
    :param target:
    :return: bool
    """
    if len(target) > len(stack):
        return False
    for x in range(1, len(target)+1):
        if target[-x] != stack[-x]:
            return False
    return True

def trim(tag: str) -> str:
    """
    All the tags are namespaced in the same namespace, so it doesn't matter. Trim it off for simplicity.
    :param tag:
    :return:
    """
    if "}" not in tag:
        return tag
    return tag[tag.find("}")+1:]

def clean_tag(tag: str) -> str:
    tag = unicodedata.normalize("NFKD", trim(tag))
    return tag

def gen(file_name: str, events):
    for index, i in enumerate(ET.iterparse(file_name, events=events)):
        event, element = i
        yield index, event, element

def find_parent_tag(patterns: list[Pattern]):
    """
    If we are finding a set of information from various tags, the information won't be complete until we have all
    of them. How do we know that we have all the information? When the common parent tab closes. This method
    finds the closest parent tag

    The patterns must start at the same level.
    :param patterns: The list of patterns
    :return: Pattern
    """
    assert patterns
    paths = [p.path for p in patterns]
    assert paths
    pp = paths[0]
    for path in paths[1:]:
        if len(pp) > len(path):
            pp = pp[:len(path)]
        for index in range(len(pp)):
            if path[index] != pp[index]:
                pp = pp[:index]
    assert pp
    return Pattern(pp, None)


def find_display_names(file_name: str, patterns: list[Pattern]):
    parent_tag: Pattern = find_parent_tag(patterns)
    element_stack = []
    display_names = Counter()
    names =[]
    for index, event, element in gen(file_name, ["start", "end"]):
        tag = clean_tag(element.tag)
        if event == "start":
            element_stack.append(tag)
        elif event == "end":
            for pattern in patterns:
                if find(element_stack, target=pattern.path):
                    if pattern.attr:
                        dn = element.attrib[pattern.attr]
                        names.insert(0, dn)
                    else:
                        dn = element.text
                        names.insert(0, dn)
            if find(element_stack, target=parent_tag.path):
                qualified_name = ":".join(names)
                display_names[qualified_name] += 1
                names = []

            element_stack.pop()
    return sorted(display_names), element_stack  # Only returning element_stack for test.


def get_test_results(display_name_wanted: Optional[str], file_name) -> Generator[Observation, None, None]:
    """
    Process Apple Health's exported export_cda.xml file. Looking for test results.
    :return:
    """
    tags: set[str] = set()
    element_stack: list[str] = []
    # file_name = "test_data/export_cda_fraction.xml"
    # file_name = "test_data/export_cda_1000.xml"
    count: int = 0
    count_sources: int = 0
    none_count: int = 0
    ob: Optional[Observation] = None
    for index, i in enumerate(ET.iterparse(file_name, events=("start", "end"))):
        event, element = i
        tag: str = unicodedata.normalize("NFKD", trim(element.tag))
        tags.add(tag)
        if event == "start":
            # print(tag, element.attrib, element_stack)
            element_stack.append(tag)
            # print(element, element.attrib, element.text)
            if find(element_stack, ["component", "observation", "code"]):
                dn = element.attrib['displayName']
                if display_name_wanted is not None and dn == display_name_wanted:
                    ob = Observation(name=element.attrib['displayName'])
        elif event == "end":
            # Some elements/attributes are not set while processing the start tag, so we have to pick them up here.
            if find(element_stack, ["component", "observation", "text", "sourceName"]):
                if element.text is None:
                    # print("None")
                    none_count += 1
                    source_name = "NoneName"
                else:
                    source_name = unicodedata.normalize("NFKD", element.text)

            if find(element_stack, ["component", "observation", "text", "unit"]):
                unit = element.text
                count += 1

            if find(element_stack, ["component", "observation", "text", "value"]):
                value = float(element.text)
                # vq = ValueQuantity(float(element.text), unit, ob.name)
                # ob.value = [vq]


            # TODO: There is a "low" and a "high"
            if find(element_stack, ["component", "observation", "effectiveTime", "low"]):  # Just use "low" for now.
                timestamp = element.attrib['value']
                dt_obj = datetime.strptime(timestamp, '%Y%m%d%H%M%S%z')
                dt_string = datetime.strftime(dt_obj, '%Y-%m-%dT%H:%M:%SZ')

            # Last tag we see, while collecting an Observation.
            if find(element_stack, ["component", "observation"]):
                if ob is not None:
                    assert value is not None
                    assert unit is not None

                    vq = ValueQuantity(value, unit, ob.name)
                    ob.data = [vq]
                    ob.filename = file_name
                    ob.date = dt_string
                    ob.source_name = source_name
                    yield ob
                ob = None
                value = None
                unit = None
                dt_string = None

            element_stack.pop()

def print_test_results():
    count = 0
    for index, obs in enumerate(get_test_results()):
        print(F"{index:8}: {obs} END")
        count += 1

    print(F"Found {count:,} observations.")
    # print_tags: bool = False # Look into RETURN values from generator functions
    # if print_tags:
    #     print("All Tags:")
    #     for tag in sorted(tags):
    #         print(tag)


def get_all_test_types(filename="export/apple_health_export/export_cda.xml") -> Counter[str]:
    print("This may take a few minutes...")
    pn = Pattern(["component", "observation", "code"], "displayName")
    ps = Pattern(["component", "observation", "text", "sourceName"], None)
    patterns = [pn, ps]
    names, _ = find_display_names(filename, patterns)
    return names

def print_all_test_types():
    names = get_all_test_types()
    max_count_name = max(names, key=names.get)
    max_count = names[max_count_name]

    lmc = int(log10(max_count) * (1 +  1 / 3) + 1)  ## Allow for commans

    print(max_count, lmc)
    for index, _ in enumerate(names.most_common()):
        name, count = _
        print(F"{index:6}: [{count:{lmc},}] {name} ")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Investigate data from Apple Health export.\nNote that "
                                     "an export can be millions of records, so this can take a long time."
                                     "When run with no arguments, it prints all tests and all results.")
    parser.add_argument("-l", "--list", action="store_true", help="List all observations. SLOW! (minutes)")
    args = parser.parse_args()
    if args.list:
        print_all_test_types()
    else:
        print_test_results()