@echo off
REM Leave this window OPEN overnight. Every hour recorded = real training data.
REM Ctrl+C to stop.
cd /d "%~dp0"
echo Recording live MBTA vehicle positions + REAL occupancy. Keep this window open.
python record_feed.py --interval 20
pause
