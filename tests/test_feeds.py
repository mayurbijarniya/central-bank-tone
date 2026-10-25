from datetime import date

from cbtone import feeds

RSS = b"""<?xml version="1.0"?>
<rss version="2.0"><channel>
<item><title>Waller, The Economic Outlook</title>
<link>https://www.federalreserve.gov/newsevents/speech/waller20261008a.htm</link>
<pubDate>Thu, 8 Oct 2026 08:30:00 GMT</pubDate></item>
<item><title>No date</title><link>https://example.test/x</link></item>
</channel></rss>"""

RDF = b"""<?xml version="1.0"?>
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns="http://purl.org/rss/1.0/"
  xmlns:dc="http://purl.org/dc/elements/1.1/">
<item><title>Speech: Housing</title><link>https://www.bankofcanada.ca/2026/10/housing/</link>
<dc:date>2026-10-01T15:05:48+00:00</dc:date></item>
</rdf:RDF>"""


def test_rss_and_rdf_items_are_read():
    assert feeds.items(RSS) == [{
        "title": "Waller, The Economic Outlook",
        "url": "https://www.federalreserve.gov/newsevents/speech/waller20261008a.htm",
        "date": date(2026, 10, 8),
    }]
    assert feeds.items(RDF)[0]["date"] == date(2026, 10, 1)


def test_page_text_keeps_paragraphs_and_drops_scripts():
    page = (b"<html><script>var x = 'Inflation is a script variable here';</script>"
            b"<p>Inflation has come down a long way but remains above our target.</p>"
            b"<p>Short.</p><footer><p>Copyright notice of the bank and its many affiliates.</p>"
            b"</footer></html>")
    assert feeds.page_text(page) == (
        "Inflation has come down a long way but remains above our target."
    )


def test_speech_links_filter_out_press_releases():
    assert feeds.SPEECH_LINK["XM"].search(
        "https://www.ecb.europa.eu//press/key/date/2026/html/ecb.sp261021~d1.en.html")
    assert not feeds.SPEECH_LINK["XM"].search(
        "https://www.ecb.europa.eu//press/pr/date/2026/html/ecb.pr261023~a3.en.html")
    assert not feeds.SPEECH_LINK["XM"].search(
        "https://www.ecb.europa.eu//press/key/date/2026/html/ecb.sp261021_1~d1.en.pdf")
