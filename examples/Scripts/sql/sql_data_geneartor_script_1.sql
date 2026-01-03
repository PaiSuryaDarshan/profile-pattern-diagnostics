-- =========================================================
-- SQL Data Generator Script for PPD cohort_example_test DB
-- =========================================================
-- PPD Cohort Example DB (SQLite)
-- 10 candidates
-- 6 groups
-- Full dimension coverage per candidate
-- Long-format scores table
-- Includes BOTH: raw_score (1–5) and norm_score (0–1)
-- =========================================================
-- (Run in terminal)
-- sqlite3 examples/input/cohort_example_test.db
-- =========================================================
-- Clean slate
-- =========================================================
-- =========================================================
-- PPD Cohort Example DB (SQLite) — RAW + NORM
-- 10 candidates, 37 dimensions, 370 rows
-- norm_score is ALWAYS raw_score / 5 (generated)
-- =========================================================
DROP TABLE IF EXISTS scores;
DROP TABLE IF EXISTS dimensions;
DROP TABLE IF EXISTS candidates;
CREATE TABLE candidates (
    candidate_id TEXT PRIMARY KEY,
    display_name TEXT,
    phone_number TEXT,
    linkedin_tag TEXT
);
CREATE TABLE dimensions (
    dimension_key TEXT PRIMARY KEY,
    group_key TEXT NOT NULL,
    dimension_name TEXT NOT NULL
);
-- norm_score is generated from raw_score (SQLite 3.31+)
CREATE TABLE scores (
    candidate_id TEXT NOT NULL,
    dimension_key TEXT NOT NULL,
    raw_score REAL NOT NULL CHECK (
        raw_score >= 1.0
        AND raw_score <= 5.0
    ),
    norm_score REAL GENERATED ALWAYS AS (raw_score / 5.0) STORED,
    PRIMARY KEY (candidate_id, dimension_key),
    FOREIGN KEY (candidate_id) REFERENCES candidates(candidate_id),
    FOREIGN KEY (dimension_key) REFERENCES dimensions(dimension_key)
);
CREATE INDEX idx_scores_dimension ON scores(dimension_key);
CREATE INDEX idx_scores_candidate ON scores(candidate_id);
-- =========================================================
-- DIMENSIONS (37)
-- =========================================================
INSERT INTO dimensions (dimension_key, group_key, dimension_name)
VALUES (
        'communication_skills::grammar',
        'communication_skills',
        'grammar'
    ),
    (
        'communication_skills::comprehension',
        'communication_skills',
        'comprehension'
    ),
    (
        'communication_skills::fluency',
        'communication_skills',
        'fluency'
    ),
    (
        'communication_skills::vocabulary_sufficiency',
        'communication_skills',
        'vocabulary_sufficiency'
    ),
    (
        'communication_skills::coherence',
        'communication_skills',
        'coherence'
    ),
    (
        'cognitive_insights::logical_reasoning',
        'cognitive_insights',
        'logical_reasoning'
    ),
    (
        'cognitive_insights::critical_thinking',
        'cognitive_insights',
        'critical_thinking'
    ),
    (
        'cognitive_insights::problem_solving',
        'cognitive_insights',
        'problem_solving'
    ),
    (
        'cognitive_insights::big_picture_thinking',
        'cognitive_insights',
        'big_picture_thinking'
    ),
    (
        'cognitive_insights::insightfulness',
        'cognitive_insights',
        'insightfulness'
    ),
    (
        'cognitive_insights::decision_making',
        'cognitive_insights',
        'decision_making'
    ),
    (
        'cognitive_insights::intellectual_self_awareness',
        'cognitive_insights',
        'intellectual_self_awareness'
    ),
    (
        'cognitive_insights::clarity',
        'cognitive_insights',
        'clarity'
    ),
    (
        'analytical_quantitative_skills::numerical_reasoning',
        'analytical_quantitative_skills',
        'numerical_reasoning'
    ),
    (
        'analytical_quantitative_skills::data_interpretation',
        'analytical_quantitative_skills',
        'data_interpretation'
    ),
    (
        'analytical_quantitative_skills::pattern_recognition',
        'analytical_quantitative_skills',
        'pattern_recognition'
    ),
    (
        'analytical_quantitative_skills::estimation_accuracy',
        'analytical_quantitative_skills',
        'estimation_accuracy'
    ),
    (
        'analytical_quantitative_skills::quantitative_consistency',
        'analytical_quantitative_skills',
        'quantitative_consistency'
    ),
    (
        'analytical_quantitative_skills::error_rate_under_time_pressure',
        'analytical_quantitative_skills',
        'error_rate_under_time_pressure'
    ),
    (
        'problem_structuring_framework_use::issue_decomposition_quality',
        'problem_structuring_framework_use',
        'issue_decomposition_quality'
    ),
    (
        'problem_structuring_framework_use::prioritisation_accuracy',
        'problem_structuring_framework_use',
        'prioritisation_accuracy'
    ),
    (
        'problem_structuring_framework_use::logical_sequencing',
        'problem_structuring_framework_use',
        'logical_sequencing'
    ),
    (
        'problem_structuring_framework_use::assumption_identification',
        'problem_structuring_framework_use',
        'assumption_identification'
    ),
    (
        'problem_structuring_framework_use::constraint_recognition',
        'problem_structuring_framework_use',
        'constraint_recognition'
    ),
    (
        'problem_structuring_framework_use::objective_alignment',
        'problem_structuring_framework_use',
        'objective_alignment'
    ),
    (
        'execution_task_reliability::instruction_adherence',
        'execution_task_reliability',
        'instruction_adherence'
    ),
    (
        'execution_task_reliability::deadline_compliance',
        'execution_task_reliability',
        'deadline_compliance'
    ),
    (
        'execution_task_reliability::output_completeness',
        'execution_task_reliability',
        'output_completeness'
    ),
    (
        'execution_task_reliability::error_density',
        'execution_task_reliability',
        'error_density'
    ),
    (
        'execution_task_reliability::follow_through_consistency',
        'execution_task_reliability',
        'follow_through_consistency'
    ),
    (
        'execution_task_reliability::task_closure_reliability',
        'execution_task_reliability',
        'task_closure_reliability'
    ),
    (
        'collaboration_professional_interaction::turn_taking_balance',
        'collaboration_professional_interaction',
        'turn_taking_balance'
    ),
    (
        'collaboration_professional_interaction::listening_to_speaking_ratio',
        'collaboration_professional_interaction',
        'listening_to_speaking_ratio'
    ),
    (
        'collaboration_professional_interaction::idea_integration_rate',
        'collaboration_professional_interaction',
        'idea_integration_rate'
    ),
    (
        'collaboration_professional_interaction::respectful_disagreement_handling',
        'collaboration_professional_interaction',
        'respectful_disagreement_handling'
    ),
    (
        'collaboration_professional_interaction::role_appropriateness',
        'collaboration_professional_interaction',
        'role_appropriateness'
    ),
    (
        'collaboration_professional_interaction::professional_conduct_consistency',
        'collaboration_professional_interaction',
        'professional_conduct_consistency'
    );
-- =========================================================
-- CANDIDATES (10)
-- =========================================================
INSERT INTO candidates (
        candidate_id,
        display_name,
        phone_number,
        linkedin_tag
    )
VALUES (
        'C001',
        'Aarav Patel',
        '+91-9876543210',
        'aarav-patel'
    ),
    (
        'C002',
        'Neha Sharma',
        '+91-9123456780',
        'neha-sharma'
    ),
    ('C003', 'Rohan Iyer', '+91-9988776655', NULL),
    ('C004', 'Priya Nair', NULL, 'priya-nair'),
    ('C005', 'Karan Malhotra', '+91-9090909090', NULL),
    (
        'C006',
        'Alex Turner',
        '+44-7700123456',
        'alex-turner'
    ),
    ('C007', 'Emily Chen', NULL, 'emily-chen'),
    ('C008', 'Daniel Ruiz', '+34-612345678', NULL),
    ('C009', 'Sara Müller', NULL, 'sara-muller'),
    (
        'C010',
        'Liam O''Connor',
        '+353-851234567',
        'liam-oconnor'
    );
-- =========================================================
-- SCORES (seed baseline per candidate)
-- Inserts 10×37 rows: one raw_score per candidate replicated across all dimensions
-- norm_score auto-computed.
-- =========================================================
INSERT INTO scores (candidate_id, dimension_key, raw_score)
SELECT c.candidate_id,
    d.dimension_key,
    CASE
        c.candidate_id
        WHEN 'C001' THEN 4.2
        WHEN 'C002' THEN 3.8
        WHEN 'C003' THEN 4.5
        WHEN 'C004' THEN 2.7
        WHEN 'C005' THEN 3.6
        WHEN 'C006' THEN 4.1
        WHEN 'C007' THEN 3.9
        WHEN 'C008' THEN 4.4
        WHEN 'C009' THEN 3.5
        WHEN 'C010' THEN 4.8
        ELSE 4.0
    END
FROM candidates c
    CROSS JOIN dimensions d;
-- =========================================================
-- Sanity checks
-- =========================================================
-- SELECT COUNT(*) FROM candidates;   -- 10
-- SELECT COUNT(*) FROM dimensions;   -- 37
-- SELECT COUNT(*) FROM scores;       -- 370