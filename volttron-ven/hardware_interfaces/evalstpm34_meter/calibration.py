"""
Calibration Manager for EVALSTPM34 Meters

Handles calibration data storage, retrieval, and calibration procedures
for EVALSTPM34 power meters during end-of-line (EOL) testing and
field calibration.
"""

import logging
import json
import os
from datetime import datetime
from typing import Dict, Optional, List, Tuple
from pathlib import Path

from .exceptions import CalibrationError
from .data_types import CalibrationData, MeterConfig, MeterReading


class CalibrationManager:
    """
    Manages calibration data and procedures for EVALSTPM34 meters.
    
    Features:
    - Store/retrieve calibration data
    - Perform EOL calibration procedures
    - Validate calibration accuracy
    - Export/import calibration data
    """
    
    def __init__(self, calibration_data_dir: str = "/var/lib/grid-services/calibration"):
        """
        Initialize calibration manager.
        
        Args:
            calibration_data_dir: Directory to store calibration files
        """
        self.logger = logging.getLogger(__name__)
        self.calibration_data_dir = Path(calibration_data_dir)
        self.calibration_data_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory cache of calibration data
        self._calibration_cache: Dict[str, CalibrationData] = {}
        
        # Load existing calibration data
        self._load_calibration_data()
    
    def _load_calibration_data(self):
        """Load all calibration data files from disk."""
        try:
            for cal_file in self.calibration_data_dir.glob("*.json"):
                meter_id = cal_file.stem
                try:
                    with open(cal_file, 'r') as f:
                        cal_dict = json.load(f)
                    
                    calibration = CalibrationData(
                        meter_id=cal_dict["meter_id"],
                        calibration_date=datetime.fromisoformat(cal_dict["calibration_date"]),
                        voltage_gain_ch1=cal_dict["voltage_calibration"]["ch1_gain"],
                        voltage_offset_ch1=cal_dict["voltage_calibration"]["ch1_offset"],
                        voltage_gain_ch2=cal_dict["voltage_calibration"]["ch2_gain"],
                        voltage_offset_ch2=cal_dict["voltage_calibration"]["ch2_offset"],
                        current_gain_ch1=cal_dict["current_calibration"]["ch1_gain"],
                        current_offset_ch1=cal_dict["current_calibration"]["ch1_offset"],
                        current_gain_ch2=cal_dict["current_calibration"]["ch2_gain"],
                        current_offset_ch2=cal_dict["current_calibration"]["ch2_offset"],
                        power_gain_ch1=cal_dict["power_calibration"]["ch1_gain"],
                        power_offset_ch1=cal_dict["power_calibration"]["ch1_offset"],
                        power_gain_ch2=cal_dict["power_calibration"]["ch2_gain"],
                        power_offset_ch2=cal_dict["power_calibration"]["ch2_offset"],
                        phase_compensation_ch1=cal_dict["phase_calibration"]["ch1_compensation"],
                        phase_compensation_ch2=cal_dict["phase_calibration"]["ch2_compensation"],
                        reference_voltage=cal_dict["reference_values"]["voltage"],
                        reference_current=cal_dict["reference_values"]["current"],
                        reference_frequency=cal_dict["reference_values"]["frequency"],
                        calibrated_by=cal_dict["metadata"]["calibrated_by"],
                        calibration_notes=cal_dict["metadata"].get("notes", ""),
                    )
                    
                    self._calibration_cache[meter_id] = calibration
                    self.logger.info(f"Loaded calibration data for meter {meter_id}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to load calibration file {cal_file}: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error loading calibration data: {e}")
    
    def get_calibration(self, meter_id: str) -> Optional[CalibrationData]:
        """
        Get calibration data for a meter.
        
        Args:
            meter_id: Meter identifier
            
        Returns:
            CalibrationData if available, None otherwise
        """
        return self._calibration_cache.get(meter_id)
    
    def save_calibration(self, calibration: CalibrationData) -> bool:
        """
        Save calibration data for a meter.
        
        Args:
            calibration: Calibration data to save
            
        Returns:
            True if successful
            
        Raises:
            CalibrationError: If save operation fails
        """
        try:
            cal_file = self.calibration_data_dir / f"{calibration.meter_id}.json"
            
            with open(cal_file, 'w') as f:
                json.dump(calibration.to_dict(), f, indent=2)
            
            # Update cache
            self._calibration_cache[calibration.meter_id] = calibration
            
            self.logger.info(f"Saved calibration data for meter {calibration.meter_id}")
            return True
            
        except Exception as e:
            raise CalibrationError(f"Failed to save calibration data: {e}")
    
    def perform_eol_calibration(self, meter, reference_voltage: float, 
                               reference_current: float, calibrated_by: str,
                               notes: str = "") -> CalibrationData:
        """
        Perform end-of-line calibration procedure.
        
        Args:
            meter: EVALSTPM34Meter instance
            reference_voltage: Reference voltage for calibration
            reference_current: Reference current for calibration
            calibrated_by: Person/system performing calibration
            notes: Optional calibration notes
            
        Returns:
            CalibrationData with calculated coefficients
            
        Raises:
            CalibrationError: If calibration procedure fails
        """
        try:
            self.logger.info(f"Starting EOL calibration for meter {meter.config.meter_id}")
            
            # Step 1: Take baseline readings
            baseline_readings = []
            for i in range(10):  # Take multiple samples
                reading = meter.read_instantaneous_values()
                baseline_readings.append(reading)
                time.sleep(0.1)
            
            # Step 2: Calculate average measurements
            avg_voltage_ch1 = sum(r.voltage_ch1 for r in baseline_readings) / len(baseline_readings)
            avg_current_ch1 = sum(r.current_ch1 for r in baseline_readings) / len(baseline_readings)
            avg_voltage_ch2 = sum(r.voltage_ch2 for r in baseline_readings) / len(baseline_readings)
            avg_current_ch2 = sum(r.current_ch2 for r in baseline_readings) / len(baseline_readings)
            
            # Step 3: Calculate calibration coefficients
            # Voltage calibration
            voltage_gain_ch1 = reference_voltage / avg_voltage_ch1 if avg_voltage_ch1 != 0 else 1.0
            voltage_gain_ch2 = reference_voltage / avg_voltage_ch2 if avg_voltage_ch2 != 0 else 1.0
            
            # Current calibration
            current_gain_ch1 = reference_current / avg_current_ch1 if avg_current_ch1 != 0 else 1.0
            current_gain_ch2 = reference_current / avg_current_ch2 if avg_current_ch2 != 0 else 1.0
            
            # Power calibration (derived from V and I calibration)
            power_gain_ch1 = voltage_gain_ch1 * current_gain_ch1
            power_gain_ch2 = voltage_gain_ch2 * current_gain_ch2
            
            # Create calibration data
            calibration = CalibrationData(
                meter_id=meter.config.meter_id,
                calibration_date=datetime.now(),
                voltage_gain_ch1=voltage_gain_ch1,
                voltage_offset_ch1=0.0,  # Could be calculated if needed
                voltage_gain_ch2=voltage_gain_ch2,
                voltage_offset_ch2=0.0,
                current_gain_ch1=current_gain_ch1,
                current_offset_ch1=0.0,
                current_gain_ch2=current_gain_ch2,
                current_offset_ch2=0.0,
                power_gain_ch1=power_gain_ch1,
                power_offset_ch1=0.0,
                power_gain_ch2=power_gain_ch2,
                power_offset_ch2=0.0,
                phase_compensation_ch1=0.0,  # Would be measured separately
                phase_compensation_ch2=0.0,
                reference_voltage=reference_voltage,
                reference_current=reference_current,
                reference_frequency=60.0,  # Standard frequency
                calibrated_by=calibrated_by,
                calibration_notes=notes,
            )
            
            # Step 4: Validate calibration
            if self._validate_calibration(calibration):
                # Save calibration data
                self.save_calibration(calibration)
                self.logger.info(f"EOL calibration completed for meter {meter.config.meter_id}")
                return calibration
            else:
                raise CalibrationError("Calibration validation failed")
                
        except Exception as e:
            raise CalibrationError(f"EOL calibration failed: {e}")
    
    def _validate_calibration(self, calibration: CalibrationData) -> bool:
        """
        Validate calibration coefficients are within acceptable ranges.
        
        Args:
            calibration: Calibration data to validate
            
        Returns:
            True if calibration is valid
        """
        # Define acceptable ranges for calibration coefficients
        min_gain = 0.5
        max_gain = 2.0
        max_offset = 10.0
        
        # Check voltage gains
        if not (min_gain <= calibration.voltage_gain_ch1 <= max_gain):
            self.logger.error(f"Voltage gain CH1 out of range: {calibration.voltage_gain_ch1}")
            return False
        
        if not (min_gain <= calibration.voltage_gain_ch2 <= max_gain):
            self.logger.error(f"Voltage gain CH2 out of range: {calibration.voltage_gain_ch2}")
            return False
        
        # Check current gains
        if not (min_gain <= calibration.current_gain_ch1 <= max_gain):
            self.logger.error(f"Current gain CH1 out of range: {calibration.current_gain_ch1}")
            return False
        
        if not (min_gain <= calibration.current_gain_ch2 <= max_gain):
            self.logger.error(f"Current gain CH2 out of range: {calibration.current_gain_ch2}")
            return False
        
        # Check offsets
        if abs(calibration.voltage_offset_ch1) > max_offset:
            self.logger.error(f"Voltage offset CH1 out of range: {calibration.voltage_offset_ch1}")
            return False
        
        if abs(calibration.voltage_offset_ch2) > max_offset:
            self.logger.error(f"Voltage offset CH2 out of range: {calibration.voltage_offset_ch2}")
            return False
        
        return True
    
    def list_calibrated_meters(self) -> List[str]:
        """
        Get list of meters with calibration data.
        
        Returns:
            List of meter IDs
        """
        return list(self._calibration_cache.keys())
    
    def export_calibration(self, meter_id: str, export_path: str) -> bool:
        """
        Export calibration data to a file.
        
        Args:
            meter_id: Meter identifier
            export_path: Path to export file
            
        Returns:
            True if successful
            
        Raises:
            CalibrationError: If export fails
        """
        try:
            calibration = self.get_calibration(meter_id)
            if not calibration:
                raise CalibrationError(f"No calibration data found for meter {meter_id}")
            
            with open(export_path, 'w') as f:
                json.dump(calibration.to_dict(), f, indent=2)
            
            self.logger.info(f"Exported calibration data for meter {meter_id} to {export_path}")
            return True
            
        except Exception as e:
            raise CalibrationError(f"Failed to export calibration: {e}")
    
    def import_calibration(self, import_path: str) -> str:
        """
        Import calibration data from a file.
        
        Args:
            import_path: Path to import file
            
        Returns:
            Meter ID of imported calibration
            
        Raises:
            CalibrationError: If import fails
        """
        try:
            with open(import_path, 'r') as f:
                cal_dict = json.load(f)
            
            calibration = CalibrationData(
                meter_id=cal_dict["meter_id"],
                calibration_date=datetime.fromisoformat(cal_dict["calibration_date"]),
                voltage_gain_ch1=cal_dict["voltage_calibration"]["ch1_gain"],
                voltage_offset_ch1=cal_dict["voltage_calibration"]["ch1_offset"],
                voltage_gain_ch2=cal_dict["voltage_calibration"]["ch2_gain"],
                voltage_offset_ch2=cal_dict["voltage_calibration"]["ch2_offset"],
                current_gain_ch1=cal_dict["current_calibration"]["ch1_gain"],
                current_offset_ch1=cal_dict["current_calibration"]["ch1_offset"],
                current_gain_ch2=cal_dict["current_calibration"]["ch2_gain"],
                current_offset_ch2=cal_dict["current_calibration"]["ch2_offset"],
                power_gain_ch1=cal_dict["power_calibration"]["ch1_gain"],
                power_offset_ch1=cal_dict["power_calibration"]["ch1_offset"],
                power_gain_ch2=cal_dict["power_calibration"]["ch2_gain"],
                power_offset_ch2=cal_dict["power_calibration"]["ch2_offset"],
                phase_compensation_ch1=cal_dict["phase_calibration"]["ch1_compensation"],
                phase_compensation_ch2=cal_dict["phase_calibration"]["ch2_compensation"],
                reference_voltage=cal_dict["reference_values"]["voltage"],
                reference_current=cal_dict["reference_values"]["current"],
                reference_frequency=cal_dict["reference_values"]["frequency"],
                calibrated_by=cal_dict["metadata"]["calibrated_by"],
                calibration_notes=cal_dict["metadata"].get("notes", ""),
            )
            
            self.save_calibration(calibration)
            
            self.logger.info(f"Imported calibration data for meter {calibration.meter_id}")
            return calibration.meter_id
            
        except Exception as e:
            raise CalibrationError(f"Failed to import calibration: {e}")