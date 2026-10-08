import argparse
import json
import logging
from typing import List

from mdm_engine import (
    Record, Condition, SourcePairPolicy,
    ClusterMembershipConstraint, EvaluatorEngine
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def parse_policies(config_data: dict) -> List[SourcePairPolicy]:
    policies = []
    for pol_cfg in config_data.get('policies', []):
        left_source = pol_cfg['left_source']
        right_source = pol_cfg['right_source']

        mandatory_gates = []
        for gate_cfg in pol_cfg.get('mandatory_gates', []):
            mandatory_gates.append(
                Condition(
                    field=gate_cfg['field'],
                    operator=gate_cfg['operator'],
                    threshold=gate_cfg.get('threshold'),
                    algorithm=gate_cfg.get('algorithm', 'Cosine'),
                    tokenizer=gate_cfg.get('tokenizer', 'Default'),
                    is_null_check=gate_cfg.get('is_null_check', False)
                )
            )

        qualifying_clauses = []
        for clause_grp_cfg in pol_cfg.get('qualifying_clauses', []):
            clause_grp = []
            for cond_cfg in clause_grp_cfg:
                clause_grp.append(
                    Condition(
                        field=cond_cfg['field'],
                        operator=cond_cfg['operator'],
                        threshold=cond_cfg.get('threshold'),
                        algorithm=cond_cfg.get('algorithm', 'Cosine'),
                        tokenizer=cond_cfg.get('tokenizer', 'Default'),
                        is_null_check=cond_cfg.get('is_null_check', False)
                    )
                )
            qualifying_clauses.append(clause_grp)

        policies.append(SourcePairPolicy(left_source, right_source, mandatory_gates, qualifying_clauses))

    return policies

def parse_constraints(config_data: dict) -> List[ClusterMembershipConstraint]:
    constraints = []
    for const_cfg in config_data.get('constraints', []):
        constraints.append(
            ClusterMembershipConstraint(
                target_source=const_cfg['target_source'],
                max_records=const_cfg['max_records']
            )
        )
    return constraints

def load_records(records_data: list) -> List[Record]:
    records = []
    for rec_data in records_data:
        records.append(
            Record(
                record_id=rec_data['record_id'],
                source=rec_data['source'],
                attributes=rec_data['attributes']
            )
        )
    return records

def process_batch(config_path: str, data_path: str):
    logging.info(f"Loading configuration from {config_path}")
    with open(config_path, 'r') as f:
        config_data = json.load(f)

    policies = parse_policies(config_data)
    constraints = parse_constraints(config_data)

    engine = EvaluatorEngine(policies, constraints)

    logging.info(f"Loading data from {data_path}")
    with open(data_path, 'r') as f:
        records_data = json.load(f)

    records = load_records(records_data)

    # Naive clustering: start with each record in its own cluster
    # Then attempt to merge clusters if pairs match and constraints allow

    clusters = [[r] for r in records]

    merged = True
    while merged:
        merged = False
        for i in range(len(clusters)):
            for j in range(i + 1, len(clusters)):
                cluster_a = clusters[i]
                cluster_b = clusters[j]

                # Check if any record in A matches any in B
                pair_match = False
                for r_a in cluster_a:
                    for r_b in cluster_b:
                        if engine.evaluate_pair(r_a, r_b):
                            pair_match = True
                            break
                    if pair_match:
                        break

                if pair_match:
                    proposed_cluster = cluster_a + cluster_b
                    if engine.validate_cluster(proposed_cluster):
                        logging.info(f"Merging clusters: {[r.record_id for r in cluster_a]} and {[r.record_id for r in cluster_b]}")
                        clusters[i] = proposed_cluster
                        del clusters[j]
                        merged = True
                        break
            if merged:
                break

    logging.info("Clustering complete. Resulting clusters:")
    for idx, cluster in enumerate(clusters):
        logging.info(f"Cluster {idx}: {[r.record_id for r in cluster]}")

    return clusters

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run MDM Data Processing Batch")
    parser.add_argument("--config", type=str, required=True, help="Path to JSON configuration file (policies & constraints)")
    parser.add_argument("--data", type=str, required=True, help="Path to JSON data file (records)")
    args = parser.parse_args()

    process_batch(args.config, args.data)
