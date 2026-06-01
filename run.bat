@echo off
echo Launching Evaluator.AI Backend Server...
start cmd /k "title Evaluator.AI Backend && set PYTHONPATH=. && uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload"

echo Launching Evaluator.AI Frontend Server...
start cmd /k "title Evaluator.AI Frontend && cd frontend && npm run dev"

echo Both servers are launching. Close their respective windows to stop them.
