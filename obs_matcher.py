import re
from typing import Dict, Iterable, List, Optional, Set, Tuple

STANDARD_LOINC = "http://loinc.org"


# --- Exceptions --------------------------------------------------------------

class NameMismatchError(Exception):
    """Raised when two observations share a LOINC but their display/text names do not match."""


# --- Helpers ----------------------------------------------------------------

def _norm_system(s: Optional[str]) -> Optional[str]:
    return s.lower() if s else None

def _normalize_text(t: Optional[str]) -> str:
    if not t:
        return ""
    t = t.strip()
    # collapse whitespace, lowercase, strip punctuation-ish dividers
    t = t.lower()
    t = re.sub(r"[\[\]\(\)\.,:/\-_]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t

def _extract_codings(codeable: Dict) -> List[Dict]:
    if not codeable:
        return []
    return list(codeable.get("coding") or [])

def _display_text_from_codeable(codeable: Dict) -> str:
    """Prefer CodeableConcept.text, else first coding.display."""
    if not codeable:
        return ""
    if codeable.get("text"):
        return str(codeable["text"])
    for cg in codeable.get("coding") or []:
        if cg.get("display"):
            return str(cg["display"])
    return ""


# --- Mapping store -----------------------------------------------------------

class ObservationCodeMapper:
    """
    Persistently maps local codes (by system,code) to LOINC codes,
    and remembers normalized display/name synonyms per LOINC.
    """

    def __init__(self) -> None:
        # maps (system, code) -> loinc_code
        self.local_to_loinc: Dict[Tuple[str, str], str] = {}
        # maps loinc_code -> set of normalized names we have seen
        self.loinc_names: Dict[str, Set[str]] = {}

    def learn_from_observation(self, obs: Dict) -> None:
        """
        If the observation has a LOINC in Observation.code.coding, map all
        non-LOINC codings to that LOINC. Also collect name synonyms.
        """
        codeable = (obs or {}).get("code") or {}
        codings = _extract_codings(codeable)
        loincs = {c["code"] for c in codings if _norm_system(c.get("system")) == STANDARD_LOINC and c.get("code")}
        if not loincs:
            return  # nothing to learn without a LOINC anchor
        # If multiple LOINCs appear (rare): choose deterministically (sorted)
        loinc = sorted(loincs)[0]

        # Learn name/synonym
        disp = _normalize_text(_display_text_from_codeable(codeable))
        if disp:
            self.loinc_names.setdefault(loinc, set()).add(disp)

        # Map all non-LOINC codings to this LOINC
        for c in codings:
            sys = _norm_system(c.get("system"))
            val = c.get("code")
            if not sys or not val:
                continue
            if sys == STANDARD_LOINC:
                continue
            self.local_to_loinc[(sys, val)] = loinc

    def mapped_loincs_for_observation(self, obs: Dict) -> Set[str]:
        """
        Return the set of LOINC codes directly present or derivable via learned local mappings.
        """
        codeable = (obs or {}).get("code") or {}
        codings = _extract_codings(codeable)
        loincs: Set[str] = set(c["code"] for c in codings
                               if _norm_system(c.get("system")) == STANDARD_LOINC and c.get("code"))
        # Add mapped LOINCs from learned local mappings
        for c in codings:
            sys = _norm_system(c.get("system"))
            val = c.get("code")
            if not sys or not val:
                continue
            if sys == STANDARD_LOINC:
                continue
            mapped = self.local_to_loinc.get((sys, val))
            if mapped:
                loincs.add(mapped)
        return loincs

    def names_for_observation(self, obs: Dict) -> Set[str]:
        """Return normalized names found in the observation (code.text or first coding.display)."""
        codeable = (obs or {}).get("code") or {}
        disp = _normalize_text(_display_text_from_codeable(codeable))
        return {disp} if disp else set()


# --- Main matcher ------------------------------------------------------------

def observations_equivalent(
    left: Dict,
    right: Dict,
    mapper: ObservationCodeMapper,
    *,
    raise_on_loinc_name_mismatch: bool = True,
    enable_text_fallback: bool = False,
    text_similarity_threshold: float = 0.85,
) -> bool:
    """
    Decide if two FHIR Observations refer to the same test concept.

    Strategy:
      1) Learn from both (populate mapper with any new local->LOINC mappings + names).
      2) If they share a LOINC (directly or via learned mapping), they match.
         - If raise_on_loinc_name_mismatch=True, raise NameMismatchError if names disagree.
      3) Optionally, fallback to text similarity (disabled by default).

    Returns:
        True if equivalent, False otherwise (or raises NameMismatchError).
    """
    # 1) Learn from each side (idempotent)
    mapper.learn_from_observation(left)
    mapper.learn_from_observation(right)

    # 2) Compare by LOINC (direct or mapped)
    left_loincs = mapper.mapped_loincs_for_observation(left)
    right_loincs = mapper.mapped_loincs_for_observation(right)
    shared = left_loincs & right_loincs
    if shared:
        if raise_on_loinc_name_mismatch:
            # If both have a name and the normalized names differ, raise
            left_names = mapper.names_for_observation(left)
            right_names = mapper.names_for_observation(right)
            if left_names and right_names and left_names.isdisjoint(right_names):
                # Only raise if neither name is already known synonym for the other LOINC
                # (You could relax this by using mapper.loinc_names[loinc] in the future.)
                raise NameMismatchError(
                    f"Name mismatch for shared LOINC {sorted(shared)[0]}: "
                    f"{sorted(left_names)} vs {sorted(right_names)}"
                )
        return True

    # 3) Optional text fallback (strict normalization; can be extended to include units/category)
    if enable_text_fallback:
        lt = next(iter(mapper.names_for_observation(left)), "")
        rt = next(iter(mapper.names_for_observation(right)), "")
        if lt and rt:
            # Token Jaccard
            A, B = set(lt.split()), set(rt.split())
            sim = (len(A & B) / len(A | B)) if A and B else 0.0
            return sim >= text_similarity_threshold

    return False