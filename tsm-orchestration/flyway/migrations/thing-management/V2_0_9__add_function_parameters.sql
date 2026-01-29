TRUNCATE TABLE function_parameter CASCADE;
ALTER TABLE function_parameter ADD CONSTRAINT func_pos_uniq UNIQUE (function_id, "position");

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
    ds_type jsonb := '{"type": "datastream", "constraint": {"min":1}}';
    field_desc text := 'Input data stream(s).';
    target_desc text := 'Output data stream(s) to which the results are written. Defaults to field if null.';
BEGIN
    INSERT INTO function_parameter
        (function_id, name, description, optional, "type", default_value, position)
    VALUES
        -- flagIsolated
        (1, 'field', field_desc, FALSE, json_build_array(ds_type), NULL, 1),
        (1, 'target', target_desc, TRUE, json_build_array(ds_type), NULL, 2),
        (1, 'gap_window', 'Minimum gap size required before and after a group to consider it isolated.', FALSE, json_build_array(offset_type), NULL, 3),
        (1, 'group_window', 'Maximum size of a data chunk to consider for isolation.', FALSE, json_build_array(offset_type), NULL, 4),
        -- flagJumps
        (2, 'field', field_desc, FALSE, json_build_array(ds_type), NULL, 1),
        (2, 'target', target_desc, TRUE, json_build_array(ds_type), NULL, 2),
        (2, 'thresh', 'Threshold for mean difference between adjacent windows to trigger flagging.', FALSE, json_build_array(float_ge_0_type), NULL, 3),
        (2, 'window', 'Size of the rolling windows used to calculate the mean.', FALSE, json_build_array(offset_type), NULL, 4),
        (2, 'min_periods', 'Minimum observations required for a valid mean calculation.', TRUE, json_build_array(int_ge_0_type), '0', 5),
        -- flagOffset
        (3, 'field', field_desc, FALSE, json_build_array(ds_type), NULL, 1),
        (3, 'target', target_desc, TRUE, json_build_array(ds_type), NULL, 2),
        (3, 'tolerance', 'Maximum allowed difference between preceding and succeeding values.', FALSE, json_build_array(float_ge_0_type), NULL, 3),
        (3, 'window', 'Maximum duration for the offset sequence.', FALSE, json_build_array(offset_type), NULL, 4),
        (3, 'thresh', 'Minimum absolute difference to consider a sequence as an offset.', TRUE, json_build_array(float_ge_0_type), NULL, 5),
        (3, 'thresh_relative', 'Minimum relative change to consider a sequence as an offset.', TRUE, json_build_array(float_type), NULL, 6),
        -- flagPlateau
        (4, 'field', field_desc, FALSE, json_build_array(ds_type), NULL, 1),
        (4, 'target', target_desc, TRUE, json_build_array(ds_type), NULL, 2),
        (4, 'min_length', 'Minimum temporal extension of a plateau.', FALSE, json_build_array(int_gt_0_type, offset_type), NULL, 3),
        (4, 'max_length', 'Maximum temporal extension of a plateau.', TRUE, json_build_array(int_gt_0_type, offset_type), NULL, 4),
        (4, 'min_jump', 'Minimum difference from preceding/succeeding periods.', TRUE, json_build_array(float_ge_0_type), NULL, 5),
        (4, 'granularity', 'Precision of the search.', TRUE, json_build_array(int_gt_0_type, offset_type), NULL, 6),
        -- flagRange
        (5, 'field', field_desc, FALSE, json_build_array(ds_type), NULL, 1),
        (5, 'target', target_desc, TRUE, json_build_array(ds_type), NULL, 2),
        (5, 'min', 'Lower bound for valid data.', FALSE, json_build_array(float_type), NULL, 3),
        (5, 'max', 'Upper bound for valid data.', FALSE, json_build_array(float_type), NULL, 4),
        -- flagAll
        (6, 'field', field_desc, FALSE, json_build_array(ds_type), NULL, 1),
        (6, 'target', target_desc, TRUE, json_build_array(ds_type), NULL, 2),
        -- flagUniLOF
        (7, 'field', field_desc, FALSE, json_build_array(ds_type), NULL, 1),
        (7, 'target', target_desc, TRUE, json_build_array(ds_type), NULL, 2),
        (7, 'n', 'Number of periods to include in LOF calculation.', TRUE, json_build_array(int_type), '20', 3),
        (7, 'thresh', 'LOF cutoff value.', TRUE, json_build_array(float_ge_0_type, '{"type": "enum", "constraint": {"only": ["auto"]}}'::jsonb), 'auto', 4),
        (7, 'probability', 'Outlier probability cutoff.', TRUE, json_build_array(float_ge_0_le_1_type), NULL, 5),
        (7, 'corruption', 'Portion or count of data considered anomalous.', TRUE, json_build_array(float_ge_0_le_1_type, int_gt_0_type), NULL, 6),
        (7, 'algorithm', 'Algorithm for nearest neighbor calculation.', TRUE, json_build_array('{"type": "enum", "constraint": {"only": ["ball_tree", "kd_tree", "brute", "auto"]}}'::jsonb), 'ball_tree', 7),
        (7, 'p', 'Minkowski metric degree.', TRUE, json_build_array(int_gt_0_type), '1', 8),
        (7, 'density', 'Temporal density calculation.', TRUE, json_build_array(float_ge_0_type, '{"type": "enum", "constraint": {"only": ["auto"]}}'::jsonb), 'auto', 9),
        (7, 'fill_na', 'Fill NaNs via interpolation if True.', TRUE, json_build_array(bool_type), 'true', 10),
        (7, 'slope_correct', 'Remove clusters caused by steep slopes.', TRUE, json_build_array(bool_type), 'true', 11),
        (7, 'min_offset', 'Minimum value jump before and after clusters to flag.', TRUE, json_build_array(float_ge_0_type), NULL, 12),
        -- flagZScore
        (8, 'field', field_desc, FALSE, json_build_array(ds_type), NULL, 1),
        (8, 'target', target_desc, TRUE, json_build_array(ds_type), NULL, 2),
        (8, 'method', '''standard'' or ''modified'' Z-score calculation.', TRUE, json_build_array('{"type": "enum", "constraint": {"only": ["standard", "modified"]}}'::jsonb), NULL, 3),
        (8, 'window', 'Rolling window size.', TRUE, json_build_array(int_gt_0_type, offset_type), NULL, 4),
        (8, 'thresh', 'Z-score threshold.', TRUE, json_build_array(float_ge_0_type), '3', 5),
        (8, 'min_residuals', 'Minimum residual to consider a point as outlier.', TRUE, json_build_array(float_ge_0_type), NULL, 6),
        (8, 'min_periods', 'Minimum valid points in a window.', TRUE, json_build_array(int_gt_0_type), NULL, 7),
        (8, 'center', 'Whether to center the window.', TRUE, json_build_array(bool_type), 'true', 8),
        (8, 'axis', 'Axis along which scoring is applied.', TRUE, json_build_array('{"type": "int", "constraint": {"min": 0, "max": 1}}'::jsonb), '0', 9),
        -- flagByScatterLowpass
        (9, 'field', field_desc, FALSE, json_build_array(ds_type), NULL, 1),
        (9, 'target', target_desc, TRUE, json_build_array(ds_type), NULL, 2),
        (9, 'window', 'Chunk size for evaluation.', FALSE, json_build_array(offset_type), NULL, 3),
        (9, 'thresh', 'Threshold for chunk deviation.', FALSE, json_build_array(float_ge_0_type), NULL, 4),
        (9, 'func', 'Aggregation function for chunk evaluation.', TRUE, json_build_array('{"type": "enum", "constraint": {"only": ["std","var","mad"]}}'::jsonb), 'std', 5),
        (9, 'sub_window', 'Window size for sub-chunks.', TRUE, json_build_array(offset_type), NULL, 6),
        (9, 'sub_thresh', 'Threshold for sub-chunk deviation.', TRUE, json_build_array(float_ge_0_type), NULL, 7),
        (9, 'min_periods', 'Minimum points required in a chunk.', TRUE, json_build_array(int_ge_0_type), NULL, 8),
        -- propagateFlags
        (10, 'field', field_desc, FALSE, json_build_array(ds_type), NULL, 1),
        (10, 'target', target_desc, TRUE, json_build_array(ds_type), NULL, 2),
        -- renameField
        (11, 'field', field_desc, FALSE, json_build_array(ds_type), NULL, 1),
        (11, 'target', target_desc, TRUE, json_build_array(ds_type), NULL, 2),
        (11, 'new_name', 'Name to assign to the field.', FALSE, json_build_array(str_type), NULL, 3),
        -- rolling
        (12, 'field', field_desc, FALSE, json_build_array(ds_type), NULL, 1),
        (12, 'target', target_desc, TRUE, json_build_array(ds_type), NULL, 2),
        (12, 'window', 'Size of the rolling window.', FALSE, json_build_array(offset_type), NULL, 3),
        (12, 'func', 'Function to apply over the rolling window.', FALSE, json_build_array('{"type": "enum", "constraint": {"only":["sum","mean","median","min","max","std","var","skew","kurt"]}}'::jsonb), 'mean', 4),
        (12, 'min_periods', 'Minimum points required for a valid result.', TRUE, json_build_array(int_ge_0_type), '0', 5),
        (12, 'center', 'Whether to center the window.', TRUE, json_build_array(bool_type), 'true', 6),
        -- transferFlags
        (13, 'field', field_desc, FALSE, json_build_array(ds_type), NULL, 1),
        (13, 'target', target_desc, TRUE, json_build_array(ds_type), NULL, 2),
        (13, 'squeeze', 'Collapse history into one column.', TRUE, json_build_array(bool_type), 'false', 3),
        (13, 'overwrite', 'Overwrite existing flags if True.', TRUE, json_build_array(bool_type), 'false', 4);
END $$;
