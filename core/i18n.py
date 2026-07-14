import json
from pathlib import Path

_I18N_DIR = Path(__file__).resolve().parent.parent / "i18n"
_SUPPORTED_LANGS = ("es", "en")
_DEFAULT_LANG = "es"

_cache = {}


def _load_lang(lang):
    if lang not in _cache:
        path = _I18N_DIR / f"{lang}.json"
        with open(path, encoding="utf-8") as f:
            _cache[lang] = json.load(f)
    return _cache[lang]


def t(key, lang=_DEFAULT_LANG, **kwargs):
    lang = lang if lang in _SUPPORTED_LANGS else _DEFAULT_LANG
    strings = _load_lang(lang)
    text = strings.get(key, key)
    return text.format(**kwargs) if kwargs else text
