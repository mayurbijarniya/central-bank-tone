"""Which central bank gave each speech.

The BIS archive has no institution column: the speaker's bank is named in the
description ("Speech by Mr Shaktikanta Das, Governor of the Reserve Bank of
India, at ..."). Each bank is listed with the names it appears under, and a
speech is assigned to the bank named first, since a host institution or a
second role ("and Chairman of the Board of the Bank for International
Settlements") comes later in the sentence.

Codes are the BIS reference areas used in the policy rate data. Governors of
euro area national central banks sit on the ECB Governing Council once their
country joins, so from that date their speeches count towards the euro area.
"""

from __future__ import annotations

import re
from datetime import date

# (code, name, names as they appear in descriptions, lower case)
BANKS: list[tuple[str, str, tuple[str, ...]]] = [
    ("US", "Federal Reserve", (
        "federal reserve system", "board of governors of the federal reserve",
        "federal reserve bank", "federal reserve board", "us federal reserve",
    )),
    ("XM", "European Central Bank", ("european central bank", "ecb")),
    ("GB", "Bank of England", ("bank of england",)),
    ("JP", "Bank of Japan", ("bank of japan",)),
    ("CA", "Bank of Canada", ("bank of canada",)),
    ("AU", "Reserve Bank of Australia", ("reserve bank of australia",)),
    ("NZ", "Reserve Bank of New Zealand", ("reserve bank of new zealand",)),
    ("CH", "Swiss National Bank", (
        "swiss national bank", "banque nationale suisse", "schweizerische nationalbank",
    )),
    ("SE", "Sveriges Riksbank", ("sveriges riksbank", "riksbank", "bank of sweden")),
    ("NO", "Norges Bank", ("norges bank", "central bank of norway")),
    ("DK", "Danmarks Nationalbank", ("danmarks nationalbank", "national bank of denmark")),
    ("IS", "Central Bank of Iceland", ("central bank of iceland",)),
    ("IN", "Reserve Bank of India", ("reserve bank of india",)),
    ("CN", "People's Bank of China", (
        "people's bank of china", "people’s bank of china", "people¿s bank of china",
        "peoples bank of china",
    )),
    ("HK", "Hong Kong Monetary Authority", ("hong kong monetary authority",)),
    ("KR", "Bank of Korea", ("bank of korea",)),
    ("ID", "Bank Indonesia", ("bank indonesia",)),
    ("MY", "Bank Negara Malaysia", ("bank negara malaysia", "central bank of malaysia")),
    ("PH", "Bangko Sentral ng Pilipinas", (
        "bangko sentral ng pilipinas", "central bank of the philippines",
    )),
    ("TH", "Bank of Thailand", ("bank of thailand",)),
    ("SA", "Saudi Central Bank", (
        "saudi arabian monetary", "saudi central bank", "saudi arabian monetary authority",
    )),
    ("KW", "Central Bank of Kuwait", ("central bank of kuwait",)),
    ("IL", "Bank of Israel", ("bank of israel",)),
    ("TR", "Central Bank of the Republic of Türkiye", (
        "central bank of the republic of turkey", "central bank of the republic of türkiye",
        "central bank of turkey",
    )),
    ("ZA", "South African Reserve Bank", ("south african reserve bank",)),
    ("MA", "Bank Al-Maghrib", ("bank al-maghrib",)),
    ("BR", "Central Bank of Brazil", ("central bank of brazil", "banco central do brasil")),
    ("MX", "Bank of Mexico", ("bank of mexico", "banco de méxico", "banco de mexico")),
    ("CL", "Central Bank of Chile", ("central bank of chile",)),
    ("CO", "Central Bank of Colombia", ("central bank of colombia", "banco de la república")),
    ("PE", "Central Reserve Bank of Peru", ("central reserve bank of peru",)),
    ("AR", "Central Bank of Argentina", (
        "central bank of argentina", "central bank of the argentine republic",
    )),
    ("CZ", "Czech National Bank", ("czech national bank",)),
    ("HU", "Magyar Nemzeti Bank", (
        "magyar nemzeti bank", "central bank of hungary", "national bank of hungary",
    )),
    ("PL", "National Bank of Poland", ("national bank of poland", "narodowy bank polski")),
    ("RO", "National Bank of Romania", ("national bank of romania",)),
    ("RS", "National Bank of Serbia", ("national bank of serbia",)),
    ("MK", "National Bank of North Macedonia", (
        "national bank of the republic of north macedonia",
        "national bank of the republic of macedonia",
    )),
    ("RU", "Bank of Russia", ("bank of russia", "central bank of the russian federation")),
    ("HR", "Croatian National Bank", ("croatian national bank",)),
    # Euro area national central banks: their own rate until they join the euro.
    ("DE", "Deutsche Bundesbank", ("deutsche bundesbank", "bundesbank")),
    ("FR", "Bank of France", ("bank of france", "banque de france")),
    ("IT", "Bank of Italy", ("bank of italy", "banca d'italia")),
    ("ES", "Bank of Spain", ("bank of spain", "banco de españa")),
    ("NL", "De Nederlandsche Bank", ("netherlands bank", "de nederlandsche bank")),
    ("BE", "National Bank of Belgium", ("national bank of belgium",)),
    ("AT", "Oesterreichische Nationalbank", (
        "austrian national bank", "central bank of the republic of austria",
        "oesterreichische nationalbank",
    )),
    ("PT", "Banco de Portugal", ("bank of portugal", "banco de portugal")),
    ("GR", "Bank of Greece", ("bank of greece",)),
    ("FI", "Bank of Finland", ("bank of finland",)),
    ("IE", "Central Bank of Ireland", (
        "central bank of ireland", "central bank and financial services authority of ireland",
    )),
    ("LU", "Central Bank of Luxembourg", ("central bank of luxembourg",)),
    ("SI", "Bank of Slovenia", ("bank of slovenia",)),
    ("CY", "Central Bank of Cyprus", ("central bank of cyprus",)),
    ("MT", "Central Bank of Malta", ("central bank of malta",)),
    ("SK", "National Bank of Slovakia", ("national bank of slovakia",)),
    ("EE", "Bank of Estonia", ("bank of estonia", "eesti pank")),
    ("LV", "Bank of Latvia", ("bank of latvia", "latvijas banka")),
    ("LT", "Bank of Lithuania", ("bank of lithuania",)),
    ("BG", "Bulgarian National Bank", ("bulgarian national bank",)),
    # Frequent speakers whose policy rates the BIS does not publish: scored, not tested.
    ("SG", "Monetary Authority of Singapore", ("monetary authority of singapore",)),
    ("PK", "State Bank of Pakistan", ("state bank of pakistan",)),
    ("LK", "Central Bank of Sri Lanka", ("central bank of sri lanka",)),
    ("KE", "Central Bank of Kenya", ("central bank of kenya",)),
    ("NG", "Central Bank of Nigeria", ("central bank of nigeria",)),
    ("GH", "Bank of Ghana", ("bank of ghana",)),
    ("UG", "Bank of Uganda", ("bank of uganda",)),
    ("ZM", "Bank of Zambia", ("bank of zambia",)),
    ("MU", "Bank of Mauritius", ("bank of mauritius",)),
    ("UA", "National Bank of Ukraine", ("national bank of ukraine",)),
    ("AL", "Bank of Albania", ("bank of albania",)),
    ("XK", "Central Bank of Kosovo", ("central bank of the republic of kosovo",)),
    ("BH", "Central Bank of Bahrain", ("central bank of bahrain",)),
    ("FJ", "Reserve Bank of Fiji", ("reserve bank of fiji",)),
    ("PG", "Bank of Papua New Guinea", ("bank of papua new guinea",)),
    ("BB", "Central Bank of Barbados", ("central bank of barbados",)),
    ("TT", "Central Bank of Trinidad and Tobago", ("central bank of trinidad and tobago",)),
    ("NA", "Bank of Namibia", ("bank of namibia",)),
    ("BW", "Bank of Botswana", ("bank of botswana",)),
    ("MW", "Reserve Bank of Malawi", ("reserve bank of malawi",)),
]

# The day each country's central bank joined the ECB Governing Council.
EURO_ENTRY = {
    **{c: date(1999, 1, 1) for c in ("DE", "FR", "IT", "ES", "NL", "BE", "AT", "PT", "FI", "IE",
                                    "LU")},
    "GR": date(2001, 1, 1),
    "SI": date(2007, 1, 1),
    "CY": date(2008, 1, 1),
    "MT": date(2008, 1, 1),
    "SK": date(2009, 1, 1),
    "EE": date(2011, 1, 1),
    "LV": date(2014, 1, 1),
    "LT": date(2015, 1, 1),
    "HR": date(2023, 1, 1),
    "BG": date(2026, 1, 1),
}

NAMES = {code: name for code, name, _ in BANKS}

REGIONS = {
    **dict.fromkeys(("US", "CA", "MX", "BR", "CL", "CO", "PE", "AR", "BB", "TT"), "Americas"),
    **dict.fromkeys(("XM", "GB", "CH", "SE", "NO", "DK", "IS", "CZ", "HU", "PL", "RO", "RS",
                     "MK", "RU", "HR", "DE", "FR", "IT", "ES", "NL", "BE", "AT", "PT", "GR",
                     "FI", "IE", "LU", "SI", "CY", "MT", "SK", "EE", "LV", "LT", "BG", "UA",
                     "AL", "XK"), "Europe"),
    **dict.fromkeys(("JP", "CN", "HK", "KR", "IN", "ID", "MY", "PH", "TH", "SG", "PK", "LK",
                     "AU", "NZ", "FJ", "PG"), "Asia-Pacific"),
    **dict.fromkeys(("SA", "KW", "IL", "TR", "BH", "ZA", "MA", "KE", "NG", "GH", "UG", "ZM",
                     "MU", "NA", "BW", "MW"), "Middle East and Africa"),
}

_PATTERN = re.compile(
    "|".join(
        f"(?P<b{i}_{j}_{code}>\\b{re.escape(alias)}\\b)"
        for i, (code, _, aliases) in enumerate(BANKS)
        for j, alias in enumerate(sorted(aliases, key=len, reverse=True))
    )
)


def bank_of(description: str | None) -> str | None:
    """The code of the central bank named first in a speech description."""
    if not description:
        return None
    match = _PATTERN.search(description.lower())
    if match is None:
        return None
    return match.lastgroup.rsplit("_", 1)[1]


def policy_area(code: str | None, on: date) -> str | None:
    """The policy rate a bank's speech speaks to: the euro area once its country joins."""
    if code is None:
        return None
    entry = EURO_ENTRY.get(code)
    if entry is not None and on >= entry:
        return "XM"
    return code
