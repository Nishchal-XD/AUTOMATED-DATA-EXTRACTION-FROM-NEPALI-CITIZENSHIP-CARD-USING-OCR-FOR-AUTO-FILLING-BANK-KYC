from main import clean_field_text

tests=[('zfhgfu',1),('abcdef',3),('zfhgfu राम',1),('राम zfhgfu',1),('JOHN DOE',5)]
for txt,cid in tests:
    print(cid, txt, '->', clean_field_text(txt,cid))
