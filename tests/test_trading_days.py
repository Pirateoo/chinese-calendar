# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import datetime
import json
import threading
from urllib.request import urlopen

import chinese_calendar
from chinese_calendar.api import create_server
from chinese_calendar.utils import is_a_share_trading_day, is_interbank_trading_day


def _start_server():
    server = create_server(host="127.0.0.1", port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def test_interbank_includes_weekend_working_day():
    sunday_workday = datetime.date(2018, 2, 11)
    assert chinese_calendar.is_workday(sunday_workday) is True
    assert is_interbank_trading_day(sunday_workday) is True


def test_a_share_excludes_weekend_even_if_workday():
    sunday_workday = datetime.date(2018, 2, 11)
    assert is_a_share_trading_day(sunday_workday) is False


def test_a_share_trading_day_on_weekday_workday():
    weekday_workday = datetime.date(2018, 5, 10)
    assert is_a_share_trading_day(weekday_workday) is True


def test_trading_day_endpoints_accept_multiple_dates():
    server, thread = _start_server()
    try:
        port = server.server_address[1]
        with urlopen(
            f"http://127.0.0.1:{port}/api/interbank/trading-days?dates=2018-02-11&dates=2018-05-01"
        ) as response:
            payload = json.load(response)["results"]
        assert payload[0]["date"] == "2018-02-11"
        assert payload[0]["is_interbank_trading_day"] is True
        assert payload[1]["is_interbank_trading_day"] is False
    finally:
        server.shutdown()
        thread.join(timeout=1)


def test_a_share_endpoint_supports_range_query():
    server, thread = _start_server()
    try:
        port = server.server_address[1]
        with urlopen(f"http://127.0.0.1:{port}/api/a-share/trading-days?start=2018-02-10&end=2018-02-12") as response:
            payload = json.load(response)["results"]
        assert payload == [
            {"date": "2018-02-10", "is_a_share_trading_day": False},
            {"date": "2018-02-11", "is_a_share_trading_day": False},
            {"date": "2018-02-12", "is_a_share_trading_day": True},
        ]
    finally:
        server.shutdown()
        thread.join(timeout=1)


def test_get_trading_days_helpers():
    start, end = datetime.date(2018, 2, 10), datetime.date(2018, 2, 12)
    interbank_days = chinese_calendar.get_interbank_trading_days(start, end)
    a_share_days = chinese_calendar.get_a_share_trading_days(start, end)

    assert interbank_days == [datetime.date(2018, 2, 11), datetime.date(2018, 2, 12)]
    assert a_share_days == [datetime.date(2018, 2, 12)]


def test_api_supports_existing_judgements_and_range_lists():
    server, thread = _start_server()
    try:
        port = server.server_address[1]
        with urlopen(f"http://127.0.0.1:{port}/api/workdays?dates=2018-02-11&dates=2018-02-12") as response:
            workday_payload = json.load(response)["results"]
        with urlopen(
            f"http://127.0.0.1:{port}/api/holidays/range?start=2018-02-10&end=2018-02-12&include_weekends=false"
        ) as response:
            holiday_range_payload = json.load(response)["holidays"]
        with urlopen(
            f"http://127.0.0.1:{port}/api/interbank/trading-days/list?start=2018-02-10&end=2018-02-12"
        ) as response:
            interbank_payload = json.load(response)["interbank_trading_days"]

        assert workday_payload == [
            {"date": "2018-02-11", "is_workday": True},
            {"date": "2018-02-12", "is_workday": True},
        ]
        assert holiday_range_payload == []
        assert interbank_payload == ["2018-02-11", "2018-02-12"]
    finally:
        server.shutdown()
        thread.join(timeout=1)
