from unittest import TestCase

from health_lib import Observation, ValueQuantity
from sparkbase import group_by_days, get_max


class Test(TestCase):
    def test_group_by_days(self):
        one: Observation = Observation(name="One", date="2021-01-01T10:01:02", source_name="X")
        two: Observation = Observation(name="Two", date="2021-01-01T10:03:04", source_name="X")
        thr: Observation = Observation(name="Thr", date="2021-01-01T11:05:06", source_name="Y")
        fou: Observation = Observation(name="Fou", date="2021-01-02T11:05:06", source_name="X")
        fiv: Observation = Observation(name="Fiv", date="2021-01-02T13:07:08", source_name="X")
        six: Observation = Observation(name="Six", date="2021-01-03T14:09:10", source_name="Y")
        data = [[one, two, thr, fou, fiv, six]]
        out = group_by_days(data)
        self.assertEqual(out, [[one, two, thr], [fou, fiv], [six]])
        out = group_by_days(data, "X")
        self.assertEqual(out, [[one, two], [fou, fiv]])

    def test_get_max(self):
        one: Observation = Observation(name="One",
                                       date="2021-01-01T10:01:02",
                                       source_name="X",
                                       data=[ValueQuantity(value=1.0, unit="grams", name='test11'), ValueQuantity(value=2.7, unit="grams", name="test12")])
        two: Observation = Observation(name="Two",
                                       date="2021-01-01T10:01:02",
                                       source_name="X",
                                       data=[ValueQuantity(value=1.7, unit="grams", name='test11'), ValueQuantity(value=5.7, unit="grams", name="test12")])
        thr: Observation = Observation(name="The",
                                       date="2021-01-01T10:01:02",
                                       source_name="X",
                                       data=[ValueQuantity(value=900.13, unit="grams", name='test11'), ValueQuantity(value=5.7, unit="grams", name="test12")])
        fou: Observation = Observation(name="Fou",
                                       date="2021-01-01T10:01:02",
                                       source_name="X",
                                       data=[ValueQuantity(value=1.5, unit="grams", name='test11'), ValueQuantity(value=50.7, unit="grams", name="test12")])
        l = [[one]]
        m = get_max(l)
        self.assertEqual(2.7, m)

        l = [[one, two], [thr, fou]]
        m = get_max(l)
        self.assertEqual(900.13, m)
