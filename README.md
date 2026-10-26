# AI Smart Bus Management Assistant — FleetIQ

A Streamlit project for bus operations with SQLite storage, route-dependent Stop List, bus/driver views, trip management, delay calculations, reports/CSV export, and an IBM Granite chat assistant.

**Demo data is synthetic.** This app is not connected to real buses, GPS, or live vehicle telemetry and does not predict future delays.

## Run on Windows in VS Code
1. Extract the ZIP to a folder.
2. Open the extracted folder in VS Code (File → Open Folder).
3. Open Terminal → New Terminal and run:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

4. Open the localhost address shown in the terminal, usually http://localhost:8501.

If PowerShell blocks activation, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in that terminal and activate again, or use `run_project.bat` by typing `cmd /c run_project.bat`.

## Configure IBM Granite (optional but required for live AI chat)
Copy `.env.example` to `.env`, then fill in your own `WATSONX_API_KEY` and `WATSONX_PROJECT_ID`. The sample endpoint is Frankfurt; use the endpoint for your own IBM project region. Restart Streamlit after editing `.env`. Never share or commit `.env` or your API key. The dashboard and database features work without AI credentials, but Granite chat will not.

## What is included
- Dashboard, filters, KPIs, charts and trip tables
- Bus/driver details and trip management
- Route stops stored in SQLite and a Route/Stop List dropdown
- Delay calculation from route scheduled time and actual departure
- Reports and CSV export
- IBM Granite chat through watsonx.ai when configured
- Synthetic starter records for a demo

## Data and limitations
The first run creates `bus_management.db` and inserts sample buses, routes, drivers, stops, and trip records. The data is fictional. Use authorised real records for real use. AI answers can be wrong and must be checked against the reports. No GPS integration or predictive model is included.
