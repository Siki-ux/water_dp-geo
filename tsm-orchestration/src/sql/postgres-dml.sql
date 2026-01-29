INSERT INTO sensor (id, name, description, encoding, metadata, properties)
VALUES (1, 'Default Sensor', 'Auto-generated sensor', 'application/pdf', 'http://example.org/sensor', null)
ON CONFLICT (id) DO NOTHING;

INSERT INTO observed_property (id, name, definition, description, properties)
VALUES (1, 'Default Property', 'http://example.org/property', 'Auto-generated property', null)
ON CONFLICT (id) DO NOTHING;

INSERT INTO relation_role
    (id, name, definition, inverse_name, inverse_definition, description, properties)
VALUES
    (1, 'created_by', 'This was created by other(s)', 'created', 'Other(s) created this', 'A derived product', null)
ON CONFLICT (id) DO UPDATE SET
    name = excluded.name,
    definition = excluded.definition,
    inverse_name = excluded.inverse_name,
    inverse_definition = excluded.inverse_definition,
    description = excluded.description,
    properties = excluded.properties;
