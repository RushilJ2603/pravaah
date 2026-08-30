"""Calibrated demand simulator (SOLUTION.md section 28.9).

Produces occupancy and movement for a city that publishes neither, so the
deployment target can be demonstrated end to end. Everything this package emits
carries `source_type=SIMULATED`; nothing here may ever produce a record that
does not.
"""
