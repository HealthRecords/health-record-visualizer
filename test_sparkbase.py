from unittest import TestCase

from health_lib import Observation
from sparkbase import group_by_days


class Test(TestCase):
    def test_group_by_days(self):
        one: Observation = Observation(name="One", date="2021-01-01T10:01:02")
        two: Observation = Observation(name="Two", date="2021-01-01T10:03:04")
        thr: Observation = Observation(name="Thr", date="2021-01-01T11:05:06")
        fou: Observation = Observation(name="Fou", date="2021-01-02T11:05:06")
        fiv: Observation = Observation(name="Fiv", date="2021-01-02T13:07:08")
        six: Observation = Observation(name="Six", date="2021-01-03T14:09:10")
        data = [[one, two, thr, fou, fiv, six]]
        out = group_by_days(data)
        self.assertEqual(out, [[one, two, thr],[fou,fiv],[six]])

