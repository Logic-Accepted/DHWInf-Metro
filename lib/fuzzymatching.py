from pypinyin import lazy_pinyin
from thefuzz import fuzz


def fuzzy_match_integrated(str1, str2):
    char_similarity = fuzz.ratio(str1, str2)
    pinyin_similarity = fuzz.ratio(
        "".join(lazy_pinyin(str1)), "".join(lazy_pinyin(str2))
    )
    return char_similarity * 0.3 + pinyin_similarity * 0.7
