CREATE TABLE IF NOT EXISTS data_products (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    is_active INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS e360_source (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS e360_source_pair_policy (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id VARCHAR(50),
    left_source VARCHAR(50),
    right_source VARCHAR(50),
    FOREIGN KEY (product_id) REFERENCES data_products(id),
    FOREIGN KEY (left_source) REFERENCES e360_source(id),
    FOREIGN KEY (right_source) REFERENCES e360_source(id)
);

CREATE TABLE IF NOT EXISTS e360_policy_condition (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    policy_id INTEGER,
    clause_type VARCHAR(20), -- 'MANDATORY' or 'QUALIFYING'
    clause_group INTEGER, -- For OR conditions in QUALIFYING
    field VARCHAR(100),
    operator VARCHAR(20),
    threshold REAL,
    algorithm VARCHAR(50),
    tokenizer VARCHAR(50),
    is_null_check INTEGER DEFAULT 0,
    FOREIGN KEY (policy_id) REFERENCES e360_source_pair_policy(id)
);

CREATE TABLE IF NOT EXISTS e360_cluster_membership_constraint (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id VARCHAR(50),
    target_source VARCHAR(50),
    max_records INTEGER,
    FOREIGN KEY (product_id) REFERENCES data_products(id),
    FOREIGN KEY (target_source) REFERENCES e360_source(id)
);
