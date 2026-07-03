import main
import sys

def test_cleaning():
    cases = [
        ("बाढ्को हमिपर रोपेत गहादुर सिह", 2),
        ("उक्किको नाम परः रिपारिह", 3),
        ("जामषर बिश्ञात सिंह ठकर", 1),
        ("Dailekh District", 10),
        ("Banke district", 10),
        ("Permanent District: Banke", 10),
        ("बाबुको नाम थरः मान बहादुर", 2)
    ]

    for text, class_id in cases:
        cleaned = main.clean_field_text(text, class_id)
        # specifically if it's class 1,2,3 we want to see what is returned
        print(f"[{class_id}] '{text}' -> '{cleaned}'")

if __name__ == "__main__":
    test_cleaning()
