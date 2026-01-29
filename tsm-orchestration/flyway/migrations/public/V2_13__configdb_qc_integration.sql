SET search_path TO config_db;

ALTER TABLE "qaqc" ALTER COLUMN "project_id" DROP NOT NULL;

ALTER TABLE "thing" ADD COLUMN "legacy_qaqc_id" BIGINT NULL;
ALTER TABLE "thing"
    ADD CONSTRAINT "fk_thing_qaqc" FOREIGN KEY ("legacy_qaqc_id") REFERENCES "qaqc" ("id") DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE project ADD CONSTRAINT project_uuid_unique UNIQUE (uuid);
