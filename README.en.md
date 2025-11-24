# Chinese Calendar

[![Package](https://img.shields.io/pypi/v/chinesecalendar.svg)](https://pypi.python.org/pypi/chinesecalendar)
[![Travis](https://img.shields.io/travis/LKI/chinese-calendar.svg)](https://travis-ci.org/LKI/chinese-calendar)
[![License](https://img.shields.io/github/license/LKI/chinese-calendar.svg)](https://github.com/LKI/chinese-calendar/blob/master/LICENSE)
[![README](https://img.shields.io/badge/简介-中文-brightgreen.svg)](https://github.com/LKI/chinese-calendar/blob/master/README.md)

Check if some date is workday or holiday in China.
Support 2004 ~ 2026.

## Installation

```
pip install chinesecalendar
```

### Local development/testing

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
pip install -U pytest pytest-cov
pytest
```

## Upgrade

```
pip install -U chinesecalendar
```

Chinese government announces holiday arrangement usually during November.
This project will release new version after official announcement.

## Sample

``` python
import datetime

# Check if 2018-04-30 is holiday in China
from chinese_calendar import is_holiday, is_workday
april_last = datetime.date(2018, 4, 30)
assert is_workday(april_last) is False
assert is_holiday(april_last) is True

# or check and get the holiday name
import chinese_calendar as calendar  # 也可以这样 import
on_holiday, holiday_name = calendar.get_holiday_detail(april_last)
assert on_holiday is True
assert holiday_name == calendar.Holiday.labour_day.value

# even check if a holiday is in lieu
import chinese_calendar
assert chinese_calendar.is_in_lieu(datetime.date(2006, 2, 1)) is False
assert chinese_calendar.is_in_lieu(datetime.date(2006, 2, 2)) is True

# New: interbank & A-share trading day helpers
assert chinese_calendar.is_interbank_trading_day(datetime.date(2018, 2, 11)) is True  # weekend make-up day is open
assert chinese_calendar.is_a_share_trading_day(datetime.date(2018, 2, 11)) is False    # A-share trades Mon-Fri only
assert chinese_calendar.get_interbank_trading_days(datetime.date(2018, 2, 10), datetime.date(2018, 2, 12)) == [
    datetime.date(2018, 2, 11),
    datetime.date(2018, 2, 12),
]
assert chinese_calendar.get_a_share_trading_days(datetime.date(2018, 2, 10), datetime.date(2018, 2, 12)) == [
    datetime.date(2018, 2, 12),
]
```

### Network API service

You can run the built-in HTTP server to expose the checks as an API that supports multiple dates or
date ranges:

```bash
python -m chinese_calendar.api
```

Example requests:

```bash
curl "http://127.0.0.1:8000/api/a-share/trading-days?start=2018-02-10&end=2018-02-12"           # per-day flags
curl "http://127.0.0.1:8000/api/interbank/trading-days?dates=2018-02-11&dates=2018-05-01"       # per-day flags
curl "http://127.0.0.1:8000/api/interbank/trading-days/list?start=2018-02-10&end=2018-02-12"    # list of trading days
curl "http://127.0.0.1:8000/api/workdays/range?start=2018-02-10&end=2018-02-12&include_weekends=false"
curl "http://127.0.0.1:8000/api/holiday/detail?dates=2018-02-11&dates=2018-05-01"
```

## Other Languages

If you fail to use Python directly,
you can translate the [constants file][constants.py] to get the complete chinese holiday arrangement.

## Contributing

1. Fork & Clone this project
2. Modify [calendar definition file][scripts/data.py]
3. Run [script][scripts/__init__.py] to generate the [constants file][constants.py]
4. Create a PR

[constants.py]: https://github.com/LKI/chinese-calendar/blob/master/chinese_calendar/constants.py
[scripts/data.py]: https://github.com/LKI/chinese-calendar/blob/master/chinese_calendar/scripts/data.py
[scripts/__init__.py]: https://github.com/LKI/chinese-calendar/blob/master/chinese_calendar/scripts/__init__.py
