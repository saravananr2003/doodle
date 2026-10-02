import math
from typing import List, Dict, Any, Optional, Set, Callable
from collections import Counter

# --- Tokenizers ---
def tokenize_default(text: str) -> List[str]:
    if text is None:
        return []
    return str(text).split()

def tokenize_ngram(text: str, n: int) -> List[str]:
    if text is None:
        return []
    s = str(text)
    if len(s) < n:
        return [s]
    return [s[i:i+n] for i in range(len(s) - n + 1)]

def tokenize_bigram(text: str) -> List[str]:
    return tokenize_ngram(text, 2)

def tokenize_trigram(text: str) -> List[str]:
    return tokenize_ngram(text, 3)

TOKENIZERS = {
    'Default': tokenize_default,
    'Bigram': tokenize_bigram,
    'Trigram': tokenize_trigram
}

# --- Algorithms ---
def calc_jaccard(tokens1: List[str], tokens2: List[str]) -> float:
    if not tokens1 and not tokens2:
        return 1.0
    if not tokens1 or not tokens2:
        return 0.0
    set1, set2 = set(tokens1), set(tokens2)
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    return float(intersection) / union if union > 0 else 0.0

def calc_cosine(tokens1: List[str], tokens2: List[str]) -> float:
    if not tokens1 and not tokens2:
        return 1.0
    if not tokens1 or not tokens2:
        return 0.0
    count1 = Counter(tokens1)
    count2 = Counter(tokens2)
    intersection = set(count1.keys()) & set(count2.keys())
    numerator = sum([count1[x] * count2[x] for x in intersection])

    sum1 = sum([count1[x]**2 for x in count1.keys()])
    sum2 = sum([count2[x]**2 for x in count2.keys()])
    denominator = math.sqrt(sum1) * math.sqrt(sum2)

    if not denominator:
        return 0.0
    else:
        return float(numerator) / denominator

ALGORITHMS = {
    'Jaccard': calc_jaccard,
    'Cosine': calc_cosine
}

# --- Data Models ---
class Record:
    def __init__(self, record_id: str, source: str, attributes: Dict[str, Any]):
        self.record_id = record_id
        self.source = source
        self.attributes = attributes

class Condition:
    def __init__(self, field: str, operator: str, threshold: Optional[float] = None,
                 algorithm: str = 'Cosine', tokenizer: str = 'Default', is_null_check: bool = False):
        """
        field: source field name
        operator: '>','=', '<', 'exact_match'
        threshold: e.g., 0.60 for 60%
        """
        self.field = field
        self.operator = operator
        self.threshold = threshold
        self.algorithm = algorithm
        self.tokenizer = tokenizer
        self.is_null_check = is_null_check

    def evaluate(self, rec1: Record, rec2: Record) -> bool:
        val1 = rec1.attributes.get(self.field)
        val2 = rec2.attributes.get(self.field)

        if self.is_null_check:
            # If the condition specifically checks if BOTH are null
            return val1 is None and val2 is None

        if val1 is None or val2 is None:
            return False

        if self.operator == 'exact_match':
            return val1 == val2

        tok_func = TOKENIZERS.get(self.tokenizer, tokenize_default)
        alg_func = ALGORITHMS.get(self.algorithm, calc_cosine)

        t1 = tok_func(str(val1))
        t2 = tok_func(str(val2))

        score = alg_func(t1, t2)

        if self.operator == '>':
            return score > self.threshold
        elif self.operator == '>=':
            return score >= self.threshold
        elif self.operator == '=':
            # We treat = with threshold (e.g. 1.0) as equality logic for similarity
            return math.isclose(score, self.threshold, rel_tol=1e-9)

        return False

class SourcePairPolicy:
    def __init__(self, left_source: str, right_source: str,
                 mandatory_gates: List[Condition] = None,
                 qualifying_clauses: List[List[Condition]] = None):
        """
        qualifying_clauses: List of OR groups, where each group is a List of AND Conditions.
        """
        self.left_source = left_source
        self.right_source = right_source
        self.mandatory_gates = mandatory_gates or []
        self.qualifying_clauses = qualifying_clauses or []

    def evaluate(self, rec1: Record, rec2: Record) -> bool:
        # Check source match
        if not ((rec1.source == self.left_source and rec2.source == self.right_source) or
                (rec1.source == self.right_source and rec2.source == self.left_source)):
            return False

        # Mandatory gates
        for gate in self.mandatory_gates:
            if not gate.evaluate(rec1, rec2):
                return False

        # Qualifying clauses (OR of ANDs)
        if not self.qualifying_clauses:
            return True

        for clause_group in self.qualifying_clauses:
            clause_passed = True
            for condition in clause_group:
                if not condition.evaluate(rec1, rec2):
                    clause_passed = False
                    break
            if clause_passed:
                return True

        return False


class ClusterMembershipConstraint:
    def __init__(self, target_source: str, max_records: int):
        self.target_source = target_source
        self.max_records = max_records

    def validate(self, cluster: List[Record]) -> bool:
        # Count distinct logical records for target source
        # We assume record_id is the unique identity within the source.
        source_records = [r.record_id for r in cluster if r.source == self.target_source]
        distinct_records = len(set(source_records))

        return distinct_records <= self.max_records

class EvaluatorEngine:
    def __init__(self, policies: List[SourcePairPolicy], constraints: List[ClusterMembershipConstraint]):
        self.policies = policies
        self.constraints = constraints

    def evaluate_pair(self, rec1: Record, rec2: Record) -> bool:
        for policy in self.policies:
            if ((rec1.source == policy.left_source and rec2.source == policy.right_source) or
                (rec1.source == policy.right_source and rec2.source == policy.left_source)):
                if policy.evaluate(rec1, rec2):
                    return True
        return False

    def validate_cluster(self, cluster: List[Record]) -> bool:
        for constraint in self.constraints:
            if not constraint.validate(cluster):
                return False
        return True
