import csv
import math
import pytest
from mayo_adpkd import calculate_metrics, process_batch, main


@pytest.mark.parametrize("growth,expected", [
    (1.0, "1A"), (2.0, "1B"), (3.5, "1C"),
    (5.0, "1D"), (7.0, "1E"),
])
def test_mayo_classes_against_published_growth_bands(growth, expected):
    age = 40
    httkv = 150 * (1 + growth / 100) ** age
    result = calculate_metrics(age=age, httkv_ml_per_m=httkv)
    assert result["mayo_class"] == expected
    assert result["estimated_annual_growth_percent"] == pytest.approx(growth, abs=0.0001)


@pytest.mark.parametrize("growth,expected", [
    (1.5, "1B"), (3.0, "1C"), (4.5, "1D"), (6.0, "1E"),
])
def test_exact_mayo_class_boundaries(growth, expected):
    age = 40
    httkv = 150 * (1 + growth / 100) ** age
    assert calculate_metrics(age=age, httkv_ml_per_m=httkv)["mayo_class"] == expected


def test_volume_and_height_equivalent_to_httkv():
    direct = calculate_metrics(age=40, httkv_ml_per_m=800)
    derived = calculate_metrics(age=40, tkv_ml=1440, height_m=1.8)
    assert direct == derived


def test_atypical_morphology_never_gets_typical_class():
    result = calculate_metrics(age=40, httkv_ml_per_m=1500, morphology="atypical")
    assert result["mayo_class"] is None
    assert result["estimated_annual_growth_percent"] is None


@pytest.mark.parametrize("values", [
    {"age": 14, "httkv_ml_per_m": 300},
    {"age": 81, "httkv_ml_per_m": 300},
    {"age": float("nan"), "httkv_ml_per_m": 300},
    {"age": 40, "httkv_ml_per_m": float("inf")},
    {"age": 40, "httkv_ml_per_m": 0},
    {"age": 40, "tkv_ml": 800},
    {"age": 40, "tkv_ml": 800, "height_m": 0},
    {"age": 40, "tkv_ml": 800, "height_m": 1.7, "httkv_ml_per_m": 400},
    {"age": 40, "httkv_ml_per_m": 400, "morphology": "unknown"},
    {"v1": 12, "v2": 3},
])
def test_invalid_inputs_are_rejected(values):
    with pytest.raises((ValueError, TypeError)):
        calculate_metrics(**values)


def test_batch_preserves_identifiers_and_computes_classes(tmp_path):
    source = tmp_path / "cases.csv"
    destination = tmp_path / "out.csv"
    source.write_text("case_id,age,tkv_ml,height_m,morphology\n"
                      "case-1,40,800,1.6,typical\n"
                      "case-2,40,800,1.6,atypical\n", encoding="utf-8")
    assert process_batch(source, destination) == 2
    with destination.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    assert rows[0]["case_id"] == "case-1"
    assert rows[0]["mayo_class"] in ("1A", "1B", "1C", "1D", "1E")
    assert rows[1]["mayo_class"] == ""


def test_invalid_batch_never_generates_partial_result(tmp_path):
    source = tmp_path / "cases.csv"
    destination = tmp_path / "out.csv"
    source.write_text("age,httkv_ml_per_m\n40,600\n41,not-a-number\n")
    with pytest.raises(ValueError, match="CSV row 3"):
        process_batch(source, destination)
    assert not destination.exists()


def test_missing_empty_and_reserved_csv(tmp_path):
    with pytest.raises(FileNotFoundError):
        process_batch(tmp_path / "missing.csv", tmp_path / "out.csv")
    source = tmp_path / "input.csv"
    source.write_text("")
    with pytest.raises(ValueError, match="empty"):
        process_batch(source, tmp_path / "out.csv")
    source.write_text("age,mayo_class\n40,1A\n")
    with pytest.raises(ValueError, match="reserved"):
        process_batch(source, tmp_path / "out.csv")


def test_batch_rejects_overwriting_input(tmp_path):
    source = tmp_path / "input.csv"
    source.write_text("age,httkv_ml_per_m\n40,600\n")
    with pytest.raises(ValueError, match="must differ"):
        process_batch(source, source)


def test_cli_single(capsys):
    assert main(["single", "--age", "40", "--httkv-ml-per-m", "800"]) == 0
    assert '"mayo_class"' in capsys.readouterr().out


def test_csv_output_escapes_spreadsheet_formulas(tmp_path):
    source = tmp_path / "source.csv"
    output = tmp_path / "output.csv"
    source.write_text('case_id,age,httkv_ml_per_m\n"=SUM(1,2)",40,800\n')
    process_batch(source, output)
    with output.open(newline="", encoding="utf-8") as stream:
        row = next(csv.DictReader(stream))
    assert row["case_id"] == "'=SUM(1,2)"
    assert row["mayo_class"] in ("1A", "1B", "1C", "1D", "1E")
