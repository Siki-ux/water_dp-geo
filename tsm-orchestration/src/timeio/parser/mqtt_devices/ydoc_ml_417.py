from __future__ import annotations

from typing import Any
from datetime import datetime

from timeio.parser.mqtt_parser import MqttParser, Observation


class YdocMl417Parser(MqttParser):
    # mqtt_ingest/test-logger-pb/test/data/jsn
    # {
    # "device":
    #   {"sn":99073020,"name":"UFZ","v":"4.2B5","imei":353081090730204,"sim":89490200001536167920},
    # "channels":[
    #   {"code":"SB","name":"Signal","unit":"bars"},
    #   {"code":"MINVi","name":"Min voltage","unit":"V"},
    #   {"code":"AVGVi","name":"Average voltage","unit":"V"},
    #   {"code":"AVGCi","name":"Average current","unit":"mA"},
    #   {"code":"P1*","name":"pr2_1_10","unit":"m3/m3"},
    #   {"code":"P2","name":"pr2_1_20","unit":"m3/m3"},
    #   {"code":"P3","name":"pr2_1_30","unit":"m3/m3"},
    #   {"code":"P4","name":"pr2_1_40","unit":"m3/m3"},
    #   {}],
    # "data":[
    #   {"$ts":230116110002,"$msg":"WDT;pr2_1"},    <== we ignore that (*)
    #   {"$ts":230116110002,"MINVi":3.74,"AVGVi":3.94,"AVGCi":116,"P1*":"0*T","P2":"0*T","P3":"0*T","P4":"0*T"},
    #   {}]}

    def do_parse(self, rawdata: Any, origin: str = "", **kwargs) -> list[Observation]:
        if "data/jsn" not in origin:
            return []

        # data = payload['data'][1]
        ret = []
        for data in rawdata["data"]:
            try:
                ts = datetime.strptime(str(data["$ts"]), "%y%m%d%H%M%S")
                ob0 = Observation(ts, data["MINVi"], origin, 0, header="MINVi")
                ob1 = Observation(ts, data["AVGVi"], origin, 1, header="AVGCi")
                ob2 = Observation(ts, data["AVGCi"], origin, 2, header="AVGCi")
                ob3 = Observation(ts, data["P1*"], origin, 3, header="P1*")
                ob4 = Observation(ts, data["P2"], origin, 4, header="P2")
                ob5 = Observation(ts, data["P3"], origin, 5, header="P3")
                ob6 = Observation(ts, data["P4"], origin, 6, header="P4")
                ret.extend([ob0, ob1, ob2, ob3, ob4, ob5, ob6])
            except KeyError:
                # we ignore data that not have all keys
                # see also the example above the function at (*)
                pass
        return ret
