from main import clean_field_text, parse_to_html_date

samples = [
    "जारी मिति : २०५२९.०७-०२",
    "Issued Date: 2019/7/4",
    "Date: 2076-04-12",
    "जारी मिति : २०७६-०४-१२"
]
print('raw->clean->parsed')
for s in samples:
    cleaned = clean_field_text(s, 13)
    parsed = parse_to_html_date(s)
    print(s, '->', cleaned, '->', parsed)
