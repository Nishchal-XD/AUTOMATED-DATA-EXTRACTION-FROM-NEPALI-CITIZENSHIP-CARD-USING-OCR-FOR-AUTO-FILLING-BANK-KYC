from main import parse_to_html_date

samples = [
    'जारी तिते २०००-०ह-ह७९९५',
    'जारी तिते २०००-०४-१२',
    'Issued: 2019/07/04',
    'जारी मिति : २०५२९.०७-०२',
]

lines = ["Testing noisy issued-date inputs:", "="*60]
for s in samples:
    lines.append(f"{s!r} -> {parse_to_html_date(s)!r}")

with open('issued_noise_results.txt','w',encoding='utf-8') as f:
    f.write("\n".join(lines))

print("done, written to issued_noise_results.txt")
