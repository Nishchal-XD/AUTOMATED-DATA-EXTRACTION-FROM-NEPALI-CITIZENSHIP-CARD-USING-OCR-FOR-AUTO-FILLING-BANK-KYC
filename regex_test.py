import re
pattern=re.compile(r'(?:बुव(?:ाको|ुको)?|बाबु(?:को)?|बुब)(?:को)?(?:\s*नर/?थेर)?')
texts=['बुबुको नर/थेर: महेश निरौल','बुबाको नर थेर: राम','बुबु नरथेर:xyz']
for text in texts:
    m=pattern.match(text)
    print(text, '->', m.group() if m else None)
