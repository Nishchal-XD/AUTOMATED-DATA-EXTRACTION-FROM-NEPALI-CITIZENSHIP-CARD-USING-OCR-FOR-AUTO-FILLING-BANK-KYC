import re

def test_dist_clean():
    text = 'Permanent Address:.-. — District: LALITPUR'
    text = text.replace("\n", " ").strip()
    text = re.sub(r"\s+", " ", text)
    print('step 1 normalized:', repr(text))
    
    text = re.sub(r"(?i).*?district\s*[:=]*\s*", "", text).strip()
    print('step 2 after district strip:', repr(text))
    
    text = re.sub(r"[^A-Za-z\s]", "", text).strip()
    print('step 3 after non-alpha:', repr(text))
    
    text = re.sub(r"\s+", " ", text).strip()
    print('step 4 final:', repr(text))
    
    return text

print(test_dist_clean())
