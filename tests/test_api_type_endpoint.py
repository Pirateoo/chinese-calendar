# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import json
import threading
import urllib.error
import urllib.request
import unittest

from chinese_calendar.api import create_server


class APIDateTypeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = create_server(host="127.0.0.1", port=0)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=1)

    def _url(self, path: str) -> str:
        return f"http://127.0.0.1:{self.port}{path}"

    def test_holiday_type_true(self):
        response = urllib.request.urlopen(self._url("/api/date/type?date=2018-02-16&type=holiday"))
        payload = json.loads(response.read().decode("utf-8"))
        self.assertTrue(payload["result"])
        self.assertEqual(payload["type"], "holiday")

    def test_workday_type_false(self):
        response = urllib.request.urlopen(self._url("/api/date/type?date=2018-02-16&type=workday"))
        payload = json.loads(response.read().decode("utf-8"))
        self.assertFalse(payload["result"])

    def test_unknown_type_returns_error(self):
        with self.assertRaises(urllib.error.HTTPError) as exc:
            urllib.request.urlopen(self._url("/api/date/type?date=2018-02-16&type=unknown"))
        self.assertEqual(exc.exception.code, 400)

    def test_missing_date_returns_error(self):
        with self.assertRaises(urllib.error.HTTPError) as exc:
            urllib.request.urlopen(self._url("/api/date/type?type=holiday"))
        self.assertEqual(exc.exception.code, 400)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
