"""Ensure father and mother name labels are stripped correctly."""

# import the actual cleaning routine from main so tests stay up to date
import sys
sys.path.append(r"c:\nagarikta")
from main import clean_field_text


def run_tests():
    cases = [
        # father name variants
        ("Father Name: Ram Kumar", 2, "Ram Kumar"),
        ("father's name: Ram Kumar", 2, "Ram Kumar"),
        ("Father's Name Ram Kumar", 2, "Ram Kumar"),
        ("father name Ram Kumar", 2, "Ram Kumar"),
        ("Ram Kumar", 2, "Ram Kumar"),
        # names with multiple punctuation/composite labels
        ("Full name; father name: Ram Kumar", 2, "Ram Kumar"),
        ("Full Name;", 5, ""),
        ("Full Name;  ", 5, ""),
        ("Full Name; John Doe", 5, "John Doe"),
        # mother name variants
        ("Mother Name: Sita Devi", 3, "Sita Devi"),
        ("mother's name: Sita Devi", 3, "Sita Devi"),
        ("Mother's Name Sita Devi", 3, "Sita Devi"),
        ("mother name Sita Devi", 3, "Sita Devi"),
        ("Sita Devi", 3, "Sita Devi"),
        # noisy inputs that should be dropped
        ("ABCD", 3, ""),
        ("12", 3, ""),
        ("A", 3, ""),
        # Nepali father name
        ("बुबुको नर/थेर: महेश निरौल", 2, "महेश निरौल"),
        # father label with stray quotes/question marks (OCR artifact)
        ("बाबुको नाम थह?”” शिबजीकार्क", 2, "शिबजीकार्क"),
        # noisy prefix and trademark symbol
        ("a INAntO® JOHN SHRESTHA", 2, "JOHN SHRESTHA"),
        # complex nepali string should pass through unchanged
        ("बाढुकक्पोभिअर गोविदद्रैष्ठ", 2, "बाढुकक्पोभिअर गोविदद्रैष्ठ"),
        # placeholder missing mother
        ("XXX", 3, ""),
        # ascii-only noise on Nepali side should be dropped entirely
        ("zfhgfu", 1, ""),
        ("abcdef", 3, ""),
        # mixed Nepali+ASCII should keep only Nepali portion
        ("zfhgfu राम", 1, "राम"),
        ("राम zfhgfu", 1, "राम"),
        # english field should not be cleared by the Nepali rule
        ("JOHN DOE", 5, "JOHN DOE"),        # the following two cases were reported as errors in Nepali data
        ("धरः भरत बहादुर शाह", 2, "भरत बहादुर शाह"),
        ("उअकैको नाम लक्ष्मी कुमारी सिंह", 1, "लक्ष्मी कुमारी सिंह"),
        ("उअकैको नाम लक्ष्मी कुमारी सिंह", 3, "लक्ष्मी कुमारी सिंह"),    ]

    print("Testing parent name extraction:")
    print("=" * 60)
    all_good = True
    for text, class_id, expected in cases:
        got = clean_field_text(text, class_id)
        status = "✓ PASS" if got == expected else "✗ FAIL"
        if got != expected:
            all_good = False
        print(f"{status} | class {class_id} | '{text}' -> '{got}' (expected '{expected}')")
    print("=" * 60)
    print("All tests passed!" if all_good else "Some tests failed")


if __name__ == "__main__":
    run_tests()
