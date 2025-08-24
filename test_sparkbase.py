from unittest import TestCase

from health_lib import Observation
from sparkbase import group_by_days


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
        self.assertEqual(out, [[one, two, thr],[fou,fiv],[six]])
        out = group_by_days(data, "X")
        self.assertEqual(out, [[one, two],[fou,fiv]])

