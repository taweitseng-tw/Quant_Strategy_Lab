"""Service layer for Instrument Profile operations — Task 009B."""

from __future__ import annotations

import json
from pathlib import Path
from core.models.instrument import InstrumentProfile


DEFAULT_PROFILES = [
    InstrumentProfile(
        symbol="ES",
        name="E-mini S&P 500",
        market="Futures",
        tick_size=0.25,
        point_value=50.0,
        commission_value=2.0,
        slippage_ticks=1.0,
        currency="USD",
        session_template="US_Index_Futures"
    ),
    InstrumentProfile(
        symbol="NQ",
        name="E-mini Nasdaq 100",
        market="Futures",
        tick_size=0.25,
        point_value=20.0,
        commission_value=2.0,
        slippage_ticks=1.0,
        currency="USD",
        session_template="US_Index_Futures"
    ),
    InstrumentProfile(
        symbol="GC",
        name="Gold Futures",
        market="Futures",
        tick_size=0.1,
        point_value=100.0,
        commission_value=2.0,
        slippage_ticks=1.0,
        currency="USD",
        session_template="US_Metal_Futures"
    )
]


class InstrumentService:
    """Service to handle loading, saving, and active selection of InstrumentProfiles.

    If a project path is provided, reads/writes to `config/instruments.json`.
    If no project path is active, falls back to clearly-labeled in-memory mock data.
    """

    def __init__(self, project_path: Path | str | None = None) -> None:
        self.project_path: Path | None = None
        self._profiles: list[InstrumentProfile] = []
        self._active_symbol: str | None = None
        
        if project_path:
            self.set_project_path(project_path)
        else:
            self.load_profiles()

    def set_project_path(self, path: Path | str | None) -> None:
        """Set the current project path and reload profiles from disk."""
        self.project_path = Path(path).resolve() if path else None
        self.load_profiles()

    def load_profiles(self) -> None:
        """Load profiles from project's instruments.json or use mock data."""
        self._profiles = []
        
        if self.project_path:
            config_file = self.project_path / "config" / "instruments.json"
            if config_file.is_file():
                try:
                    with open(config_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    
                    if isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and "symbol" in item:
                                self._profiles.append(self._dict_to_profile(item))
                    
                    if not self._profiles:
                        # If file was empty list or invalid, populate defaults
                        self._profiles = list(DEFAULT_PROFILES)
                        self._save_to_disk()
                except Exception:
                    # Fallback on parse failure
                    self._profiles = list(DEFAULT_PROFILES)
                    self._save_to_disk()
            else:
                # File does not exist, initialize with default profiles
                self._profiles = list(DEFAULT_PROFILES)
                try:
                    self._save_to_disk()
                except Exception:
                    pass
        else:
            # Load default in-memory profiles
            self._profiles = list(DEFAULT_PROFILES)

        # Retain or set active symbol
        if self._profiles:
            if not self._active_symbol or not any(p.symbol == self._active_symbol for p in self._profiles):
                self._active_symbol = self._profiles[0].symbol
        else:
            self._active_symbol = None

    def get_profiles(self) -> list[InstrumentProfile]:
        """Return the current list of profiles."""
        return self._profiles

    def get_active_profile(self) -> InstrumentProfile | None:
        """Return the currently selected active profile."""
        if not self._active_symbol:
            return None
        for p in self._profiles:
            if p.symbol == self._active_symbol:
                return p
        return None

    def set_active_profile(self, symbol: str | None) -> None:
        """Set the active profile by symbol."""
        if not symbol:
            self._active_symbol = None
            return
        
        if any(p.symbol == symbol for p in self._profiles):
            self._active_symbol = symbol

    def save_profile(self, profile: InstrumentProfile) -> None:
        """Save/update a profile. Writes to disk if project is active."""
        if not profile.symbol or not profile.symbol.strip():
            raise ValueError("Profile symbol cannot be empty.")
            
        profile.symbol = profile.symbol.strip()
        
        # Check if it already exists
        existing_idx = -1
        for i, p in enumerate(self._profiles):
            if p.symbol == profile.symbol:
                existing_idx = i
                break
                
        if existing_idx >= 0:
            self._profiles[existing_idx] = profile
        else:
            self._profiles.append(profile)
            
        # Ensure there is an active symbol
        if not self._active_symbol:
            self._active_symbol = profile.symbol
            
        if self.project_path:
            self._save_to_disk()

    def delete_profile(self, symbol: str) -> None:
        """Delete a profile by symbol. Writes to disk if project is active."""
        self._profiles = [p for p in self._profiles if p.symbol != symbol]
        
        if self._active_symbol == symbol:
            if self._profiles:
                self._active_symbol = self._profiles[0].symbol
            else:
                self._active_symbol = None
                
        if self.project_path:
            self._save_to_disk()

    def is_mock_data(self) -> bool:
        """Return True if no active project is open (working in memory)."""
        return self.project_path is None

    def _save_to_disk(self) -> None:
        """Serialize and write profiles to project's config/instruments.json."""
        if not self.project_path:
            return
            
        config_file = self.project_path / "config" / "instruments.json"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        serialized = [self._profile_to_dict(p) for p in self._profiles]
        
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(serialized, f, indent=2)

    @staticmethod
    def _profile_to_dict(profile: InstrumentProfile) -> dict:
        return {
            "symbol": profile.symbol,
            "name": profile.name,
            "market": profile.market,
            "tick_size": profile.tick_size,
            "point_value": profile.point_value,
            "commission_value": profile.commission_value,
            "slippage_ticks": profile.slippage_ticks,
            "currency": profile.currency,
            "session_template": profile.session_template,
        }

    @staticmethod
    def _dict_to_profile(d: dict) -> InstrumentProfile:
        return InstrumentProfile(
            symbol=d["symbol"],
            name=d.get("name", ""),
            market=d.get("market", ""),
            tick_size=float(d.get("tick_size", 1.0)),
            point_value=float(d.get("point_value", 1.0)),
            commission_value=float(d.get("commission_value", 0.0)),
            slippage_ticks=float(d.get("slippage_ticks", 0.0)),
            currency=d.get("currency", "USD"),
            session_template=d.get("session_template", ""),
        )
