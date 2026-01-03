-- =========================================================
-- PPD cohort_diverse_example.db (REMADE) — pattern-diverse seed
-- =========================================================
-- Goal:
--   Build a SQLite DB where DIFFERENT candidates reliably trigger
--   DIFFERENT pattern flags across groups:
--     - uniform_high
--     - uniform_low
--     - balanced
--     - bottlenecked
--     - polarised (two-tail: low + high)
--     - noisy (high within-group dispersion WITHOUT low-tail)
--
-- Notes:
--   • raw_score: 1–5
--   • norm_score: raw_score / 5 (stored, not generated)
--   • Patterns are computed on NORMALISED scores in your pipeline.
--   • This seed uses strong extremes to be robust to typical taus.
--
-- Run:
--   sqlite3 profile-pattern-diagnostics/examples/input/cohort_diverse_example.db < this_file.sql
-- =========================================================
DROP TABLE IF EXISTS scores;
DROP TABLE IF EXISTS dimensions;
DROP TABLE IF EXISTS candidates;
-- =========================
-- Candidates
-- =========================
CREATE TABLE candidates (
    candidate_id TEXT PRIMARY KEY,
    display_name TEXT,
    phone_number TEXT,
    linkedin_tag TEXT
);
-- =========================
-- Dimensions (frozen schema)
-- =========================
CREATE TABLE dimensions (
    dimension_key TEXT PRIMARY KEY,
    group_key TEXT NOT NULL,
    dimension_name TEXT NOT NULL
);
-- =========================
-- Scores (long format)
-- =========================
CREATE TABLE scores (
    candidate_id TEXT NOT NULL,
    dimension_key TEXT NOT NULL,
    raw_score REAL NOT NULL CHECK (
        raw_score >= 1.0
        AND raw_score <= 5.0
    ),
    norm_score REAL NOT NULL CHECK (
        norm_score >= 0.0
        AND norm_score <= 1.0
    ),
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
VALUES -- 1) communication_skills (5)
    (
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
    -- 2) cognitive_insights (8)
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
    -- 3) analytical_quantitative_skills (6)
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
    -- 4) problem_structuring_framework_use (6)
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
    -- 5) execution_task_reliability (6)
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
    -- 6) collaboration_professional_interaction (6)
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
-- (names optional; pattern intention in comments)
-- =========================================================
INSERT INTO candidates (
        candidate_id,
        display_name,
        phone_number,
        linkedin_tag
    )
VALUES ('C001', 'Uniform High (All Groups)', NULL, NULL),
    -- uniform_high everywhere
    ('C002', 'Uniform Low (All Groups)', NULL, NULL),
    -- uniform_low everywhere
    ('C003', 'Polarised (Cognitive)', NULL, NULL),
    -- polarised in cognitive_insights
    ('C004', 'Bottleneck (Execution)', NULL, NULL),
    -- bottlenecked in execution_task_reliability
    ('C005', 'Noisy (Framework)', NULL, NULL),
    -- noisy in problem_structuring_framework_use
    ('C006', 'Balanced (All Groups)', NULL, NULL),
    -- balanced everywhere (mid, low std)
    ('C007', 'Polarised (Communication)', NULL, NULL),
    -- polarised in communication_skills
    ('C008', 'Bottleneck (Analytical)', NULL, NULL),
    -- bottlenecked in analytical_quantitative_skills
    ('C009', 'Noisy (Collaboration)', NULL, NULL),
    -- noisy in collaboration_professional_interaction
    ('C010', 'Mixed Sanity (Mostly High)', NULL, NULL);
-- mostly high, but not perfectly uniform
-- =========================================================
-- SCORES (10 × 37)
-- Raw pattern recipes (robust extremes)
-- =========================================================
-- =========================================================
-- SCORES (10 × 37) — pattern-diverse
-- =========================================================
WITH raw AS (
    SELECT c.candidate_id,
        d.dimension_key,
        CASE
            -- C001: uniform_high everywhere
            WHEN c.candidate_id = 'C001' THEN 4.9 -- C002: uniform_low everywhere
            WHEN c.candidate_id = 'C002' THEN 1.4 -- C003: polarised in cognitive_insights (two-tail)
            WHEN c.candidate_id = 'C003' THEN CASE
                WHEN d.group_key = 'cognitive_insights' THEN CASE
                    WHEN d.dimension_name IN ('critical_thinking', 'decision_making') THEN 1.3
                    WHEN d.dimension_name IN (
                        'logical_reasoning',
                        'problem_solving',
                        'insightfulness'
                    ) THEN 5.0
                    ELSE 4.5
                END
                ELSE 4.3
            END -- C004: bottlenecked in execution_task_reliability
            WHEN c.candidate_id = 'C004' THEN CASE
                WHEN d.group_key = 'execution_task_reliability' THEN CASE
                    WHEN d.dimension_name = 'error_density' THEN 1.5
                    ELSE 4.7
                END
                ELSE 4.2
            END -- C005: noisy in problem_structuring_framework_use (no extreme low tail)
            WHEN c.candidate_id = 'C005' THEN CASE
                WHEN d.group_key = 'problem_structuring_framework_use' THEN CASE
                    WHEN d.dimension_name IN (
                        'issue_decomposition_quality',
                        'objective_alignment'
                    ) THEN 4.9
                    WHEN d.dimension_name IN (
                        'assumption_identification',
                        'constraint_recognition'
                    ) THEN 3.0
                    ELSE 4.4
                END
                ELSE 4.1
            END -- C006: balanced everywhere (mid, tight)
            WHEN c.candidate_id = 'C006' THEN CASE
                WHEN d.group_key = 'cognitive_insights' THEN 3.6
                WHEN d.group_key = 'communication_skills' THEN 3.7
                WHEN d.group_key = 'analytical_quantitative_skills' THEN 3.6
                WHEN d.group_key = 'problem_structuring_framework_use' THEN 3.7
                WHEN d.group_key = 'execution_task_reliability' THEN 3.6
                WHEN d.group_key = 'collaboration_professional_interaction' THEN 3.7
                ELSE 3.6
            END -- C007: polarised in communication_skills
            WHEN c.candidate_id = 'C007' THEN CASE
                WHEN d.group_key = 'communication_skills' THEN CASE
                    WHEN d.dimension_name IN ('grammar', 'coherence') THEN 1.2
                    WHEN d.dimension_name IN ('fluency', 'comprehension') THEN 5.0
                    ELSE 4.4
                END
                ELSE 4.2
            END -- C008: bottlenecked in analytical_quantitative_skills
            WHEN c.candidate_id = 'C008' THEN CASE
                WHEN d.group_key = 'analytical_quantitative_skills' THEN CASE
                    WHEN d.dimension_name = 'estimation_accuracy' THEN 1.6
                    ELSE 4.8
                END
                ELSE 4.2
            END -- C009: noisy in collaboration_professional_interaction (no extreme low tail)
            WHEN c.candidate_id = 'C009' THEN CASE
                WHEN d.group_key = 'collaboration_professional_interaction' THEN CASE
                    WHEN d.dimension_name IN (
                        'turn_taking_balance',
                        'respectful_disagreement_handling'
                    ) THEN 4.9
                    WHEN d.dimension_name IN ('role_appropriateness', 'idea_integration_rate') THEN 3.1
                    ELSE 4.4
                END
                ELSE 4.1
            END -- C010: mostly high, not perfectly uniform
            WHEN c.candidate_id = 'C010' THEN CASE
                WHEN d.group_key = 'communication_skills' THEN CASE
                    WHEN d.dimension_name = 'vocabulary_sufficiency' THEN 4.2
                    ELSE 4.7
                END
                WHEN d.group_key = 'cognitive_insights' THEN CASE
                    WHEN d.dimension_name = 'intellectual_self_awareness' THEN 3.8
                    ELSE 4.6
                END
                ELSE 4.5
            END
            ELSE 4.0
        END AS raw_score
    FROM candidates c
        CROSS JOIN dimensions d
)
INSERT INTO scores (
        candidate_id,
        dimension_key,
        raw_score,
        norm_score
    )
SELECT candidate_id,
    dimension_key,
    raw_score,
    raw_score / 5.0
FROM raw;
-- =========================================================
-- Sanity checks
-- =========================================================
-- SELECT COUNT(*) FROM candidates;   -- 10
-- SELECT COUNT(*) FROM dimensions;   -- 37
-- SELECT COUNT(*) FROM scores;       -- 370
--
-- Spot-check extremes:
-- SELECT candidate_id, MIN(norm_score), MAX(norm_score), MAX(norm_score)-MIN(norm_score)
-- FROM scores GROUP BY candidate_id ORDER BY candidate_id;