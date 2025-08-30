import unittest
from obs_matcher import (
    ObservationCodeMapper,
    observations_equivalent,
    NameMismatchError,
    STANDARD_LOINC,
)

def obs(codeable):
    return {"resourceType": "Observation", "code": codeable}

def cc(text=None, codings=None):
    return {"text": text, "coding": codings or []}

def coding(system, code, display=None):
    d = {"system": system, "code": code}
    if display is not None:
        d["display"] = display
    return d


class TestObservationMatcher(unittest.TestCase):

    def setUp(self):
        self.mapper = ObservationCodeMapper()

    def test_direct_loinc_match_same_name(self):
        o1 = obs(cc("Eosinophils, Automated Count",
                    [coding(STANDARD_LOINC, "711-2")]))
        o2 = obs(cc("Eosinophils, Automated Count",
                    [coding(STANDARD_LOINC, "711-2")]))

        self.assertTrue(observations_equivalent(o1, o2, self.mapper))

    def test_direct_loinc_match_different_name_raises(self):
        o1 = obs(cc("Eosinophils, Automated Count",
                    [coding(STANDARD_LOINC, "711-2")]))
        o2 = obs(cc("EOS ABS (AUTO)",
                    [coding(STANDARD_LOINC, "711-2")]))

        with self.assertRaises(NameMismatchError):
            observations_equivalent(o1, o2, self.mapper, raise_on_loinc_name_mismatch=True)

    def test_direct_loinc_match_different_name_allowed_if_flag_off(self):
        o1 = obs(cc("Eosinophils, Automated Count",
                    [coding(STANDARD_LOINC, "711-2")]))
        o2 = obs(cc("EOS ABS (AUTO)",
                    [coding(STANDARD_LOINC, "711-2")]))

        self.assertTrue(
            observations_equivalent(o1, o2, self.mapper, raise_on_loinc_name_mismatch=False)
        )

    def test_learn_mapping_then_match_local_to_loinc(self):
        # First observation teaches that local code maps to LOINC 711-2
        o_teach = obs(cc("Eosinophils, Automated Count", [
            coding(STANDARD_LOINC, "711-2"),
            coding("urn:oid:1.2.3.4", "2000395"),
        ]))
        # Learn from it
        observations_equivalent(o_teach, o_teach, self.mapper)

        # Now an obs with only the local code should match an obs with only the LOINC
        o_local_only = obs(cc("Eosinophils, Automated Count", [
            coding("urn:oid:1.2.3.4", "2000395"),
        ]))
        o_loinc_only = obs(cc("Eosinophils, Automated Count", [
            coding(STANDARD_LOINC, "711-2"),
        ]))

        self.assertTrue(observations_equivalent(o_local_only, o_loinc_only, self.mapper))

    def test_no_loinc_and_no_mapping_returns_false(self):
        o1 = obs(cc("Random Test", [coding("urn:oid:x", "X1")]))
        o2 = obs(cc("Random Test", [coding("urn:oid:y", "Y1")]))
        self.assertFalse(observations_equivalent(o1, o2, self.mapper))

    def test_optional_text_fallback(self):
        # No LOINCs and no mapping, but semantically similar names
        o1 = obs(cc("Eosinophils Automated Count", [coding("urn:oid:x", "X1")]))
        o2 = obs(cc("eosinophils, automated count", [coding("urn:oid:y", "Y1")]))
        self.assertTrue(
            observations_equivalent(o1, o2, self.mapper, enable_text_fallback=True, text_similarity_threshold=0.8)
        )

if __name__ == "__main__":
    unittest.main()