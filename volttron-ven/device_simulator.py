
# Device simulator logic for VEN agent

import threading
import random
from collections import deque
from typing import Any, Deque

# Metering configuration knobs (tunable at runtime)
meter_base_min_kw: float = 0.5
meter_base_max_kw: float = 2.0
meter_jitter_pct: float = 0.05  # ±5% around target when set

voltage_enabled: bool = False
voltage_nominal: float = 120.0
voltage_jitter_pct: float = 0.02  # ±2%

current_enabled: bool = False
power_factor: float = 1.0  # 0 < pf <= 1

# latest metering snapshot for UI/live endpoint
last_metering_sample: dict[str, Any] | None = None

# Simple circuit model (placeholder)
circuits: list[dict[str, Any]] = [
	{"id": "hvac1",    "name": "HVAC",       "type": "hvac",    "enabled": True,  "connected": True, "rated_kw": 3.5, "current_kw": 0.0, "critical": True,  "mode": "dynamic", "fixed_kw": 0.0},
	{"id": "heater1",  "name": "Heater",     "type": "heater",  "enabled": True,  "connected": True, "rated_kw": 1.5, "current_kw": 0.0, "critical": False, "mode": "dynamic", "fixed_kw": 0.0},
	{"id": "ev1",      "name": "EV Charger", "type": "ev",      "enabled": False, "connected": True, "rated_kw": 7.2, "current_kw": 0.0, "critical": False, "mode": "dynamic", "fixed_kw": 0.0},
	{"id": "batt1",    "name": "Battery",    "type": "battery", "enabled": False, "connected": True, "rated_kw": 5.0, "current_kw": 0.0, "critical": False, "mode": "dynamic", "fixed_kw": 0.0},
	{"id": "pv1",      "name": "Solar PV",   "type": "pv",      "enabled": False, "connected": True, "rated_kw": 6.0, "current_kw": 0.0, "critical": False, "mode": "dynamic", "fixed_kw": 0.0},
	{"id": "lights1",  "name": "Lights",     "type": "lights",  "enabled": True,  "connected": True, "rated_kw": 0.4, "current_kw": 0.0, "critical": False, "mode": "dynamic", "fixed_kw": 0.0},
	{"id": "fridge1",  "name": "Fridge",     "type": "fridge",  "enabled": True,  "connected": True, "rated_kw": 0.2, "current_kw": 0.0, "critical": True,  "mode": "dynamic", "fixed_kw": 0.0},
	{"id": "misc1",    "name": "House",      "type": "misc",    "enabled": True,  "connected": True, "rated_kw": 1.0, "current_kw": 0.0, "critical": False, "mode": "dynamic", "fixed_kw": 0.0},
]

circuit_priority: dict[str, int] = {"hvac": 1, "misc": 1, "heater": 2, "ev": 3, "battery": 2, "pv": 0}

load_limits: dict[str, dict[str, float]] = {}
panel_temp_target_kw: float | None = None
panel_temp_until_ts: int | None = None

circuit_model_enabled: bool = True
battery_capacity_kwh: float = 13.5
battery_soc: float = 0.5  # 0..1

power_history: Deque[tuple[int, float]] = deque(maxlen=360)
active_event: dict[str, Any] | None = None

def circuits_snapshot() -> list[dict[str, Any]]:
	"""Return a snapshot of all circuits with current state and shed capability."""
	return [dict(c) for c in circuits]

def shed_capability_for(c: dict[str, Any]) -> float:
	"""Estimate shed capability for a circuit based on type and state."""
	try:
		typ = c.get("type")
		kw = float(c.get("current_kw", 0.0))
		rated = float(c.get("rated_kw", 0.0))
		crit = bool(c.get("critical", False))
		if not c.get("enabled", True):
			return 0.0
		crit_floor_factor = 0.8 if crit else None
		if typ == "hvac":
			floor = (crit_floor_factor or 0.2) * rated
			return round(max(0.0, kw - floor), 2)
		if typ == "heater":
			return round(kw, 2)
		if typ == "ev":
			return round(kw, 2)
		if typ == "misc":
			floor = (crit_floor_factor or 0.3) * rated
			return round(max(0.0, kw - floor), 2)
		if typ == "pv":
			return 0.0
		if typ == "battery":
			return round(rated, 2)
		if typ in ("lights", "fridge"):
			floor = (crit_floor_factor or 0.5) * rated
			return round(max(0.0, kw - floor), 2)
	except Exception:
		return 0.0
	return 0.0

def distribute_power_to_circuits(total_kw: float) -> list[dict[str, Any]]:
	"""Distribute total power among enabled circuits by rated_kw proportion."""
	enabled = [c for c in circuits if c.get("enabled", True) and c.get("rated_kw", 0.0) > 0]
	if not enabled or total_kw <= 0:
		for c in circuits:
			c["current_kw"] = 0.0
		return circuits_snapshot()
	weight_sum = sum(float(c.get("rated_kw", 0.0)) for c in enabled)
	for c in enabled:
		share = float(c.get("rated_kw", 0.0)) / weight_sum if weight_sum > 0 else 0.0
		c["current_kw"] = round(max(0.0, total_kw * share), 2)
	for c in circuits:
		if c not in enabled:
			c["current_kw"] = 0.0
	return circuits_snapshot()

def pv_curve_factor(ts_utc: int) -> float:
	"""Simulate a diurnal PV output curve (bell-shaped, peaks at midday)."""
	hour = (ts_utc // 3600) % 24
	local_hour = (hour - 8) % 24
	x = (local_hour - 12) / 6.0
	import math
	val = math.exp(-x * x)
	return float(max(0.0, min(1.0, val)))

def compute_panel_step(now_ts: int) -> dict[str, Any]:
	"""Compute per-circuit kW and aggregate net power for this step."""
	global battery_soc
	if not circuit_model_enabled:
		total = next_power_reading()
		circuits_snap = distribute_power_to_circuits(total)
		return {"power_kw": total, "circuits": circuits_snap, "battery_soc": battery_soc}
	# Gather references
	target = None
	batt = next((c for c in circuits if c["type"] == "battery"), None)
	pv = next((c for c in circuits if c["type"] == "pv"), None)
	ev = next((c for c in circuits if c["type"] == "ev"), None)
	hvac = next((c for c in circuits if c["type"] == "hvac"), None)
	heater = next((c for c in circuits if c["type"] == "heater"), None)
	house = next((c for c in circuits if c["type"] == "misc"), None)
	lights = next((c for c in circuits if c["type"] == "lights"), None)
	fridge = next((c for c in circuits if c["type"] == "fridge"), None)
	# Base: zero out current_kw
	for c in circuits:
		c["current_kw"] = 0.0
	# House load (misc): between base min/max with jitter
	base_low, base_high = meter_base_min_kw, max(meter_base_min_kw, meter_base_max_kw)
	house_kw = 0.0
	if house and house.get("connected", True):
		dyn = round(random.uniform(base_low, base_high), 2)
		house_kw = dyn
		house_kw = min(house_kw, house_kw)
		house["current_kw"] = house_kw
	# HVAC: duty between 0.2..0.8 of rated
	hvac_kw = 0.0
	if hvac and hvac.get("connected", True):
		duty = max(0.0, min(1.0, 0.5 + random.uniform(-0.3, 0.3)))
		hvac_kw = round(hvac.get("rated_kw", 0.0) * duty, 2)
		hvac_kw = min(hvac_kw, hvac_kw)
		hvac["current_kw"] = hvac_kw
	# Heater: bursty low duty 0..0.5
	heater_kw = 0.0
	if heater and heater.get("connected", True):
		duty = max(0.0, min(0.5, random.uniform(0.0, 0.5)))
		heater_kw = round(heater.get("rated_kw", 0.0) * duty, 2)
		heater_kw = min(heater_kw, heater_kw)
		heater["current_kw"] = heater_kw
	# EV: simple on/off at rated when enabled
	ev_kw = 0.0
	if ev and ev.get("connected", True):
		ev_kw = round(ev.get("rated_kw", 0.0), 2)
		ev_kw = min(ev_kw, ev_kw)
		ev["current_kw"] = ev_kw
	# Lights: modest variable draw up to rated
	if lights and lights.get("connected", True):
		lk = round(max(0.0, min(lights.get("rated_kw", 0.0), random.uniform(0.05, lights.get("rated_kw", 0.0)))), 2)
		lk = min(lk, lk)
		lights["current_kw"] = lk
	else:
		lk = 0.0
	# Fridge: quasi-constant duty with small jitter
	if fridge and fridge.get("connected", True):
		fk = round(max(0.0, min(fridge.get("rated_kw", 0.0), 0.5 * fridge.get("rated_kw", 0.0) + random.uniform(-0.02, 0.02))), 2)
		fk = min(fk, fk)
		fridge["current_kw"] = fk
	else:
		fk = 0.0
	# PV generation: rated * curve factor
	pv_gen = 0.0
	if pv and pv.get("connected", True) and pv.get("enabled", False):
		pv_gen = round(pv.get("rated_kw", 0.0) * pv_curve_factor(now_ts), 2)
		pv["current_kw"] = -pv_gen
	# Pre-battery net load
	load_kw = house_kw + hvac_kw + heater_kw + ev_kw + lk + fk
	net_kw_before_batt = max(0.0, load_kw - pv_gen)
	# Battery action: attempt to move net toward effective target
	batt_flow = 0.0
	if batt and batt.get("enabled", False):
		batt_max = float(batt.get("rated_kw", 0.0))
		batt_flow = 0.0
		step_h = max(1.0, 60) / 3600.0
		energy_delta_kwh = batt_flow * step_h
		battery_soc = max(0.0, min(1.0, battery_soc + (energy_delta_kwh / max(0.1, battery_capacity_kwh))))
		if batt_flow > 0 and battery_soc <= 0.01:
			batt_flow = 0.0
		if batt_flow < 0 and battery_soc >= 0.99:
			batt_flow = 0.0
		batt["current_kw"] = -batt_flow
	power_kw = round(max(0.0, net_kw_before_batt - max(0.0, batt_flow)), 2)
	return {"power_kw": power_kw, "circuits": circuits_snapshot(), "battery_soc": battery_soc}

def next_power_reading() -> float:
	"""Simulate next power reading based on config and target."""
	low, high = meter_base_min_kw, meter_base_max_kw
	if high < low:
		high = low
	return round(random.uniform(low, high), 2)

