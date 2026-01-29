#! /usr/bin/env python
# -*- coding: utf-8 -*-


import pandas as pd
import pytest
import json

from timeio.parser import CsvParser
from timeio.errors import ParsingError

RAWDATA = """
//Hydroinnova CRS-1000 Data
//CellSig=12

//RecordNum,Date Time(UTC),P1_mb,P3_mb,P4_mb,T1_C,T2_C,T3_C,T4_C,T_CS215,RH1,RH2,RH_CS215,Vbat,N1Cts,N2Cts,N1ET_sec,N2ET_sec,N1T_C,N1RH,N2T_C,N2RH,D1

1418, 2021/09/09 05:45:00,  987.0, 989.70, 991.05,   15.9, 128.9,  15.8,  14.6,  13.8, 75.2,119.0, 89.2, 11.853,      160,      122,     900,     900,  17.9, 62.7,  17.7, 63.5,        0
1419, 2021/09/09 06:00:00,  987.0, 989.74, 991.05,   15.9, 128.9,  15.7,  14.5,  14.2, 75.6,119.0, 88.8, 11.856,      171,      111,     900,     900,  18.0, 62.9,  17.8, 63.6,        0
1420, 2021/09/09 06:15:00,  987.1, 989.76, 991.12,   15.9, 128.9,  15.8,  14.6,  14.5, 76.1,119.0, 89.5, 11.855,      165,      103,     900,     900,  18.1, 63.2,  17.9, 63.8,        0
"""


@pytest.mark.parametrize(
    "settings, columns",
    [
        ({"skiprows": 4, "header": None}, [2, 4, 8]),
        ({"skiprows": 3, "header": 0}, ["P1_mb", "P4_mb", "T4_C"]),
        ({"skiprows": 3, "header": 0, "comment": "//"}, ["P1_mb", "P4_mb", "T4_C"]),
    ],
)
def test_parsing(settings, columns):
    base_settings = {
        "decimal": ".",
        "delimiter": ",",
        "skipfooter": 0,
        "timestamp_columns": [{"column": 1, "format": "%Y/%m/%d %H:%M:%S"}],
    }
    parser = CsvParser({**base_settings, **settings})
    df = parser.do_parse(RAWDATA.strip(), "project", "thing")

    assert df.columns[[1, 3, 7]].equals(pd.Index(columns))
    assert df.iloc[:, 2].tolist() == [989.7, 989.74, 989.76]
    assert df.iloc[:, 14].tolist() == [122, 111, 103]

    tframe = df.iloc[:, 3].to_frame()
    obs = parser.to_observations(tframe, origin="test")

    assert set([d["datastream_pos"] for d in obs]) == set(map(str, tframe.columns))
    assert set([d["result_number"] for d in obs]) == set(tframe.squeeze().tolist())


DIRTYDATA = """
//Hydroinnova CRS-1000 Data
//CellSig=12

//RecordNum,Date Time(UTC),P1_mb,P3_mb,P4_mb,T1_C,

1418, 2021/09/09 05:45:00,  987.0, 989.70, 991.05,   15.9
1419, 2021/09/09 06:00:00,  987.0,    xW8, 991.05,   15.9
1420, 2021/09/09 06:15:00,  987.1, 989.76, 991.12,   15.9
"""


def test_dirty_data_parsing():
    settings = {
        "decimal": ".",
        "delimiter": ",",
        "skiprows": 3,
        "skipfooter": 0,
        "timestamp_columns": [{"column": 1, "format": "%Y/%m/%d %H:%M:%S"}],
    }

    parser = CsvParser(settings)
    df = parser.do_parse(DIRTYDATA, "project", "thing")

    assert pd.api.types.is_numeric_dtype(df[2])
    assert pd.api.types.is_string_dtype(df[3])

    obs = parser.to_observations(df[[3]], origin="test")
    assert len(obs) == 3
    assert obs[0]["result_time"] == "2021-09-09T06:00:00"
    assert obs[0]["result_string"] == "xW8"
    params = json.loads(obs[0]["parameters"])
    assert params["origin"] == "test"
    assert params["column_header"] == "3"
    assert params["parser_id"] is None

    assert obs[1]["result_time"] == "2021-09-09T05:45:00"
    assert obs[1]["result_number"] == 989.7
    params = json.loads(obs[1]["parameters"])
    assert params["origin"] == "test"
    assert params["column_header"] == "3"
    assert params["parser_id"] is None


MULTIDATECOLUMDATA = """
============================================================================
   Datum     Zeit  Temp spezLeitf   Tiefe   Chl   Chl    ODO ODOsat Batterie
   t/m/j hh:mm:ss     C     uS/cm   Meter  ug/l   RFU   mg/l %Lokal     Volt
----------------------------------------------------------------------------
02/11/22 14:00:51 20.52         3   0.151   9.1   2.2   9.10  100.5     12.5
02/11/22 15:00:51 20.38         3   0.158 -23.5  -5.6   9.11  100.3     12.5
02/11/22 16:00:51 20.19         3   0.161  -0.5  -0.1   9.15  100.3     12.4
02/11/22 17:00:51 20.02         3   0.164   0.0   0.0   9.18  100.3     12.5
"""


def test_multi_date_column_parsing():
    settings = {
        "decimal": ".",
        "delimiter": "\\s+",
        "skiprows": 4,
        "skipfooter": 0,
        "header": None,
        "timestamp_columns": [
            {"column": 0, "format": "%d/%m/%y"},
            {"column": 1, "format": "%H:%M:%S"},
        ],
    }
    parser = CsvParser(settings)
    df = parser.do_parse(MULTIDATECOLUMDATA.strip(), "project", "thing")

    assert df.index.equals(
        pd.to_datetime(
            [
                "2022-11-02 14:00:51",
                "2022-11-02 15:00:51",
                "2022-11-02 16:00:51",
                "2022-11-02 17:00:51",
            ]
        )
    )
    assert df.columns.equals(pd.RangeIndex(2, 10))
    assert (df[2] == [20.52, 20.38, 20.19, 20.02]).all()
    assert (df[9] == [12.5, 12.5, 12.4, 12.5]).all()


RAWDATA_EMPTY_COLS = """time;var1;var2;var3;var4;var5;var6
2025-08-28 17:00:00;1;1;;;;1
2025-08-28 17:10:00;1;1;;;;1
2025-08-28 17:20:00;1;1;;;;1
"""


def test_empty_col_csv():
    settings = {
        "decimal": ".",
        "delimiter": ";",
        "skiprows": 0,
        "header": 0,
        "skipfooter": 0,
        "timestamp_columns": [{"column": 0, "format": "%Y-%m-%d %H:%M:%S"}],
    }
    parser = CsvParser(settings)
    df = parser.do_parse(RAWDATA_EMPTY_COLS, "project", "thing")
    assert df.shape == (3, 6)


RAWDATA_WITH_MS = """time;dachnummer;Temp_degC_1;Temp_degC_2
2025-09-04 15:32:32.064000;2;24.66;26.18
2025-09-04 15:32:32.065000;2;24.66;26.18
"""


def test_with_ms():
    settings = {
        "decimal": ".",
        "delimiter": ";",
        "skiprows": 0,
        "header": 0,
        "skipfooter": 0,
        "timestamp_columns": [{"column": 0, "format": "%Y-%m-%d %H:%M:%S.%f"}],
    }

    parser = CsvParser(settings)
    df = parser.do_parse(RAWDATA_WITH_MS, "project", "thing")
    obs = parser.to_observations(df, origin="test")
    expected_df_index = pd.Index(
        [
            "2025-09-04T15:32:32.064000",
            "2025-09-04T15:32:32.065000",
        ],
        name="result_time",
    )
    expected_obs_timestamps = [
        "2025-09-04T15:32:32.064000",
        "2025-09-04T15:32:32.065000",
        "2025-09-04T15:32:32.064000",
        "2025-09-04T15:32:32.065000",
        "2025-09-04T15:32:32.064000",
        "2025-09-04T15:32:32.065000",
    ]
    assert df.index.equals(expected_df_index)
    assert [i["result_time"] for i in obs] == expected_obs_timestamps


RAWDATA_WITHOUT_HEADER = """2025-09-04 15:32:32.064000;2;24.66;26.18
2025-09-04 15:32:32.065000;2;24.66;26.18
"""


@pytest.mark.parametrize(
    "settings, expected_columns, expected_index_name",
    [
        [
            {"names": ["time", "dachnummer", "Temp_degC_1", "Temp_degC_2"]},
            ["dachnummer", "Temp_degC_1", "Temp_degC_2"],
            "time",
        ],
        [{}, [1, 2, 3], 0],
    ],
)
def test_custom_names(settings, expected_columns, expected_index_name):
    base_settings = {
        "decimal": ".",
        "delimiter": ";",
        "skiprows": 0,
        "skipfooter": 0,
        "timestamp_columns": [{"column": 0, "format": "%Y-%m-%d %H:%M:%S.%f"}],
    }
    parser = CsvParser({**base_settings, **settings})
    df = parser.do_parse(RAWDATA_WITHOUT_HEADER, "project", "thing")
    assert list(df.columns) == expected_columns
    assert df.index.name == expected_index_name


def test_custom_names_error():
    settings = {
        "decimal": ".",
        "delimiter": ";",
        "skiprows": 0,
        "skipfooter": 0,
        "timestamp_columns": [{"column": 0, "format": "%Y-%m-%d %H:%M:%S.%f"}],
        "names": ["time", "dachnummer", "Temp_degC_1", "Temp_degC_2", "count"],
    }
    paser = CsvParser(settings)
    with pytest.raises(
        ParsingError,
        match="Number of custom column names does not match number of columns in CSV.",
    ):
        paser.do_parse(RAWDATA_WITHOUT_HEADER, "project", "thing")


RAWDATA_WITHOUT_TZ = """time,var1,var2,var3
2025-01-01 00:00:00,1,2,3
2025-01-01 00:10:00,1,2,3
2025-01-01 00:20:00,1,2,3
"""

RAWDATA_WITH_TZ = """time,var1,var2,var3
2025-01-01 00:00:00+01:00,1,2,3
2025-01-01 00:10:00+01:00,1,2,3
2025-01-01 00:20:00+01:00,1,2,3
"""


@pytest.mark.parametrize(
    "settings, rawdata, expected_index",
    [
        (
            {
                "timestamp_columns": [{"column": 0, "format": "%Y-%m-%d %H:%M:%S"}],
                "timezone": "Europe/Berlin",
            },
            RAWDATA_WITHOUT_TZ,
            pd.DatetimeIndex(
                [
                    "2025-01-01 00:00:00+01:00",
                    "2025-01-01 00:10:00+01:00",
                    "2025-01-01 00:20:00+01:00",
                ],
                name="time",
                tz="Europe/Berlin",
            ),
        ),
        (
            {"timestamp_columns": [{"column": 0, "format": "%Y-%m-%d %H:%M:%S%z"}]},
            RAWDATA_WITH_TZ,
            pd.DatetimeIndex(
                [
                    "2025-01-01 00:00:00+01:00",
                    "2025-01-01 00:10:00+01:00",
                    "2025-01-01 00:20:00+01:00",
                ],
                name="time",
                tz="UTC+01:00",
            ),
        ),
    ],
)
def test_tz(settings, rawdata, expected_index):
    base_settings = {
        "decimal": ".",
        "delimiter": ",",
        "skiprows": 0,
        "header": 0,
        "skipfooter": 0,
    }
    parser = CsvParser({**base_settings, **settings})
    df = parser.do_parse(rawdata, "project", "thing")
    assert df.index.equals(expected_index)


def test_double_tz_error():
    settings = {
        "decimal": ".",
        "delimiter": ",",
        "skiprows": 0,
        "header": 0,
        "skipfooter": 0,
        "timestamp_columns": [{"column": 0, "format": "%Y-%m-%d %H:%M:%S%z"}],
        "timezone": "Europe/Berlin",
    }
    paser = CsvParser(settings)
    with pytest.raises(
        ParsingError,
        match="Cannot localize timezone 'Europe/Berlin': index is already timezone aware with tz \(UTC\+01:00\)\.",
    ):
        paser.do_parse(RAWDATA_WITH_TZ, "project", "thing")


RAWDATA_SKIP_WITH_HEADER = """Skipline
#Commentline
time,var1,var2,var3
#A second commentline
2025-01-01 00:00:00,1,2,3
2025-01-01 00:10:00,1,2,3
2025-01-01 00:20:00,1,2,3
#Third Commentline
Skipfooter1
Skipfooter2
"""


@pytest.mark.parametrize(
    "settings",
    [
        {"skiprows": 2, "header": 0},
        {"header": 2},
    ],
)
def test_skipping_and_comments_with_header(settings):
    base_settings = {
        "comment": "#",
        "skipfooter": 2,
        "delimiter": ",",
        "decimal": ".",
        "timestamp_columns": [{"column": 0, "format": "%Y-%m-%d %H:%M:%S"}],
    }
    parser = CsvParser({**base_settings, **settings})
    df = parser.do_parse(RAWDATA_SKIP_WITH_HEADER, "project", "thing")
    expected_index = pd.DatetimeIndex(
        ["2025-01-01 00:00:00", "2025-01-01 00:10:00", "2025-01-01 00:20:00"],
        name="time",
    )
    expected_col_names = ["var1", "var2", "var3"]
    assert df.shape == (3, 3)
    assert df.index.equals(expected_index)
    assert list(df.columns) == expected_col_names


RAWDATA_SKIP_WITHOUT_HEADER = """Skipline
#Commentline
#A second commentline
2025-01-01 00:00:00,1,2,3
2025-01-01 00:10:00,1,2,3
2025-01-01 00:20:00,1,2,3
#Third Commentline
Skipfooter1
Skipfooter2
"""


@pytest.mark.parametrize(
    "settings",
    [
        {"skiprows": 1},
        {"skiprows": 2},
    ],
)
def test_skipping_and_comments_without_header(settings):
    base_settings = {
        "comment": "#",
        "skipfooter": 2,
        "delimiter": ",",
        "decimal": ".",
        "header": None,
        "timestamp_columns": [{"column": 0, "format": "%Y-%m-%d %H:%M:%S"}],
    }
    parser = CsvParser({**base_settings, **settings})
    df = parser.do_parse(RAWDATA_SKIP_WITHOUT_HEADER, "project", "thing")
    expected_index = pd.DatetimeIndex(
        ["2025-01-01 00:00:00", "2025-01-01 00:10:00", "2025-01-01 00:20:00"],
        name="time",
    )
    expected_col_names = [1, 2, 3]
    assert df.shape == (3, 3)
    assert df.index.equals(expected_index)
    assert list(df.columns) == expected_col_names


RAWDATA_SKIP_ROWS = """Skipline_0
datetime,val1,val2,val3
Skipline_2
Skiptline_3
2025-01-01 00:00:00,1,2,3
2025-01-01 00:10:00,1,2,3
2025-01-01 00:20:00,1,2,3
"""


def test_skiprows():
    settings = {
        "delimiter": ",",
        "decimal": ".",
        "header": 0,
        "skiprows": [0, 2, 3],
        "timestamp_columns": [{"column": 0, "format": "%Y-%m-%d %H:%M:%S"}],
    }
    parser = CsvParser({**settings})
    df = parser.do_parse(RAWDATA_SKIP_ROWS, "project", "thing")
    expected_index = pd.DatetimeIndex(
        ["2025-01-01 00:00:00", "2025-01-01 00:10:00", "2025-01-01 00:20:00"],
        name="datetime",
    )
    expected_col_names = ["val1", "val2", "val3"]
    assert df.shape == (3, 3)
    assert df.index.equals(expected_index)
    assert list(df.columns) == expected_col_names
