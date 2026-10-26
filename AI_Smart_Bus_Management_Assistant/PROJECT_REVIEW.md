# Mentor review notes

**Objective:** Organise college bus records, calculate recorded departure delays, show reports, and let an administrator ask natural-language questions about the stored records.

**Tools:** Python, Streamlit, SQLite, Pandas, IBM watsonx.ai SDK, IBM Granite, python-dotenv, VS Code.

**Architecture:** Streamlit provides the UI; Python handles logic and delay calculations; SQLite stores buses, routes, drivers, stops and trips; Python retrieves relevant records and sends them with a question to Granite through watsonx.ai.

**Honest scope:** Granite is an existing hosted model; it was not trained in this project. Starter records are synthetic. The app does not collect live data, track GPS, or predict future delays.

**Demo:** Overview → show route filter and Stop List → Trip Management → reports/export → AI assistant (only after credentials are configured).
