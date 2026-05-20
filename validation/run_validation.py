import json
import pathlib

import numpy as np

from homogeneity_analyser.analyzers import HomogeneityAnalyzer

ROOT = pathlib.Path(__file__).resolve().parent
ANNOT = ROOT / "annotated"
FIXTURES = ROOT / "fixtures_musicxml"


def load_series(name: str):
    data = np.genfromtxt(ANNOT / name, delimiter=",", skip_header=1)
    t = data[:, 0].tolist()
    H = data[:, 1].tolist()
    return {"t": t, "H": H}


def load_expected(name: str):
    return json.loads((ANNOT / name).read_text(encoding="utf-8"))


def eval_change_points(pred, expected, tol):
    remaining = set(pred)
    matched = 0
    for e in expected:
        hit = None
        for p in list(remaining):
            if abs(p - e) <= tol:
                hit = p
                break
        if hit is not None:
            matched += 1
            remaining.remove(hit)
    precision = matched / max(len(pred), 1)
    recall = matched / max(len(expected), 1)
    return precision, recall, matched


def run():
    series = load_series("series_step.csv")
    expected = load_expected("series_step_expected.json")

    analyzer = HomogeneityAnalyzer.__new__(HomogeneityAnalyzer)
    pred = HomogeneityAnalyzer.segment_homogeneity_pelt(analyzer, series, penalty=0.05, min_size=2)

    prec, rec, matched = eval_change_points(pred, expected["change_points"], expected["tolerance"])
    report = (
        f"Detected: {pred}\n"
        f"Expected: {expected['change_points']}\n"
        f"Matched: {matched}\n"
        f"Precision: {prec:.3f}\n"
        f"Recall: {rec:.3f}\n"
    )
    print("Synthetic series validation")
    print(report)

    xml = FIXTURES / "step_density.xml"
    exp = json.loads((FIXTURES / "step_density_expected.json").read_text(encoding="utf-8"))
    analyzer = HomogeneityAnalyzer(
        score_path=str(xml),
        time_step=float(exp["time_step"]),
        pitch_space="absolute",
    )
    results = analyzer.analyze_score(window_size=float(exp["window_size"]), sigma=float(exp["sigma"]))
    cp_idx = analyzer.segment_homogeneity_pelt(results, penalty=float(exp["penalty"]), min_size=int(exp["min_size"]))
    cp_times = [results["t"][i] for i in cp_idx]
    tol = float(exp["tolerance"])
    prec, rec, matched = eval_change_points(cp_times, exp["change_times"], tol)
    xml_report = (
        f"Detected: {cp_times}\n"
        f"Expected: {exp['change_times']}\n"
        f"Matched: {matched}\n"
        f"Precision: {prec:.3f}\n"
        f"Recall: {rec:.3f}\n"
    )
    print("MusicXML fixture validation")
    print(xml_report)


if __name__ == "__main__":
    run()
