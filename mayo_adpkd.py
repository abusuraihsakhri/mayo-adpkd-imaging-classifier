#!/usr/bin/env python3
"""Mayo Imaging Classification (MIC) for typical ADPKD, ages 15–80.

Based on Irazabal et al., JASN 2015 and KDIGO 2025. This classifies
age-adjusted height-adjusted total kidney volume; it does NOT predict an
individual patient's eGFR or determine eligibility for treatment.
"""
import argparse
import csv
import json
import math
from pathlib import Path

STARTING_HTTKV = 150.0  # mL/m, theoretical baseline at birth
BOUNDARIES = ((1.5, "1A"), (3.0, "1B"), (4.5, "1C"), (6.0, "1D"))


def _positive_number(value, label):
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be a finite positive number") from exc
    if not math.isfinite(result) or result <= 0:
        raise ValueError(f"{label} must be a finite positive number")
    return result


def calculate_metrics(*, age, tkv_ml=None, height_m=None,
                      httkv_ml_per_m=None, morphology="typical"):
    """Return MIC class for typical morphology, or unclassified for atypical.

    Supply either htTKV in mL/m, or TKV in mL together with height in meters.
    The growth percentage is the model-implied annual TKV growth, not an
    observed longitudinal rate.
    """
    years = _positive_number(age, "age")
    if not 15 <= years <= 80:
        raise ValueError("MIC is validated for ages 15–80 years")
    morph = str(morphology).strip().lower()
    if morph not in ("typical", "atypical"):
        raise ValueError("morphology must be 'typical' or 'atypical'")
    if httkv_ml_per_m is not None and (tkv_ml is not None or height_m is not None):
        raise ValueError("Specify htTKV OR both TKV and height, not both")
    if httkv_ml_per_m is None:
        if tkv_ml is None or height_m is None:
            raise ValueError("Supply httkv_ml_per_m or both tkv_ml and height_m")
        volume = _positive_number(tkv_ml, "tkv_ml")
        height = _positive_number(height_m, "height_m")
        httkv = volume / height
    else:
        httkv = _positive_number(httkv_ml_per_m, "httkv_ml_per_m")
    if not math.isfinite(httkv) or httkv <= 0:
        raise ValueError("Calculated htTKV must be finite and positive")

    output = {
        "age_years": years,
        "ht_tkv_ml_per_m": round(httkv, 3),
        "morphology": morph,
        "mayo_class": None,
        "estimated_annual_growth_percent": None,
        "interpretation": "MIC 1A–1E cannot be applied to atypical (class 2) morphology.",
    }
    if morph == "atypical":
        return output

    # HtTKV = 150 × (1 + growth_fraction) ** age.
    growth = 100.0 * math.expm1(math.log(httkv / STARTING_HTTKV) / years)
    mic = next((name for limit, name in BOUNDARIES if growth < limit), "1E")
    output.update({
        "mayo_class": mic,
        "estimated_annual_growth_percent": round(growth, 4),
        "interpretation": (
            "Imaging prognostic stratum only; not an individual eGFR prediction "
            "or stand-alone treatment recommendation."
        ),
    })
    return output


def process_batch(input_csv, output_csv):
    """Evaluate a CSV atomically. All rows must be valid; no partial export."""
    source, destination = Path(input_csv), Path(output_csv)
    if not source.is_file():
        raise FileNotFoundError(f"Input CSV file not found: {source}")
    if not destination.parent.is_dir():
        raise FileNotFoundError(f"Output directory does not exist: {destination.parent}")
    if source.resolve() == destination.resolve():
        raise ValueError("Input and output CSV paths must differ")
    with source.open("r", newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        fields = reader.fieldnames
        if not fields:
            raise ValueError("Input CSV file is empty or has no headers")
        if len(set(fields)) != len(fields):
            raise ValueError("Duplicate CSV column headers")
        if "age" not in fields:
            raise ValueError("Missing required CSV column: age")
        extra = ["mayo_class", "ht_tkv_ml_per_m", "estimated_annual_growth_percent",
                 "interpretation"]
        if any(col in fields for col in extra):
            raise ValueError("Input CSV contains reserved output columns")
        rows = []
        for line, row in enumerate(reader, 2):
            if None in row:
                raise ValueError(f"CSV row {line}: too many fields")
            try:
                result = calculate_metrics(
                    age=row["age"],
                    tkv_ml=row.get("tkv_ml") or None,
                    height_m=row.get("height_m") or None,
                    httkv_ml_per_m=row.get("httkv_ml_per_m") or None,
                    morphology=row.get("morphology") or "typical",
                )
            except ValueError as exc:
                raise ValueError(f"CSV row {line}: {exc}") from exc
            rows.append({**row, **{k: result[k] for k in extra}})
    with destination.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields + extra)
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Mayo ADPKD imaging classification (research/education only)")
    commands = parser.add_subparsers(dest="command", required=True)
    single = commands.add_parser("single", help="Classify one imaging measurement")
    single.add_argument("--age", type=float, required=True, help="Age, 15–80 years")
    single.add_argument("--tkv-ml", type=float, help="Total kidney volume in mL")
    single.add_argument("--height-m", type=float, help="Height in meters")
    single.add_argument("--httkv-ml-per-m", type=float, help="Height-adjusted TKV, mL/m")
    single.add_argument("--morphology", choices=["typical", "atypical"],
                        default="typical")
    batch = commands.add_parser("batch", help="Classify CSV rows")
    batch.add_argument("-i", "--input", required=True)
    batch.add_argument("-o", "--output", default="results.csv")
    args = parser.parse_args(argv)
    try:
        if args.command == "single":
            result = calculate_metrics(
                age=args.age, tkv_ml=args.tkv_ml, height_m=args.height_m,
                httkv_ml_per_m=args.httkv_ml_per_m, morphology=args.morphology)
            print(json.dumps(result, indent=2))
        else:
            count = process_batch(args.input, args.output)
            print(f"Processed {count} records -> {args.output}")
    except (ValueError, FileNotFoundError, OSError) as exc:
        parser.exit(2, f"error: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
