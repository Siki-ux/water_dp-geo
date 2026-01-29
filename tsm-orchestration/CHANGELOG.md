# Changelog
- Use `Added`, `Changed`, `Fixed`, `Removed`

## [Unreleased]
### Added
### Fixed
### Changed
### Removed

## 2025-01-20
### Added
- Option to add set file encoding for csv parser ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/552))
### Fixed
- Failing parser on user input errors ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/551))
### Changed
- Frost-Server configuration ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/502))
- T-Systems external api payload changes ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/550))
- File parser are identified using UUIDs instead of database ids ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/541))
### Removed

## 2025-12-17
### Added
- Option to send Grafana warnings via email ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/543))
### Fixed
- Fixed parser failing without pandas kwargs ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/539))
### Changed
### Removed

## 2025-12-10
### Added
- Parsers get UUID ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/530))
- Monitoring dashboard ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/515))
### Fixed
- Fixed scheduler intervals ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/518))
### Changed
- Parser 'Pandas read csv' settings are prioritized ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/531))

## 2025-11-12

### Added
- unittests (several merge requests)

### Fixed
- parser skiprows, comment and header handling ([Merge Request 1](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/489), [Merge Request 2](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/489))
- stalling workers ([Merge Request 1](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/484), [Merge Request 2](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/485))
- sms data syncing ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/483))

## 2025-10-17

### Added
- basic JSON-Parser ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/457))
- cron triggered qc jobs ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/470))

### Changed
- added parsing tags to S3 objects ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/466))
- bumped debian images and python versions ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/468))
- improve reparse script ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/473))

### Fixed
- stalling SMS synchronization ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/464))
- journal writing ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/465))
- fix duplicated mqtt client ids ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/479))

## 2025-09-12

### Added
- tsm-dataprocessing-extensions in SaQC jobs ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/444))
- time zone handling in file parser ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/448))
- millisecond handling in file parser  ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/451))
- custom headers for CSV Parser  ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/454))

### Changed
- ConfigDB description columns to type TEXT  ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/446))
- T-Systems-API aggregation time  ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/450))
- parameter mapping for TTN API from hard-coded to dynamic  ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/453))

### Fixed
- Thing Management DB data model  ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/452))

## 2025-08-29

### Added
- Data Calibration function ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-dataprocessing-extension/-/merge_requests/1))

### Changed
- Improved failure tolerance of thr delete thing scripts ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/442))

### Fixed
- CSV-Header Parsing error with empty columns ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/441))

## 2025-08-28

### Added
- script to delete things ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/433))

### Changed
- Grafana panel headers ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/430))

### Fixed
- Close SFTP connections ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/437))
- Grafana connection issues ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/432))
- CSV-Header Parsing ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/431))

## 2025-08-12

### Added
- Keycloak as an AAI proxy
- Hidden Alpha version of the new Thing-Management
- Option to use csv-file headers as datastream names
- Mosquitto Monitoring

### Changed
- Mosquitto resource settings

### Fixed
- extSFTP service failures

## 2025-07-09

### Added
- MQTTDeviceType `chirpstack-generic` ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/383))
- option to use header names as datastream names in CsvParser ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/347))
- option to write duplicated data for CsvParser. With headers and positions ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/397))
- timeout for ExtAPI HTTPs Requests ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/399))
- migration scripts for changing position based datastream names to header based datastream names ([Merge Request1](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/400), [Merge Request 2](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/402), [Merge Request 3](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/403))

### Changed
- Refactoring python code for Grafana workers ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/375))
- Tsystems API due to changed response ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/398))
- Increase mosquitto message limitations ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/391))

### Fixed
- Pass CSV parser warnings to dashboard journal ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/388))

### Removed
- explicit mapping of parameter to result_type in Bosch API ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/396))

## 2025-06-18

### Added
- Option to use self-hosted docker images ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/386))
- Additional parameters for TTN API ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/387))

### Fixed
- Authentication in TSystems API ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/387))

## 2025-06-12

### Added
- Option to disable the database service ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/358))
- Option to sort and filter columns in Grafana dashoard journal ([Merge Request1](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/366), [Merge Request 2](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/364), [Merge Request 3](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/362), [Merge Request 4](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/360))
- Component tests

### Changed
- Migrated `observation` tables from timescaleDB Hypertables to 'normal' Postgres tables ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/379))
- Added ID Column to `observation` tables ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/348))
- New worker for cron scheduled jobs ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/351))
- Handle failing external API calls gracefully ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/377))

### Fixed
- Duplicated configDB entries ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/287))
- Incompatable timeouts for FROST froze STA requests ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/371))

## 2025-03-28

### Fixed
- Bug when running the QC-Settings ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/343))

## 2025-03-27

### Fixed
- Bug when saving the QC-Settings ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/341))

## 2025-03-26

### Changed
- Switching to materialized views for SMS data ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/326))

### Fixed
- Idle State when creating views for frost ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/336))
- Bug, when Saving a QaQc Test ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/337))

## 2025-03-19
