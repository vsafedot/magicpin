@echo off
echo Starting Vera Deterministic Bot...
pip install -q fastapi uvicorn pydantic
python main.py
pause
