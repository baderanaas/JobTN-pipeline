import re
from datetime import datetime
from dateutil.relativedelta import relativedelta


def convert_date(date):
    months = {
        "janvier": "01",
        "février": "02",
        "mars": "03",
        "avril": "04",
        "mai": "05",
        "juin": "06",
        "juillet": "07",
        "août": "08",
        "septembre": "09",
        "octobre": "10",
        "novembre": "11",
        "décembre": "12",
    }
    date = re.sub(r"[^a-z0-9 ]", "", date.lower())
    day, month, year = date.split()
    date = f"{year}-{months[month]}-{day}"
    return (datetime.strptime(date, "%Y-%m-%d") + relativedelta(months=1)).strftime(
        "%Y-%m-%d"
    )
