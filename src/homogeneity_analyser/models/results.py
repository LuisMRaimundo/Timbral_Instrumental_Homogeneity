"""Typed result containers (mirror legacy dict shapes for services and tests)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class HomogeneitySeriesResult:
    """Time series for H(t) with optional m1–m3 breakdown."""

    t: list[float]
    H: list[float]
    m1: list[float] = field(default_factory=list)
    m2: list[float] = field(default_factory=list)
    m3: list[float] = field(default_factory=list)

    @classmethod
    def from_legacy(cls, d: dict[str, Any]) -> HomogeneitySeriesResult:
        t, H = d["t"], d["H"]
        if len(H) != len(t):
            raise ValueError("H length must match t")
        m1, m2, m3 = d.get("m1", []), d.get("m2", []), d.get("m3", [])
        if (m1 or m2 or m3) and not (len(m1) == len(t) and len(m2) == len(t) and len(m3) == len(t)):
            raise ValueError("m1, m2, m3 must match t length when provided")
        return cls(t=list(t), H=list(H), m1=list(m1), m2=list(m2), m3=list(m3))

    def as_legacy_dict(self) -> dict[str, list[float]]:
        out: dict[str, list[float]] = {"t": self.t, "H": self.H}
        if len(self.m1) == len(self.t):
            out["m1"] = self.m1
            out["m2"] = self.m2
            out["m3"] = self.m3
        return out


@dataclass
class TimbralSeriesResult:
    t: list[float]
    H_timbral: list[float]
    timbral_state_distribution: list[dict[str, float] | None] = field(default_factory=list)
    dominant_timbral_state: list[str | None] = field(default_factory=list)
    timbral_state_concentration: list[float] = field(default_factory=list)
    h_timbral_diagnostics: list[dict[str, Any] | None] = field(default_factory=list)

    @classmethod
    def from_legacy(cls, d: dict[str, Any]) -> TimbralSeriesResult:
        t = list(d["t"])
        h = list(d["H_timbral"])
        if len(h) != len(t):
            raise ValueError("t and H_timbral length mismatch")
        n = len(t)

        def _coerce_list(key: str, default: Any) -> list[Any]:
            v = d.get(key)
            if v is None:
                return [default] * n
            v = list(v)
            if len(v) != n:
                return [default] * n
            return v

        diag_raw = d.get("H_timbral_diagnostics")
        diag_list: list[dict[str, Any] | None]
        if isinstance(diag_raw, list) and len(diag_raw) == n:
            diag_list = [dict(x) if isinstance(x, dict) else None for x in diag_raw]
        else:
            diag_list = []

        return cls(
            t=t,
            H_timbral=h,
            timbral_state_distribution=_coerce_list("timbral_state_distribution", {}),
            dominant_timbral_state=_coerce_list("dominant_timbral_state", None),
            timbral_state_concentration=_coerce_list("timbral_state_concentration", 1.0),
            h_timbral_diagnostics=diag_list,
        )

    def as_legacy_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {"t": self.t, "H_timbral": self.H_timbral}
        if len(self.timbral_state_distribution) == len(self.t):
            out["timbral_state_distribution"] = list(self.timbral_state_distribution)
            out["dominant_timbral_state"] = list(self.dominant_timbral_state)
            out["timbral_state_concentration"] = list(self.timbral_state_concentration)
        if len(self.h_timbral_diagnostics) == len(self.t):
            out["H_timbral_diagnostics"] = list(self.h_timbral_diagnostics)
        return out


@dataclass
class RegisterSeriesResult:
    t: list[float]
    U: list[float]

    @classmethod
    def from_legacy(cls, d: dict[str, Any]) -> RegisterSeriesResult:
        if len(d["t"]) != len(d["U"]):
            raise ValueError("t and U length mismatch")
        return cls(t=list(d["t"]), U=list(d["U"]))

    def as_legacy_dict(self) -> dict[str, list[float]]:
        return {"t": self.t, "U": self.U}


@dataclass
class OrchestrationSymbolicSeriesResult:
    """Time series for neutral symbolic orchestration ``H_orchestration_symbolic``."""

    t: list[float]
    H_orchestration_symbolic: list[float]
    h_orchestration_symbolic_diagnostics: list[dict[str, Any] | None] = field(default_factory=list)

    @classmethod
    def from_legacy(cls, d: dict[str, Any]) -> OrchestrationSymbolicSeriesResult:
        t = list(d["t"])
        h = list(d["H_orchestration_symbolic"])
        if len(h) != len(t):
            raise ValueError("t and H_orchestration_symbolic length mismatch")
        n = len(t)
        diag_raw = d.get("H_orchestration_symbolic_diagnostics")
        diag_list: list[dict[str, Any] | None]
        if isinstance(diag_raw, list) and len(diag_raw) == n:
            diag_list = [dict(x) if isinstance(x, dict) else None for x in diag_raw]
        else:
            diag_list = []
        return cls(t=t, H_orchestration_symbolic=h, h_orchestration_symbolic_diagnostics=diag_list)

    def as_legacy_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {"t": self.t, "H_orchestration_symbolic": self.H_orchestration_symbolic}
        if len(self.h_orchestration_symbolic_diagnostics) == len(self.t):
            out["H_orchestration_symbolic_diagnostics"] = list(self.h_orchestration_symbolic_diagnostics)
        return out


@dataclass
class NotatedFusionPotentialSeriesResult:
    """Time series for notation-derived ``H_notated_fusion_potential`` and optional dynamic-adjusted series."""

    t: list[float]
    H_notated_fusion_potential: list[float]
    h_notated_fusion_potential_diagnostics: list[dict[str, Any] | None] = field(default_factory=list)
    H_notated_fusion_potential_dynamic: list[float] = field(default_factory=list)

    @classmethod
    def from_legacy(cls, d: dict[str, Any]) -> NotatedFusionPotentialSeriesResult:
        t = list(d["t"])
        h = list(d["H_notated_fusion_potential"])
        if len(h) != len(t):
            raise ValueError("t and H_notated_fusion_potential length mismatch")
        n = len(t)
        diag_raw = d.get("H_notated_fusion_potential_diagnostics")
        diag_list: list[dict[str, Any] | None]
        if isinstance(diag_raw, list) and len(diag_raw) == n:
            diag_list = [dict(x) if isinstance(x, dict) else None for x in diag_raw]
        else:
            diag_list = []
        raw_dyn = d.get("H_notated_fusion_potential_dynamic")
        if isinstance(raw_dyn, list) and len(raw_dyn) == n:
            h_dyn = [float(x) for x in raw_dyn]
        else:
            h_dyn = []
            for i in range(n):
                di = diag_list[i] if i < len(diag_list) else None
                if isinstance(di, dict) and "H_notated_fusion_potential_dynamic" in di:
                    h_dyn.append(float(di["H_notated_fusion_potential_dynamic"]))
                else:
                    h_dyn.append(float(h[i]))
        return cls(
            t=t,
            H_notated_fusion_potential=h,
            h_notated_fusion_potential_diagnostics=diag_list,
            H_notated_fusion_potential_dynamic=h_dyn,
        )

    def as_legacy_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {"t": self.t, "H_notated_fusion_potential": self.H_notated_fusion_potential}
        if len(self.h_notated_fusion_potential_diagnostics) == len(self.t):
            out["H_notated_fusion_potential_diagnostics"] = list(self.h_notated_fusion_potential_diagnostics)
        if len(self.H_notated_fusion_potential_dynamic) == len(self.t):
            out["H_notated_fusion_potential_dynamic"] = list(self.H_notated_fusion_potential_dynamic)
        return out


@dataclass
class FusionAcousticHeuristicSeriesResult:
    """Time series for acoustic-informed fusion heuristic ``H_fusion_acoustic_heuristic``."""

    t: list[float]
    H_fusion_acoustic_heuristic: list[float]
    h_fusion_acoustic_heuristic_diagnostics: list[dict[str, Any] | None] = field(default_factory=list)
    fusion_model_header: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_legacy(cls, d: dict[str, Any]) -> FusionAcousticHeuristicSeriesResult:
        t = list(d["t"])
        h = list(d["H_fusion_acoustic_heuristic"])
        if len(h) != len(t):
            raise ValueError("t and H_fusion_acoustic_heuristic length mismatch")
        n = len(t)
        diag_raw = d.get("H_fusion_acoustic_heuristic_diagnostics")
        diag_list: list[dict[str, Any] | None]
        if isinstance(diag_raw, list) and len(diag_raw) == n:
            diag_list = [dict(x) if isinstance(x, dict) else None for x in diag_raw]
        else:
            diag_list = []
        hdr_raw = d.get("fusion_model_header")
        fusion_header: dict[str, Any] = dict(hdr_raw) if isinstance(hdr_raw, dict) else {}
        return cls(
            t=t,
            H_fusion_acoustic_heuristic=h,
            h_fusion_acoustic_heuristic_diagnostics=diag_list,
            fusion_model_header=fusion_header,
        )

    def as_legacy_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "t": self.t,
            "H_fusion_acoustic_heuristic": self.H_fusion_acoustic_heuristic,
            "fusion_model_header": dict(self.fusion_model_header),
        }
        if len(self.h_fusion_acoustic_heuristic_diagnostics) == len(self.t):
            out["H_fusion_acoustic_heuristic_diagnostics"] = list(self.h_fusion_acoustic_heuristic_diagnostics)
        return out


@dataclass
class ClusterSeriesResult:
    """Time series for vertical cluster compactness ``H_cluster`` with optional per-window diagnostics."""

    t: list[float]
    H_cluster: list[float]
    h_cluster_diagnostics: list[dict[str, Any] | None] = field(default_factory=list)

    @classmethod
    def from_legacy(cls, d: dict[str, Any]) -> ClusterSeriesResult:
        t = list(d["t"])
        h = list(d["H_cluster"])
        if len(h) != len(t):
            raise ValueError("t and H_cluster length mismatch")
        n = len(t)
        diag_raw = d.get("H_cluster_diagnostics")
        diag_list: list[dict[str, Any] | None]
        if isinstance(diag_raw, list) and len(diag_raw) == n:
            diag_list = [dict(x) if isinstance(x, dict) else None for x in diag_raw]
        else:
            diag_list = []
        return cls(t=t, H_cluster=h, h_cluster_diagnostics=diag_list)

    def as_legacy_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {"t": self.t, "H_cluster": self.H_cluster}
        if len(self.h_cluster_diagnostics) == len(self.t):
            out["H_cluster_diagnostics"] = list(self.h_cluster_diagnostics)
        return out
