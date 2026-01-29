SET search_path TO config_db;

/*
    Define function to set existing active qaqc setup to 'false'
    if different/new setup for the same project_id is set to 'true'
 */
CREATE OR REPLACE FUNCTION unique_qaqc_per_project()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW."default" = TRUE THEN
        UPDATE config_db.qaqc
        SET "default" = FALSE
        WHERE project_id = NEW.project_id AND "default" = TRUE AND id <> NEW.id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

/*
  Remove the existing trigger
 */
DROP TRIGGER IF EXISTS enforce_unique_qaqc_setup ON config_db.qaqc;
/*
    Create trigger to execute the function before insert/update on qaqc
 */
CREATE TRIGGER enforce_unique_qaqc_setup
BEFORE INSERT OR UPDATE ON config_db.qaqc
FOR EACH ROW
EXECUTE FUNCTION unique_qaqc_per_project();
