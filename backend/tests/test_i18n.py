from app.i18n import CATALOGS, keys, placeholders, t


def test_catalog_keys_and_placeholders_match():
    all_keys = keys()
    assert all(set(CATALOGS[lang]) == all_keys for lang in CATALOGS)
    for key in all_keys:
        assert placeholders(key, "en") == placeholders(key, "hi") == placeholders(key, "bn")


def test_reminder_renders_in_all_languages():
    params = {"name": "Riya", "amount": 8986.34}
    rendered = {lang: t("reminders.payment", lang, **params) for lang in CATALOGS}
    assert all("Riya" in value for value in rendered.values())
    assert "EMI" in rendered["en"]
    assert "EMI" in rendered["hi"]
    assert "EMI" in rendered["bn"]
    assert rendered["hi"] != rendered["en"]
    assert rendered["bn"] != rendered["en"]
