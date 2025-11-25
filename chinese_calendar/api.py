# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import datetime
import json
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable, Dict, List, Optional
from urllib.parse import parse_qs, urlparse

from chinese_calendar import __version__
from chinese_calendar.utils import (
    get_a_share_trading_days,
    get_dates,
    get_holiday_detail,
    get_holidays,
    get_interbank_trading_days,
    get_workdays,
    is_a_share_trading_day,
    is_holiday,
    is_in_lieu,
    is_interbank_trading_day,
    is_workday,
)


TYPE_CHECKERS: Dict[str, Callable[[datetime.date], bool]] = {
    "holiday": is_holiday,
    "workday": is_workday,
    "in-lieu": is_in_lieu,
    "interbank-trading-day": is_interbank_trading_day,
    "a-share-trading-day": is_a_share_trading_day,
}


def _parse_date(value: str) -> datetime.date:
    try:
        return datetime.date.fromisoformat(value)
    except ValueError:
        raise ValueError(f"Invalid date format: {value}. Expected YYYY-MM-DD.")


def _collect_dates(dates: Optional[List[str]], start: Optional[str], end: Optional[str]) -> List[datetime.date]:
    if dates:
        return [_parse_date(d) for d in dates]
    if start and end:
        start_date, end_date = _parse_date(start), _parse_date(end)
        if end_date < start_date:
            raise ValueError("end date must not be earlier than start date")
        return get_dates(start_date, end_date)
    raise ValueError("Provide either repeated 'dates' parameters or both 'start' and 'end'.")


def _health_handler(_: Dict[str, List[str]]):
    return {"status": "ok", "version": __version__}


def _flag_handler(func: Callable[[datetime.date], bool], key: str) -> Callable[[Dict[str, List[str]]], Dict]:
    def handler(query: Dict[str, List[str]]):
        dates = _collect_dates(query.get("dates"), query.get("start", [None])[0], query.get("end", [None])[0])
        return {"results": [{"date": date.isoformat(), key: func(date)} for date in dates]}

    return handler


def _interbank_handler(query: Dict[str, List[str]]):
    dates = _collect_dates(query.get("dates"), query.get("start", [None])[0], query.get("end", [None])[0])
    return {
        "results": [
            {"date": date.isoformat(), "is_interbank_trading_day": is_interbank_trading_day(date)}
            for date in dates
        ]
    }


def _a_share_handler(query: Dict[str, List[str]]):
    dates = _collect_dates(query.get("dates"), query.get("start", [None])[0], query.get("end", [None])[0])
    return {
        "results": [
            {"date": date.isoformat(), "is_a_share_trading_day": is_a_share_trading_day(date)}
            for date in dates
        ]
    }


def _holiday_detail_handler(query: Dict[str, List[str]]):
    dates = _collect_dates(query.get("dates"), query.get("start", [None])[0], query.get("end", [None])[0])
    results = []
    for date in dates:
        is_holiday_flag, name = get_holiday_detail(date)
        results.append({"date": date.isoformat(), "is_holiday": is_holiday_flag, "holiday_name": name})
    return {"results": results}


def _type_check_handler(query: Dict[str, List[str]]):
    date_value = query.get("date", [None])[0]
    if not date_value:
        raise ValueError("'date' query parameter is required for this endpoint.")

    type_value = query.get("type", [None])[0]
    if not type_value:
        raise ValueError("'type' query parameter is required for this endpoint.")

    try:
        checker = TYPE_CHECKERS[type_value]
    except KeyError:
        supported = ", ".join(sorted(TYPE_CHECKERS.keys()))
        raise ValueError(f"Unknown type '{type_value}'. Supported types: {supported}.")

    date = _parse_date(date_value)
    return {"date": date.isoformat(), "type": type_value, "result": checker(date)}


def _parse_bool(value: Optional[str], default: bool = True) -> bool:
    if value is None:
        return default
    lowered = value.lower()
    if lowered in {"true", "1", "yes", "on"}:
        return True
    if lowered in {"false", "0", "no", "off"}:
        return False
    raise ValueError("Boolean parameters accept true/false/1/0/yes/no/on/off")


def _range_required(query: Dict[str, List[str]]):
    start, end = query.get("start", [None])[0], query.get("end", [None])[0]
    if not start or not end:
        raise ValueError("'start' and 'end' query parameters are required for this endpoint.")
    start_date, end_date = _parse_date(start), _parse_date(end)
    if end_date < start_date:
        raise ValueError("end date must not be earlier than start date")
    return start_date, end_date


def _range_list_handler(
    func: Callable[..., List[datetime.date]], key: str, include_weekends_supported: bool = False
):
    def handler(query: Dict[str, List[str]]):
        start, end = _range_required(query)
        include_weekends_param = query.get("include_weekends", [None])[0]
        include_weekends = _parse_bool(include_weekends_param, default=True) if include_weekends_supported else True
        days = func(start, end, include_weekends) if include_weekends_supported else func(start, end)
        return {key: [day.isoformat() for day in days]}

    return handler


class _CalendarRequestHandler(BaseHTTPRequestHandler):
    routes: Dict[str, Callable[[Dict[str, List[str]]], Dict]] = {
        "/api/health": _health_handler,
        "/api/workdays": _flag_handler(is_workday, "is_workday"),
        "/api/holidays": _flag_handler(is_holiday, "is_holiday"),
        "/api/in-lieu": _flag_handler(is_in_lieu, "is_in_lieu"),
        "/api/holiday/detail": _holiday_detail_handler,
        "/api/date/type": _type_check_handler,
        "/api/holidays/range": _range_list_handler(get_holidays, "holidays", include_weekends_supported=True),
        "/api/workdays/range": _range_list_handler(get_workdays, "workdays", include_weekends_supported=True),
        "/api/interbank/trading-days": _interbank_handler,
        "/api/a-share/trading-days": _a_share_handler,
        "/api/interbank/trading-days/list": _range_list_handler(
            get_interbank_trading_days, "interbank_trading_days"
        ),
        "/api/a-share/trading-days/list": _range_list_handler(
            get_a_share_trading_days, "a_share_trading_days"
        ),
    }

    def _json_response(self, status: HTTPStatus, payload: Dict):
        response = json.dumps(payload).encode("utf-8")
        self.send_response(status.value)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def log_message(self, format, *args):
        return  # silence default logging

    def do_GET(self):  # noqa: N802
        parsed = urlparse(self.path)
        handler = self.routes.get(parsed.path)
        if not handler:
            self._json_response(HTTPStatus.NOT_FOUND, {"detail": "Not Found"})
            return
        try:
            payload = handler(parse_qs(parsed.query))
        except ValueError as exc:
            self._json_response(HTTPStatus.BAD_REQUEST, {"detail": str(exc)})
            return
        self._json_response(HTTPStatus.OK, payload)


def create_server(host: str = "0.0.0.0", port: int = 8000) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), _CalendarRequestHandler)


def run(host: str = "0.0.0.0", port: int = 8000):
    """Run the API service with the built-in HTTP server."""
    server = create_server(host, port)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        thread.join()
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
        server.server_close()


__all__ = [
    "create_server",
    "run",
]


if __name__ == "__main__":
    run()
