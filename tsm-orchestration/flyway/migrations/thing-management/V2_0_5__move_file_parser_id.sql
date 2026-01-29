ALTER TABLE external_sftp_ingest DROP COLUMN IF EXISTS file_parser_id;
ALTER TABLE rawdatastorage ADD COLUMN IF NOT EXISTS file_parser_id INT;
ALTER TABLE rawdatastorage ALTER COLUMN file_parser_id DROP NOT NULL;

ALTER TABLE rawdatastorage ADD CONSTRAINT fk_file_parser FOREIGN KEY (file_parser_id) REFERENCES file_parser(id) ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED;
