-- SQLite queries executed against report_source.sqlite.
-- The database is materialized by scripts/build_eg13_validation_report_source.py
-- from the saved EG13 reproduction JSON/CSVs and anonymous package manifest.

SELECT main_accuracy, gain_pp, scenes, relations,
       selected_collision_pairs, collision_delta
FROM headline;

SELECT method, accuracy, satisfied, relations, role, display_order AS "order"
FROM comparison
ORDER BY display_order;

SELECT display_order AS "order", control, accuracy, gain_pp,
       ci_low_pp, ci_high_pp, supported
FROM controls
ORDER BY display_order;

SELECT display_order AS "order", room, scenes, relations,
       baseline, main, gain_pp
FROM rooms
ORDER BY display_order;

SELECT display_order AS "order", check_name AS "check",
       comparisons, failures, result
FROM quality
ORDER BY display_order;
