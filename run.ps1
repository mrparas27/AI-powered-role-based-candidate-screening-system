# Powershell Script to launch both servers concurrently in new windows
Start-Process powershell -ArgumentList "-NoExit", "-Command", "$env:PYTHONPATH='.'; uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload" -Title "Evaluator.AI Backend"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev" -Title "Evaluator.AI Frontend"
Write-Host "Both FastAPI Backend and Vite Frontend servers have been launched in separate terminal windows." -ForegroundColor Green
