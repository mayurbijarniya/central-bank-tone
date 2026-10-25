from datetime import date

import pytest

from cbtone import banks


@pytest.mark.parametrize(
    ("description", "code"),
    [
        ("Speech by Mr Shaktikanta Das, Governor of the Reserve Bank of India, at the BIS.", "IN"),
        ("Remarks by Mr Jerome H Powell, Chair of the Board of Governors of the Federal Reserve "
         "System, at the European Central Bank Forum, Sintra.", "US"),
        ("Speech by Mr John C Williams, President of the Federal Reserve Bank of New York.", "US"),
        ("Speech by Mr Jens Weidmann, President of the Deutsche Bundesbank and Chairman of the "
         "Board of Directors of the Bank for International Settlements.", "DE"),
        ("Speech by Ms Wu Xiaoling, Deputy Governor of the People¿s Bank of China.", "CN"),
        ("Speech by the General Manager of the Bank for International Settlements.", None),
        (None, None),
    ],
)
def test_the_first_named_bank_is_the_speakers(description, code):
    assert banks.bank_of(description) == code


def test_euro_area_governors_count_towards_the_euro_from_entry():
    assert banks.policy_area("DE", date(1998, 12, 31)) == "DE"
    assert banks.policy_area("DE", date(1999, 1, 1)) == "XM"
    assert banks.policy_area("HR", date(2022, 12, 31)) == "HR"
    assert banks.policy_area("HR", date(2023, 1, 1)) == "XM"
    assert banks.policy_area("GB", date(2010, 1, 1)) == "GB"
    assert banks.policy_area(None, date(2010, 1, 1)) is None


def test_every_bank_code_is_unique():
    codes = [code for code, _, _ in banks.BANKS]
    assert len(codes) == len(set(codes))
