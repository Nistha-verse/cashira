from datetime import date

from app.services.validation import validate_rows


def test_validation_skips_bad_rows_and_reports_quality():
    rows = [
        {"transaction_date": "2024-01-01", "direction": "inflow", "category": "sales", "amount": "10"},
        {"transaction_date": "2024-01-01", "direction": "inflow", "category": "sales", "amount": "10"},
        {"transaction_date": "2024-01-02", "direction": "outflow", "category": "stock", "amount": "-1"},
        {"transaction_date": None, "direction": "outflow", "category": "stock", "amount": "2"},
        {"transaction_date": "2024-01-03", "direction": "other", "category": "other", "amount": "2"},
    ]
    result = validate_rows(rows)
    assert len(result.valid_rows) == 1
    assert result.valid_rows[0]["transaction_date"] == date(2024, 1, 1)
    assert result.report.duplicates == 1
    assert result.report.invalid_amounts == 1
    assert result.report.invalid_dates == 1
    assert result.report.invalid_directions == 1


def test_validation_counts_calendar_gaps_without_crashing():
    result = validate_rows(
        [
            {"transaction_date": "2024-01-01", "direction": "inflow", "category": "sales", "amount": 10},
            {"transaction_date": "2024-01-03", "direction": "inflow", "category": "sales", "amount": 12},
        ]
    )
    assert result.report.gaps == 1
