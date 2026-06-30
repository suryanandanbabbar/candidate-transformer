from typing import Any

from candidate_transformer.interfaces.strategy import EntityResolutionStrategy
from candidate_transformer.strategies.registry import strategy_registry


@strategy_registry("deterministic_entity_resolution")
class DeterministicEntityResolutionStrategy(EntityResolutionStrategy):
    """
    Matches two intermediate candidate records deterministically based on a strict priority:
    1. Exact Phone match (if both have at least one intersecting normalized phone)
    2. Exact Email match (if both have at least one intersecting normalized email)
    3. Exact Name match (if both have the same non-empty normalized name)
    """

    def _normalize_name(self, name: str) -> dict[str, Any]:
        import re
        clean_name = re.sub(r'[^\w\s]', '', str(name).lower()).strip()
        tokens = clean_name.split()
        if not tokens:
            return {}
        
        nicknames = {
            "bob": "robert",
            "bill": "william",
            "dick": "richard",
            "chuck": "charles",
            "jim": "james",
            "dave": "david",
            "tom": "thomas",
            "mike": "michael",
            "andy": "andrew"
        }
        
        first = tokens[0]
        first = nicknames.get(first, first)
        last = tokens[-1] if len(tokens) > 1 else ""
        
        middle = []
        if len(tokens) > 2:
            middle = tokens[1:-1]
            
        return {"first": first, "last": last, "middle": middle, "tokens": tokens}

    def _names_match(self, name_a: str, name_b: str) -> bool:
        if not name_a or not name_b:
            return False
            
        norm_a = self._normalize_name(name_a)
        norm_b = self._normalize_name(name_b)
        
        if not norm_a or not norm_b:
            return False
            
        if not norm_a["last"] and not norm_b["last"]:
            return norm_a["first"] == norm_b["first"]
            
        if norm_a["first"] != norm_b["first"] or norm_a["last"] != norm_b["last"]:
            return False
            
        mid_a = norm_a.get("middle", [])
        mid_b = norm_b.get("middle", [])
        
        if mid_a and mid_b:
            m_a = mid_a[0]
            m_b = mid_b[0]
            if len(m_a) == 1 or len(m_b) == 1:
                if m_a[0] != m_b[0]:
                    return False
            else:
                if m_a != m_b:
                    return False
                    
        return True

    def match(self, record_a: dict[str, Any], record_b: dict[str, Any]) -> bool:
        # 1. Phone Match
        phones_a = set(record_a.get("phones") or [])
        phones_b = set(record_b.get("phones") or [])
        if phones_a and phones_b and not phones_a.isdisjoint(phones_b):
            return True

        # 2. Email Match
        emails_a = set(record_a.get("emails") or [])
        emails_b = set(record_b.get("emails") or [])
        if emails_a and emails_b and not emails_a.isdisjoint(emails_b):
            return True

        # 3. Exact Name Match
        if self._names_match(record_a.get("full_name"), record_b.get("full_name")):
            return True

        return False
