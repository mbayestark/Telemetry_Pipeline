"""
Central configuration for the telemetry pipeline.

All tunable parameters live here so the system can be adjusted in one place
without touching pipeline logic.
"""

# Devices simulated by the generator
DEVICES = ["DEV_001", "DEV_002", "DEV_003", "DEV_004", "DEV_005"]

# Number of clean records to generate before injecting messy ones
DEFAULT_CLEAN_RECORDS = 200

# Normal reporting interval between readings (minutes)
NORMAL_INTERVAL_MINUTES = 5

# Valid sensor ranges — used by the validator for range checks.
# These are the physically possible limits of the sensors (wider than the
# normal operating band), so a genuinely hot reading is still a VALID reading
# that the alerting layer can flag — not something the validator throws away.
VALID_RANGES = {
    "temperature": (-40, 85),      # celsius (sensor physical limits)
    "battery": (0, 100),           # percent
    "signal_strength": (-120, 0),  # dBm
}

# Normal operating band used to GENERATE clean sample data. Sits inside the
# valid range; anomalous-but-valid readings are injected outside this band.
NORMAL_TEMP_RANGE = (18, 70)       # celsius

# Alert thresholds
# Note: valid temperature readings span 18-70C (see VALID_RANGES). Alert
# thresholds sit OUTSIDE the normal operating band so that only genuinely
# concerning readings trigger an alert, not every normal high/low reading.
BATTERY_THRESHOLD = 20.0     # alert if latest battery below this (percent)
TEMP_HIGH_THRESHOLD = 75.0   # alert if any reading above this (celsius)
TEMP_LOW_THRESHOLD = 10.0    # alert if any reading below this (celsius)
MAX_GAP_MINUTES = 30.0       # alert if gap between readings exceeds this (minutes)

# Rate-of-change thresholds — flag physically implausible jumps between
# consecutive readings, even when both values are individually in range.
MAX_TEMP_CHANGE_PER_MINUTE = 2.0    # °C per minute
MAX_BATTERY_CHANGE_PER_MINUTE = 1.0 # % per minute