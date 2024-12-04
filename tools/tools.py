import re
from datetime import datetime
from dateutil.relativedelta import relativedelta


def convert_date(date):
    months = {
        "jan": "01",
        "f": "02",
        "ma": "03",
        "av": "04",
        "mai": "05",
        "juin": "06",
        "let": "07",
        "ao": "08",
        "tembre": "09",
        "obre": "10",
        "vembre": "11",
        "cembre": "12",
    }
    date = re.sub(r"[^a-z0-9 ]", "", date.lower())
    day, month, year = date.split()
    for key in months:
        if key in month:
            month = months.get(key)
            break
    else:
        raise ValueError(f"Invalid or unsupported month: {month}")
    date = f"{year}-{month}-{day}"
    return (datetime.strptime(date, "%Y-%m-%d") + relativedelta(months=1)).strftime(
        "%Y-%m-%dT%H:%M:%S.%f%z"
    )


def format_date(date):
    print(date)
    value = int(re.sub(r"[^0-9]", "", date))
    now = datetime.now()

    if "jour" in date:
        new_date = now - relativedelta(days=value)
    elif "mois" in date:
        new_date = now - relativedelta(months=value)
    elif "heure" in date:
        new_date = now - relativedelta(hours=value)
    elif "min" in date:
        new_date = now - relativedelta(minutes=value)
    else:
        new_date = now

    new_date_plus_month = new_date + relativedelta(months=1)

    return new_date_plus_month.strftime("%Y-%m-%dT%H:%M:%S.%f%z")
