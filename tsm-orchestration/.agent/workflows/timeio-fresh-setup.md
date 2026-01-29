---
description: Complete setup workflow for fresh tsm-orchestration stack to get data in FROST
---

# Fresh TimeIO Stack Setup (Until Data in FROST)

This workflow documents every step needed to set up a **brand new tsm-orchestration stack** and successfully ingest data that's visible in FROST.

## Prerequisites
- Docker & Docker Compose installed
- Stack running: `docker compose up -d`
- Wait for all containers healthy (~2-3 minutes)

---

## Step 1: Keycloak - Create Project Group

> [!IMPORTANT]
> TimeIO requires groups with **`UFZ-TSM:` prefix** in the `timeio` realm.

### Via Keycloak Admin UI
1. Navigate to: `http://localhost/keycloak/admin/master/console/#/timeio/groups`
2. Click "Create group"
3. Name: `UFZ-TSM:MyProject` (exactly this format)

### Via API (Alternative)
```bash
# Get admin token
TOKEN=$(curl -s -X POST "http://localhost:8081/realms/timeio/protocol/openid-connect/token" \
  -d "client_id=admin-cli" \
  -d "username=admin" \
  -d "password=admin" \
  -d "grant_type=password" | jq -r .access_token)

# Create group
curl -X POST "http://localhost:8081/admin/realms/timeio/groups" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "UFZ-TSM:MyProject"}'
```

---

## Step 2: Keycloak - Add User to Group

### Via Keycloak Admin UI
1. Navigate to: `http://localhost:8081/admin/master/console/#/timeio/users`
2. Select your user (or create one)
3. Go to "Groups" tab → "Join group" → Select `UFZ-TSM:MyProject`

### Via API
```bash
# Get user ID
USER_ID=$(curl -s "http://localhost:8081/admin/realms/timeio/users?username=YOUR_USERNAME" \
  -H "Authorization: Bearer $TOKEN" | jq -r '.[0].id')

# Get group ID
GROUP_ID=$(curl -s "http://localhost:8081/admin/realms/timeio/groups?search=UFZ-TSM:MyProject" \
  -H "Authorization: Bearer $TOKEN" | jq -r '.[0].id')

# Add user to group
curl -X PUT "http://localhost:8081/admin/realms/timeio/users/$USER_ID/groups/$GROUP_ID" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Step 3: Thing Management - Create Project

> The project is automatically created when the first thing is assigned to a group.
> If using the frontend, this is handled automatically.

---

## Step 4: Thing Management - Create Thing

### Via Thing Management Frontend (Recommended)
1. Navigate to: `http://localhost/thing-management/things`
2. Login with your Keycloak user
3. Click "Create New Thing"
4. **Thing Tab**: Fill in Name, select Project
5. **MQTT Ingest Tab**: 
   - **Broker URI**: `mqtt-broker`
   - **Topic**: `mqtt_ingest/<username>/data` (use the generated username)
   - **MQTT Device Type**: `chirpstack_generic`
6. Save and note the generated:
   - **MQTT Username**: `u_XXXXXXXX`
   - **MQTT Password**: `p_XXXXXXXXXXXX`

### Via API
```bash
# Get service token
API_TOKEN=$(curl -s -X POST "http://localhost:8081/realms/timeio/protocol/openid-connect/token" \
  -d "client_id=thing-management" \
  -d "client_secret=YOUR_CLIENT_SECRET" \
  -d "grant_type=client_credentials" | jq -r .access_token)

# Create thing
curl -X POST "http://localhost:8002/thing" \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "MySensor",
    "project_id": "YOUR_PROJECT_UUID",
    "mqtt": {
      "mqtt_device_type": {"name": "chirpstack_generic"}
    }
  }'
```

---

## Step 5: Datastreams - Auto-Created

> [!TIP]
> **Datastreams are automatically created** by `db_api` when the first observation arrives.
> You do NOT need to manually create them.

The `chirpstack_generic` parser extracts datastream names from the JSON payload keys.
For example, payload `{"object": {"temperature": 25, "humidity": 60}}` creates:
- Datastream `temperature`
- Datastream `humidity`

### Manual Creation (Optional)
Only if you need datastreams before first observation:
```bash
curl -X POST "http://db-api:8003/datastream/YOUR_THING_UUID" \
  -H "Content-Type: application/json" \
  -d '{"position": "temperature", "name": "Temperature Sensor"}'
```

---

## Step 6: FIX Schema Mapping (REQUIRED!)

> [!CAUTION]
> **This step is REQUIRED!** TimeIO has a bug where it creates the wrong schema name in `schema_thing_mapping`.
> It creates `project_myproject_1` but the actual schema is `user_myproject`.
> Without this fix, all data ingestion fails with 400 errors!

### Quick Fix (Recommended)
Run the automated fix script from `water_dp-api`:
```powershell
cd c:\Users\Siki\source\dp\water_dp-api
powershell -ExecutionPolicy Bypass -File scripts/fix_timeio.ps1
```

This script automatically:
1. Fixes schema_thing_mapping (project_* → user_*)
2. Creates FROST views for all user_* schemas
3. Grants required permissions

### Manual Fix (Alternative)
// turbo
```bash
docker exec -e PGPASSWORD=postgres tsm-orchestration-database-1 \
  psql -U postgres -d postgres -c "SELECT * FROM public.schema_thing_mapping;"
```

### Check Actual Schema Name
// turbo
```bash
docker exec -e PGPASSWORD=postgres tsm-orchestration-database-1 \
  psql -U postgres -d postgres -c "\dn"
```

### Apply the Fix
```bash
docker exec -e PGPASSWORD=postgres tsm-orchestration-database-1 \
  psql -U postgres -d postgres -c "UPDATE public.schema_thing_mapping SET schema = 'user_myproject' WHERE schema = 'project_myproject_1';"
```

---

## Step 6.5: Create FROST Views (REQUIRED!)

> [!CAUTION]
> **FROST views are missing!** TimeIO creates tables but not the uppercase views FROST expects.
> Without this, FROST returns 500 errors for all queries.

Run this SQL to create the required views:
```bash
docker exec -e PGPASSWORD=postgres tsm-orchestration-database-1 psql -U postgres -d postgres -c "
-- OBSERVATIONS view
CREATE OR REPLACE VIEW user_myproject.\"OBSERVATIONS\" AS
SELECT 
    o.id AS \"ID\",
    o.phenomenon_time_start AS \"PHENOMENON_TIME_START\",
    o.phenomenon_time_end AS \"PHENOMENON_TIME_END\",
    o.result_time AS \"RESULT_TIME\",
    o.result_type AS \"RESULT_TYPE\",
    o.result_number AS \"RESULT_NUMBER\",
    o.result_string AS \"RESULT_STRING\",
    o.result_json AS \"RESULT_JSON\",
    o.result_boolean AS \"RESULT_BOOLEAN\",
    o.result_quality AS \"RESULT_QUALITY\",
    o.valid_time_start AS \"VALID_TIME_START\",
    o.valid_time_end AS \"VALID_TIME_END\",
    o.parameters AS \"PARAMETERS\",
    o.datastream_id AS \"DATASTREAM_ID\",
    NULL::bigint AS \"MULTI_DATASTREAM_ID\",
    NULL::bigint AS \"FEATURE_ID\"
FROM user_myproject.observation o;

-- DATASTREAMS view
CREATE OR REPLACE VIEW user_myproject.\"DATASTREAMS\" AS
SELECT 
    d.id AS \"ID\",
    d.name AS \"NAME\",
    d.name AS \"DESCRIPTION\",
    d.position AS \"OBSERVATION_TYPE\",
    d.properties AS \"PROPERTIES\",
    NULL::geometry AS \"OBSERVED_AREA\",
    NULL::timestamptz AS \"PHENOMENON_TIME_START\",
    NULL::timestamptz AS \"PHENOMENON_TIME_END\",
    NULL::timestamptz AS \"RESULT_TIME_START\",
    NULL::timestamptz AS \"RESULT_TIME_END\",
    d.thing_id AS \"THING_ID\",
    NULL::bigint AS \"SENSOR_ID\",
    NULL::bigint AS \"OBS_PROPERTY_ID\"
FROM user_myproject.datastream d;

-- THINGS view
CREATE OR REPLACE VIEW user_myproject.\"THINGS\" AS
SELECT 
    t.id AS \"ID\",
    t.name AS \"NAME\",
    t.description AS \"DESCRIPTION\",
    t.properties AS \"PROPERTIES\",
    t.uuid AS \"UUID\"
FROM user_myproject.thing t;

-- Grant permissions
GRANT SELECT ON user_myproject.\"OBSERVATIONS\" TO PUBLIC;
GRANT SELECT ON user_myproject.\"DATASTREAMS\" TO PUBLIC;
GRANT SELECT ON user_myproject.\"THINGS\" TO PUBLIC;
"
```

---

## Step 7: Publish Test Data

### Prepare Payload File
```bash
echo '{"time": "2026-01-23T12:00:00Z", "object": {"temperature": 25.5, "humidity": 60.2}}' > /tmp/payload.json
```

### Publish via MQTT
```bash
# Get MQTT broker container ID
MQTT_CONTAINER=$(docker ps --filter "name=mqtt-broker" -q)

# Copy payload
docker cp /tmp/payload.json $MQTT_CONTAINER:/tmp/payload.json

# Publish (replace u_XXXXXXXX and password with values from Step 4)
docker exec $MQTT_CONTAINER mosquitto_pub \
  -h localhost -p 1883 \
  -t "mqtt_ingest/u_XXXXXXXX/data" \
  -u u_XXXXXXXX \
  -P p_XXXXXXXXXXXX \
  -f /tmp/payload.json
```

### Check Worker Logs
```bash
docker logs tsm-orchestration-worker-mqtt-ingest-1 --tail 20
```

**Success indicators:**
- `======================= NEW MESSAGE ==========`
- `===================== PROCESSING DONE ========`

---

## Step 8: Verify Data in FROST

### Via API
```bash
# Replace project_slug_id with your project identifier
curl "http://localhost/sta/project_myproject_1/v1.1/Observations"
```

### Expected Response
```json
{
  "value": [
    {"@iot.id": 1, "result": 25.5, "resultTime": "2026-01-23T12:00:00Z"},
    {"@iot.id": 2, "result": 60.2, "resultTime": "2026-01-23T12:00:00Z"}
  ]
}
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| MQTT message ignored | Wrong topic format | Use `mqtt_ingest/<username>/...` |
| 400 from db_api | Wrong schema_thing_mapping | Update mapping to correct schema |
| FROST 500 error | Missing/wrong FROST views | Recreate simplified views (see architecture doc) |
| Parser error | Wrong payload format | Match parser expected format |

---

## Quick Reference: MQTT Topic Format

```
mqtt_ingest/<username>/<anything>
           ↑ Must be the MQTT username from Thing Management
```

**Example**: `mqtt_ingest/u_3uph9kbu/data`
