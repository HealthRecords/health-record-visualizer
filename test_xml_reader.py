from unittest import TestCase

from xml_reader import find, trim, find_display_names, find_parent_tag, Pattern, FetchType


class Test(TestCase):
    def test_find(self):
        stack = ["1", "2", "3"]
        target = ["2", "3"]
        self.assertTrue(find(stack, target))

        target = ["3", "2"]
        self.assertFalse(find(stack, target))

        target = ["3", "2"]
        stack = []
        self.assertFalse(find(stack, target))

    def test_trim(self):
        tag = "{urn:hl7-org:v3}text"
        self.assertEqual("text", trim(tag))

        tag = "text"
        self.assertEqual("text", trim(tag))

        tag = ""
        self.assertEqual("", trim(tag))

    def test_load(self):
        import xml.etree.ElementTree as ET

        for event, element in ET.iterparse("test_data/export_cda_fraction_source.xml", events=["start"]):
            if element.text:
                t = element.text.strip()
            else:
                t = element.text
            # print(element, t)

    def test_find_display_names(self):
        display_names, element_stack = find_display_names(
            "test_data/test_find_display_names.xml",
            [Pattern(["organizer", "code"], FetchType.ATTR, "displayName")])
        self.assertEqual(1, len(display_names))
        self.assertEqual(0, len(element_stack))

        display_names, element_stack = find_display_names(
            "test_data/test_find_display_names.xml",
            [Pattern(["component", "observation", "code"], FetchType.ATTR, "displayName")])
        self.assertEqual(2, len(display_names))
        self.assertEqual(0, len(element_stack))
        self.assertEqual(2, display_names["Heart rate"])
        self.assertEqual(1, display_names["Alt heart rate"])

        display_names, element_stack = find_display_names(
            "test_data/test_find_display_names.xml",
            [Pattern(["component", "observation", "text", "sourceName"], FetchType.CONTENT, None)])
        self.assertEqual(2, len(display_names))
        self.assertEqual(0, len(element_stack))
        self.assertEqual(2, display_names["EMAY Oximeter:Heart rate"])
        self.assertEqual(1, display_names["EMAY Oximeter:Alt Heart rate"])

    def test_find_display_names2(self):
        display_names, element_stack = find_display_names(
            "test_data/test_find_display_names.xml",
            [
                Pattern(["component", "observation", "code"], FetchType.ATTR, "displayName"),
                Pattern(["component", "observation", "text", "sourceName"], FetchType.CONTENT, None),
            ])
        self.assertEqual(2, len(display_names))
        self.assertEqual(0, len(element_stack))
        self.assertEqual(2, display_names["EMAY Oximeter:Heart rate"])
        self.assertEqual(1, display_names["EMAY Oximeter:Alt heart rate"])

    def test_find_parent_tag(self):
        paths: list[Pattern] = [
            Pattern(["a", "b", "c"], FetchType.CONTENT, None),
            Pattern(["a", "b"], FetchType.CONTENT, None),
        ]
        path: Pattern = find_parent_tag(paths)
        self.assertEqual(2, len(path.path))
        self.assertEqual(["a", "b"], path.path)

        paths: list[Pattern] = [
            Pattern(["a", "b", "c"], FetchType.CONTENT, None),
            Pattern(["a"], FetchType.CONTENT, None),
            Pattern(["a", "b", "c", "d"], FetchType.CONTENT, None),
        ]
        path: Pattern = find_parent_tag(paths)
        self.assertEqual(1, len(path.path))
        self.assertEqual(["a"], path.path)
