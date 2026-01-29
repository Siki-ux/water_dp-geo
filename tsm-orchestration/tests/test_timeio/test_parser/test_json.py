#! /usr/bin/env python
# -*- coding: utf-8 -*-


import pandas as pd
import pytest

from timeio.parser.json_parser import JsonParser

# from timeio.errors import ParsingError

RAWDATA = """
{
"Datetime": "2025-08-12T13:01:23", // Messzeitpunkt (UTC, ISO 8601)
"Frame_count": 123, // Nachrichten-Sequenznummer, 0..65535
"Voltage": 3.6, // Batteriespannung [V]
"Firmware_version_ANALOG": 0, // Firmware-Version, 0..15
"Air_temperature": 25.51, // Umgebungstemperatur [°C]
"Relative_humidity": 45.23, // rel. Luftfeuchtigkeit [%rH]
"Electrical_voltage_1": 317, // Analogspannung Eingang #1 [μV]
"Electrical_voltage_2": 20, // Analogspannung Eingang #2 [μV]
"Electrical_voltage_3": 0, // Analogspannung Eingang #3 [μV]
// fehlt, da im Beispiel inaktiv: "Electrical_voltage_4": 0, // Analogspannung Eingang #4 [μV]
"Analog_input_voltage_range_1": 1, // Spannungsbereich Eingang #1
"Analog_input_voltage_range_2": 2, // Spannungsbereich Eingang #2
"Analog_input_voltage_range_3": 3, // Spannungsbereich Eingang #3
"Analog_input_voltage_range_4": 0 // Spannungsbereich Eingang #4
}
"""


def test_parsing():
    settings = {
        "timestamp_keys": [{"key": "Datetime", "format": "%Y-%m-%dT%H:%M:%S"}],
        "comment": "//",
    }
    parser = JsonParser(settings)
    df = parser.do_parse(RAWDATA.strip(), "thing", "project")

    assert df.columns.tolist() == [
        "Frame_count",
        "Voltage",
        "Firmware_version_ANALOG",
        "Air_temperature",
        "Relative_humidity",
        "Electrical_voltage_1",
        "Electrical_voltage_2",
        "Electrical_voltage_3",
        "Analog_input_voltage_range_1",
        "Analog_input_voltage_range_2",
        "Analog_input_voltage_range_3",
        "Analog_input_voltage_range_4",
    ]
    assert df.index.equals(pd.to_datetime(["2025-08-12 13:01:23"]))
    assert df["Frame_count"].tolist() == [123]
    assert df["Analog_input_voltage_range_4"].tolist() == [0]


MULTIDATECOLUMDATA = """    
{
"Date": "2025-08-09",
"Time": "06:15:00",
"Frame_count": 123, ? Nachrichten-Sequenznummer, 0..65535
"Voltage": 3.6, ? Batteriespannung [V]
"Firmware_version_RAIN": 0, ? Firmware-Version, 0..15
"Air_temperature": 25.51, ? Umgebungstemperatur [°C]
"Relative_humidity": 45.23, ? rel. Luftfeuchtigkeit [%rH]
"Electrical_pulse_count_1": 0, ? Impulszählerwert Eingang #1
"Electrical_pulse_count_2": 10, ? Impulszählerwert Eingang #2
"Electrical_pulse_count_3": 3, ? Impulszählerwert Eingang #3
? fehlt, da im Beispiel inaktiv: "Electrical_pulse_count_4": 0, ? Impulszählerwert Eingang #4
"Pulse_count_active_status_1": 1, ? Impulszähler Eingang #1 aktiv?
"Pulse_count_active_status_2": 1, ? Impulszähler Eingang #2 aktiv?
"Pulse_count_active_status_3": 1, ? Impulszähler Eingang #3 aktiv?
"Pulse_count_active_status_4": 0 ? Impulszähler Eingang #4 aktiv?
}
"""


def test_multi_date_column_parsing():
    settings = {
        "timestamp_keys": [
            {"key": "Date", "format": "%Y-%m-%d"},
            {"key": "Time", "format": "%H:%M:%S"},
        ],
        "comment": "?",
    }
    parser = JsonParser(settings)
    df = parser.do_parse(MULTIDATECOLUMDATA.strip(), "thing", "project")

    assert df.columns.tolist() == [
        "Frame_count",
        "Voltage",
        "Firmware_version_RAIN",
        "Air_temperature",
        "Relative_humidity",
        "Electrical_pulse_count_1",
        "Electrical_pulse_count_2",
        "Electrical_pulse_count_3",
        "Pulse_count_active_status_1",
        "Pulse_count_active_status_2",
        "Pulse_count_active_status_3",
        "Pulse_count_active_status_4",
    ]
    assert df.index.equals(pd.to_datetime(["2025-08-09 06:15:00"]))
    assert df["Frame_count"].tolist() == [123]
    assert df["Pulse_count_active_status_4"].tolist() == [0]


NESTEDDATA = """
{
"Timestamp": { # UTC, date and time in separate fields
    "Date": "20240701",
    "Time": "123456"
    },
"Parameters": { # Nested Objekt with sensor data
    "Frame_count": 123, # Nachrichten-Sequenznummer, 0..65535
    "Voltage": 3.6, # Batteriespannung [V]
    "Firmware_version_SOIL": 0, # Firmware-Version, 0..15
    "Air_temperature": 25.51, # Umgebungstemperatur [°C]
    "Relative_humidity": 45.23, # rel. Luftfeuchtigkeit [%rH]
    "Soil_temperature_1": 15.5, # Bodentemperatur Sensor #1 [°C]
    "Soil_temperature_2": 14.7, # Bodentemperatur Sensor #2 [°C]
    "Soil_temperature_3": 13.1, # Bodentemperatur Sensor #3 [°C]
    "Soil_moisture_1": 12.3, # vol. Bodenwassergehalt Sensor #1 [Vol%]
    "Soil_moisture_2": 17.5, # vol. Bodenwassergehalt Sensor #2 [Vol%]
    "Soil_moisture_3": 18.1, # vol. Bodenwassergehalt Sensor #3 [Vol%]
    "Soil_permittivity_1": 2.3, # Permittivity Sensor #1
    "Soil_permittivity_2": 3.1, # Permittivity Sensor #2
    "Soil_permittivity_3": 4.0 # Permittivity Sensor #3
    }
}
"""


def test_nested_json_parsing():
    settings = {
        "timestamp_keys": [
            {"key": "Timestamp.Date", "format": "%Y%m%d"},
            {"key": "Timestamp.Time", "format": "%H%M%S"},
        ],
        "comment": "#",
    }
    parser = JsonParser(settings)
    df = parser.do_parse(NESTEDDATA.strip(), "thing", "project")

    assert df.columns.tolist() == [
        "Parameters.Frame_count",
        "Parameters.Voltage",
        "Parameters.Firmware_version_SOIL",
        "Parameters.Air_temperature",
        "Parameters.Relative_humidity",
        "Parameters.Soil_temperature_1",
        "Parameters.Soil_temperature_2",
        "Parameters.Soil_temperature_3",
        "Parameters.Soil_moisture_1",
        "Parameters.Soil_moisture_2",
        "Parameters.Soil_moisture_3",
        "Parameters.Soil_permittivity_1",
        "Parameters.Soil_permittivity_2",
        "Parameters.Soil_permittivity_3",
    ]
    assert df.index.equals(pd.to_datetime(["2024-07-01 12:34:56"]))
    assert df["Parameters.Frame_count"].tolist() == [123]
    assert df["Parameters.Soil_permittivity_3"].tolist() == [4.0]


# Note: the array data must be an array of objects (not an object with an array property)
# see also https://pandas.pydata.org/docs/reference/api/pandas.json_normalize.html
ARRAYDATA = """
[
    {
        "Datetime": "2025-01-01T00:00:00",
        "Frame_count": 123,
        "Voltage": 3.6,
        "Firmware_version_THL": 0,
        "Air_temperature": 25.51,
        "Relative_humidity": 45.23,
        "Illuminance": 123
    },
    {
        "Datetime": "2025-01-01T01:00:00",
        "Frame_count": 124,
        "Voltage": 3.55,
        "Firmware_version_THL": 0,
        "Air_temperature": 25.45,
        "Relative_humidity": 45.31,
        "Illuminance": 130
    },
    {
        "Datetime": "2025-01-01T02:00:00",
        "Frame_count": 125,
        "Voltage": 3.5,
        "Firmware_version_THL": 0,
        "Air_temperature": 25.37,
        "Relative_humidity": 45.27,
        "Illuminance": 128
    }
]
"""


def test_array_json_parsing():
    settings = {
        "timestamp_keys": [{"key": "Datetime", "format": "%Y-%m-%dT%H:%M:%S"}],
    }
    parser = JsonParser(settings)
    df = parser.do_parse(ARRAYDATA.strip(), "thing", "project")

    assert df.columns.tolist() == [
        "Frame_count",
        "Voltage",
        "Firmware_version_THL",
        "Air_temperature",
        "Relative_humidity",
        "Illuminance",
    ]
    assert df.index.equals(
        pd.to_datetime(
            ["2025-01-01 00:00:00", "2025-01-01 01:00:00", "2025-01-01 02:00:00"]
        )
    )
    assert df["Frame_count"].tolist() == [123, 124, 125]
    assert df["Illuminance"].tolist() == [123, 130, 128]
