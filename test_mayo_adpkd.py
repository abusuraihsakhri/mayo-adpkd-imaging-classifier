import pytest
from mayo_adpkd import calculate_metrics, process_batch


def test_mayo_adpkd_single():
    res = calculate_metrics(v1=12.0, v2=4.0)
    assert "score" in res
    assert "classification" in res
    assert res["score"] > 0


def test_mayo_adpkd_batch(tmp_path):
    csv_in = tmp_path / "in.csv"
    csv_out = tmp_path / "out.csv"
    csv_in.write_text("Patient,v1,v2\nPat_001,15.0,3.0\nPat_002,5.0,1.0\n", encoding="utf-8")

    process_batch(str(csv_in), str(csv_out))
    assert csv_out.exists()
    content = csv_out.read_text(encoding="utf-8")
    assert "Pat_001" in content
    assert "score" in content


def test_mayo_adpkd_batch_missing_input():
    """Verify that process_batch raises FileNotFoundError for missing input."""
    with pytest.raises(FileNotFoundError, match="Input CSV file not found"):
        process_batch("nonexistent_file.csv", "output.csv")


def test_mayo_adpkd_batch_invalid_output_dir(tmp_path):
    """Verify that process_batch raises FileNotFoundError for invalid output dir."""
    csv_in = tmp_path / "in.csv"
    csv_in.write_text("Patient,v1\nPat_001,15.0\n", encoding="utf-8")

    with pytest.raises(FileNotFoundError, match="Output directory does not exist"):
        process_batch(str(csv_in), "/nonexistent_dir/output.csv")


def test_mayo_adpkd_batch_empty_csv(tmp_path):
    """Verify that process_batch raises ValueError for empty CSV."""
    csv_in = tmp_path / "empty.csv"
    csv_in.write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="empty or has no headers"):
        process_batch(str(csv_in), str(tmp_path / "out.csv"))


def test_calculate_metrics_classification_tiers():
    """Verify classification tier boundaries."""
    low = calculate_metrics(v1=5.0)
    assert low["classification"] == "Low / Standard"

    moderate = calculate_metrics(v1=15.0)
    assert moderate["classification"] == "Moderate / Intermediate"

    high = calculate_metrics(v1=30.0)
    assert high["classification"] == "High / Severe"
