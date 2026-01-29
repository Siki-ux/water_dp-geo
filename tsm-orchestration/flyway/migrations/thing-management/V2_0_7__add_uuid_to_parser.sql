ALTER TABLE file_parser ADD COLUMN uuid UUID NOT NULL UNIQUE DEFAULT gen_random_uuid();

ALTER TABLE file_parser ADD CONSTRAINT file_parser_name_project_uniq UNIQUE ("name", project_id);
