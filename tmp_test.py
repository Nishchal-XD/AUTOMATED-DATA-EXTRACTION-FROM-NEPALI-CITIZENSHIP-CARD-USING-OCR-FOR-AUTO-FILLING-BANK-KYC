from main import parse_to_html_date

samples = [
    'जारी तिते २०००-०ह-ह७७९५',
    'जारी तिते २०००-०४-१२',
    'Issued: 2019/07/04',
    'जारी मिति : २०५२९.०७-०२',
]

print("Testing noisy issued-date inputs:")
print("="*60)
for s in samples:
    print(repr(s), '->', repr(parse_to_html_date(s)))
