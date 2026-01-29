ALTER TABLE "function"
  DROP CONSTRAINT IF EXISTS fk_function_user;

ALTER TABLE "function"
  ALTER COLUMN created_by DROP NOT NULL;

ALTER TABLE "function"
  ALTER COLUMN created_at DROP NOT NULL;

ALTER TABLE function_parameter ALTER COLUMN type TYPE VARCHAR(255);

ALTER TABLE function_parameter
  DROP CONSTRAINT IF EXISTS function_parameter_type_check;

ALTER TABLE function_parameter
  DROP COLUMN IF EXISTS type;

ALTER TABLE function_parameter
  ADD COLUMN IF NOT EXISTS type jsonb;


INSERT INTO function (id, name, description) VALUES
(1, 'flagIsolated', 'Find and flag temporally isolated data groups.'),
(2, 'flagJumps', 'Flag jumps and drops in data where the mean significantly changes.'),
(3, 'flagOffset', 'Detect and flag spikes or offset value courses in data.'),
(4, 'flagPlateau', 'Flag anomalous value plateaus in a time series.'),
(5, 'flagRange', 'Flag values exceeding the given min-max interval.'),
(6, 'flagAll', 'Set the given flag at all unflagged positions.'),
(7, 'flagUniLOF', 'Flag outliers using univariate Local Outlier Factor (LOF).'),
(8, 'flagZScore', 'Flag data points where (rolling) Z-score exceeds threshold.'),
(9, 'flagByScatterLowpass', 'Flag data chunks exceeding a deviation threshold.'),
(10, 'propagateFlags', 'Extend existing flags to preceding or subsequent values.'),
(11, 'renameField', 'Rename field to the given name.'),
(12, 'rolling', 'Calculate a rolling-window function on the data.'),
(13, 'transferFlags', 'Transfer flags from one variable to another.');

DO $$
DECLARE
    offset_type jsonb := '{"type": "offset", "constraint": {"regex": "^(\\d+)?(Y|YS|A|AS|Q|QS|M|MS|W(-MON|-TUE|-WED|-THU|-FRI|-SAT|-SUN)?|SM|SMS|D|B|C|BM|BMS|BQ|BQS|BY|BYS|CBM|CBMS|CQ|CQS|H|T|min|S|L|ms|U|us|N)$"}}';
    int_type jsonb := '{"type": "int", "constraint": {}}';
    int_gt_0_type jsonb := '{"type": "int", "constraint": {"min": 1}}';
    int_ge_0_type jsonb := '{"type": "int", "constraint": {"min": 0}}';
    float_type jsonb := '{"type": "float", "constraint": {}}';
    float_ge_0_type jsonb := '{"type": "float", "constraint": {"min": 0}}';
    float_ge_0_le_1_type jsonb := '{"type": "float", "constraint": {"min": 0, "max": 1}}';
    bool_type jsonb := '{"type": "bool", "constraint": {}}';
    str_type jsonb := '{"type": "str", "constraint": {}}';
BEGIN
    INSERT INTO function_parameter
        (function_id, name, description, optional, "type", default_value, position)
    VALUES
        -- flagIsolated
        (1, 'gap_window', 'Minimum gap size required before and after a group to consider it isolated.', FALSE, json_build_array(offset_type), NULL, 1),
        (1, 'group_window', 'Maximum size of a data chunk to consider for isolation.', FALSE, json_build_array(offset_type), NULL, 2),
        -- flagJumps
        (2, 'thresh', 'Threshold for mean difference between adjacent windows to trigger flagging.', FALSE, json_build_array(float_ge_0_type), NULL, 1),
        (2, 'window', 'Size of the rolling windows used to calculate the mean.', FALSE, json_build_array(offset_type), NULL, 2),
        (2, 'min_periods', 'Minimum observations required for a valid mean calculation.', TRUE, json_build_array(int_ge_0_type), '0', 3),
        -- flagOffset
        (3, 'tolerance', 'Maximum allowed difference between preceding and succeeding values.', FALSE, json_build_array(float_ge_0_type), NULL, 1),
        (3, 'window', 'Maximum duration for the offset sequence.', FALSE, json_build_array(offset_type), NULL, 2),
        (3, 'thresh', 'Minimum absolute difference to consider a sequence as an offset.', TRUE, json_build_array(float_ge_0_type), NULL, 3),
        (3, 'thresh_relative', 'Minimum relative change to consider a sequence as an offset.', TRUE, json_build_array(float_type), NULL, 4),
        -- flagPlateau
        (4, 'min_length', 'Minimum temporal extension of a plateau.', FALSE, json_build_array(int_gt_0_type, offset_type), NULL, 1),
        (4, 'max_length', 'Maximum temporal extension of a plateau.', TRUE, json_build_array(int_gt_0_type, offset_type), NULL, 2),
        (4, 'min_jump', 'Minimum difference from preceding/succeeding periods.', TRUE, json_build_array(float_ge_0_type), NULL, 3),
        (4, 'granularity', 'Precision of the search.', TRUE, json_build_array(int_gt_0_type, offset_type), NULL, 4),
        -- flagRange
        (5, 'min', 'Lower bound for valid data.', FALSE, json_build_array(float_type), NULL, 1),
        (5, 'max', 'Upper bound for valid data.', FALSE, json_build_array(float_type), NULL, 2),
        -- flagUniLOF
        (7, 'n', 'Number of periods to include in LOF calculation.', TRUE, json_build_array(int_type), '20', 1),
        (7, 'thresh', 'LOF cutoff value.', TRUE, json_build_array(float_ge_0_type, '{"type": "enum", "constraint": {"only": ["auto"]}}'::jsonb), 'auto', 2),
        (7, 'probability', 'Outlier probability cutoff.', TRUE, json_build_array(float_ge_0_le_1_type), NULL, 3),
        (7, 'corruption', 'Portion or count of data considered anomalous.', TRUE, json_build_array(float_ge_0_le_1_type, int_gt_0_type), NULL, 4),
        (7, 'algorithm', 'Algorithm for nearest neighbor calculation.', TRUE, json_build_array('{"type": "enum", "constraint": {"only": ["ball_tree", "kd_tree", "brute", "auto"]}}'::jsonb), 'ball_tree', 5),
        (7, 'p', 'Minkowski metric degree.', TRUE, json_build_array(int_gt_0_type), '1', 6),
        (7, 'density', 'Temporal density calculation.', TRUE, json_build_array(float_ge_0_type, '{"type": "enum", "constraint": {"only": ["auto"]}}'::jsonb), 'auto', 7),
        (7, 'fill_na', 'Fill NaNs via interpolation if True.', TRUE, json_build_array(bool_type), 'true', 8),
        (7, 'slope_correct', 'Remove clusters caused by steep slopes.', TRUE, json_build_array(bool_type), 'true', 9),
        (7, 'min_offset', 'Minimum value jump before and after clusters to flag.', TRUE, json_build_array(float_ge_0_type), NULL, 10),
        -- flagZScore
        (8, 'method', '''standard'' or ''modified'' Z-score calculation.', TRUE, json_build_array('{"type": "enum", "constraint": {"only": ["standard", "modified"]}}'::jsonb), NULL, 1),
        (8, 'window', 'Rolling window size.', TRUE, json_build_array(int_gt_0_type, offset_type), NULL, 2),
        (8, 'thresh', 'Z-score threshold.', TRUE, json_build_array(float_ge_0_type), '3', 3),
        (8, 'min_residuals', 'Minimum residual to consider a point as outlier.', TRUE, json_build_array(float_ge_0_type), NULL, 4),
        (8, 'min_periods', 'Minimum valid points in a window.', TRUE, json_build_array(int_gt_0_type), NULL, 5),
        (8, 'center', 'Whether to center the window.', TRUE, json_build_array(bool_type), 'true', 6),
        (8, 'axis', 'Axis along which scoring is applied.', TRUE, json_build_array('{"type": "int", "constraint": {"min": 0, "max": 1}}'::jsonb), '0', 7),
        -- flagByScatterLowpass
        (9, 'window', 'Chunk size for evaluation.', FALSE, json_build_array(offset_type), NULL, 1),
        (9, 'thresh', 'Threshold for chunk deviation.', FALSE, json_build_array(float_ge_0_type), NULL, 2),
        (9, 'func', 'Aggregation function for chunk evaluation.', TRUE, json_build_array('{"type": "enum", "constraint": {"only": ["std","var","mad"]}}'::jsonb), 'std', 3),
        (9, 'sub_window', 'Window size for sub-chunks.', TRUE, json_build_array(offset_type), NULL, 4),
        (9, 'sub_thresh', 'Threshold for sub-chunk deviation.', TRUE, json_build_array(float_ge_0_type), NULL, 5),
        (9, 'min_periods', 'Minimum points required in a chunk.', TRUE, json_build_array(int_ge_0_type), NULL, 6),
        -- renameField
        (11, 'new_name', 'Name to assign to the field.', FALSE, json_build_array(str_type), NULL, 1),
        -- rolling
        (12, 'window', 'Size of the rolling window.', FALSE, json_build_array(offset_type), NULL, 1),
        (12, 'func', 'Function to apply over the rolling window.', FALSE, json_build_array('{"type": "enum", "constraint": {"only":["sum","mean","median","min","max","std","var","skew","kurt"]}}'::jsonb), 'mean', 2),
        (12, 'min_periods', 'Minimum points required for a valid result.', TRUE, json_build_array(int_ge_0_type), '0', 3),
        (12, 'center', 'Whether to center the window.', TRUE, json_build_array(bool_type), 'true', 4),
        -- transferFlags
        (13, 'squeeze', 'Collapse history into one column.', TRUE, json_build_array(bool_type), 'false', 1),
        (13, 'overwrite', 'Overwrite existing flags if True.', TRUE, json_build_array(bool_type), 'false', 2);
END $$;
