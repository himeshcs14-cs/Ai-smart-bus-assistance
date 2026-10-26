import sqlite3
from datetime import date, datetime, time
from pathlib import Path

import pandas as pd
import streamlit as st

from database import DB_NAME, init_db
from ai_assistant import ask_bus_assistant

init_db()


# ---------------------------------------------------------
# Page setup and visual system
# ---------------------------------------------------------
st.set_page_config(
    page_title="FleetIQ | Smart Bus Management",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root {
        --navy: #14213D;
        --navy-light: #1E3157;
        --blue: #2563EB;
        --blue-soft: #EAF1FF;
        --canvas: #F4F7FB;
        --ink: #18243A;
        --muted: #68758B;
        --line: #E1E8F0;
        --white: #FFFFFF;
        --green: #16805D;
        --amber: #B96B0B;
        --red: #C43D4B;
    }
    .stApp { background: var(--canvas); color: var(--ink); }
    .block-container {
        max-width: 1540px;
        padding-top: 1.4rem;
        padding-bottom: 3rem;
    }
    section[data-testid="stSidebar"] {
        background: var(--navy);
        border-right: 1px solid #24385E;
    }
    section[data-testid="stSidebar"] * { color: #F7FAFF; }
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        color: #D5DFEF;
    }
    section[data-testid="stSidebar"] div[data-baseweb="select"] * {
        color: #172033;
    }
    .brand-row {
        display: flex; align-items: center; gap: 12px;
        padding: 8px 0 18px 0;
    }
    .brand-mark {
        width: 44px; height: 44px; border-radius: 13px;
        display: flex; align-items: center; justify-content: center;
        background: #2E5BBD; font-size: 23px;
    }
    .brand-title { font-size: 21px; font-weight: 800; color: #FFFFFF; line-height: 1.1; }
    .brand-sub { color: #B9C8E0; font-size: 11px; letter-spacing: 1.3px; margin-top: 5px; }
    .eyebrow {
        color: var(--blue); font-size: 11px; font-weight: 800;
        letter-spacing: 1.6px; text-transform: uppercase; margin-bottom: 7px;
    }
    .page-title { color: var(--ink); font-size: 30px; font-weight: 800; line-height: 1.2; }
    .page-subtitle { color: var(--muted); font-size: 14px; margin-top: 7px; margin-bottom: 18px; }
    .section-title { font-size: 18px; font-weight: 750; color: var(--ink); margin: 8px 0 3px 0; }
    .section-subtitle { color: var(--muted); font-size: 13px; margin-bottom: 12px; }
    div[data-testid="stMetric"] {
        background: #FFFFFF; border: 1px solid var(--line);
        border-radius: 15px; padding: 18px 18px 15px 18px;
        box-shadow: 0 4px 15px rgba(20, 33, 61, .035);
    }
    div[data-testid="stMetricLabel"] { color: var(--muted); font-size: 13px; }
    div[data-testid="stMetricValue"] { color: var(--navy); font-weight: 800; }
    div[data-testid="stMetricDelta"] { font-size: 12px; }
    div[data-testid="stForm"] {
        background: #FFFFFF; border: 1px solid var(--line);
        border-radius: 14px; padding: 20px;
    }
    div[data-testid="stDataFrame"] {
        border: 1px solid var(--line); border-radius: 12px; overflow: hidden;
        background: #FFFFFF;
    }
    .stButton > button, .stFormSubmitButton > button,
    .stDownloadButton > button {
        border-radius: 9px; min-height: 40px; font-weight: 650;
    }
    .stButton > button[kind="primary"],
    .stFormSubmitButton > button[kind="primary"] {
        background: var(--blue); border-color: var(--blue);
    }
    div[data-testid="stAlert"] { border-radius: 11px; }
    hr { border-color: var(--line); }
    .status-pill {
        display: inline-block; padding: 4px 9px; border-radius: 999px;
        background: var(--blue-soft); color: #204EAD;
        font-size: 11px; font-weight: 800; letter-spacing: .3px;
    }
    .footer-note { color: #8390A3; font-size: 11px; padding-top: 20px; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# Database access
# ---------------------------------------------------------
def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def load_bus_records():
    """Load trips with bus, route and driver details."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT
                t.trip_id,
                t.bus_id,
                b.registration_no,
                b.status,
                b.route_id,
                r.route_name,
                r.scheduled_departure,
                t.trip_date,
                t.actual_departure,
                COALESCE(t.students_count, 0) AS students_count,
                d.driver_id,
                d.driver_name,
                d.phone_no
            FROM bus_trips AS t
            JOIN buses AS b ON b.bus_id = t.bus_id
            JOIN routes AS r ON r.route_id = b.route_id
            LEFT JOIN drivers AS d ON d.bus_id = b.bus_id
            ORDER BY t.trip_date DESC, t.trip_id DESC
            """
        ).fetchall()
        records = [dict(row) for row in rows]
    finally:
        conn.close()

    for record in records:
        scheduled = record.get("scheduled_departure")
        actual = record.get("actual_departure")
        if scheduled and actual:
            try:
                start = datetime.strptime(scheduled, "%H:%M")
                end = datetime.strptime(actual, "%H:%M")
                record["delay_minutes"] = int((end - start).total_seconds() / 60)
            except ValueError:
                record["delay_minutes"] = None
        else:
            record["delay_minutes"] = None
    return records


def load_buses():
    conn = get_connection()
    try:
        return [
            dict(row)
            for row in conn.execute(
                """
                SELECT b.bus_id, b.registration_no, b.route_id,
                       r.route_name, b.status
                FROM buses b
                JOIN routes r ON r.route_id = b.route_id
                ORDER BY b.bus_id
                """
            ).fetchall()
        ]
    finally:
        conn.close()


def load_drivers():
    conn = get_connection()
    try:
        return [
            dict(row)
            for row in conn.execute(
                """
                SELECT d.driver_id, d.driver_name, d.phone_no, d.bus_id,
                       b.registration_no, r.route_name
                FROM drivers d
                JOIN buses b ON b.bus_id = d.bus_id
                JOIN routes r ON r.route_id = b.route_id
                ORDER BY d.driver_id
                """
            ).fetchall()
        ]
    finally:
        conn.close()


def get_stops_for_route(route_name):
    """Return stops from route_stops for the selected route, in route order."""
    if not route_name or route_name == "All routes":
        return []

    conn = get_connection()
    try:
        # Older databases may not have the route_stops table yet.
        table_exists = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='route_stops'"
        ).fetchone()
        if not table_exists:
            return []

        rows = conn.execute(
            """
            SELECT s.stop_name
            FROM route_stops AS s
            JOIN routes AS r ON r.route_id = s.route_id
            WHERE r.route_name = ?
            ORDER BY s.stop_order, s.stop_id
            """,
            (route_name,),
        ).fetchall()
        return [row["stop_name"] for row in rows]
    except sqlite3.Error:
        return []
    finally:
        conn.close()


def save_departure(bus_id, trip_date, actual_departure, students_count):
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO bus_trips
                (bus_id, trip_date, actual_departure, students_count)
            VALUES (?, ?, ?, ?)
            """,
            (bus_id, trip_date, actual_departure, int(students_count)),
        )
        conn.commit()
        return True, "Departure saved successfully."
    except sqlite3.IntegrityError as exc:
        conn.rollback()
        if "unique" in str(exc).lower():
            return False, "A trip is already recorded for this bus on this date."
        return False, f"Could not save the trip: {exc}"
    except sqlite3.Error as exc:
        conn.rollback()
        return False, f"Database error: {exc}"
    finally:
        conn.close()


def edit_departure(trip_id, actual_departure, students_count):
    conn = get_connection()
    try:
        cur = conn.execute(
            """
            UPDATE bus_trips
            SET actual_departure = ?, students_count = ?
            WHERE trip_id = ?
            """,
            (actual_departure, int(students_count), int(trip_id)),
        )
        conn.commit()
        if cur.rowcount == 0:
            return False, "Trip not found."
        return True, "Trip updated successfully."
    except sqlite3.Error as exc:
        conn.rollback()
        return False, f"Database error: {exc}"
    finally:
        conn.close()


# ---------------------------------------------------------
# Load application data
# ---------------------------------------------------------
try:
    all_records = load_bus_records()
    buses = load_buses()
    drivers = load_drivers()
except Exception as exc:
    st.error(f"Could not load the bus database: {exc}")
    st.info(
        "Check that bus_management.db is in this project folder and that "
        "database.py has created the required tables."
    )
    st.stop()

if not buses:
    st.warning("No buses were found in the database. Add buses before using the dashboard.")
    st.stop()

trips_df = pd.DataFrame(all_records)
buses_df = pd.DataFrame(buses)
drivers_df = pd.DataFrame(drivers)


# ---------------------------------------------------------
# Sidebar navigation and filters
# ---------------------------------------------------------
with st.sidebar:
    st.markdown(
        """
        <div class="brand-row">
            <div class="brand-mark">🚌</div>
            <div>
                <div class="brand-title">FleetIQ</div>
                <div class="brand-sub">SMART TRANSPORT</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.markdown("**WORKSPACE**")
    page = st.radio(
        "Navigation",
        [
            "Overview",
            "Buses & Drivers",
            "Trip Management",
            "Reports & Analytics",
            "AI Assistant",
        ],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.markdown("**FILTERS**")

    date_values = sorted(
        trips_df["trip_date"].dropna().astype(str).unique().tolist(),
        reverse=True,
    ) if not trips_df.empty else []
    date_choices = ["All dates"] + date_values
    chosen_date = st.selectbox("Trip date", date_choices, index=0)

    route_values = sorted(buses_df["route_name"].dropna().unique().tolist())
    chosen_route = st.selectbox(
        "Route",
        ["All routes"] + route_values,
        key="sidebar_route_filter",
    )

    # Stop List dropdown appears immediately below Route.
    if chosen_route != "All routes":
        stop_values = get_stops_for_route(chosen_route)
        if stop_values:
            chosen_stop = st.selectbox(
                "Stop List",
                ["All Stops"] + stop_values,
                key="sidebar_stop_filter",
            )
        else:
            chosen_stop = "All Stops"
            st.selectbox(
                "Stop List",
                ["No stops configured"],
                disabled=True,
                key="sidebar_stop_filter_empty",
            )
            st.caption("Add stops to the route_stops table to populate this list.")
    else:
        chosen_stop = "All Stops"
        st.selectbox(
            "Stop List",
            ["Select a route first"],
            disabled=True,
            key="sidebar_stop_filter_disabled",
        )

    status_values = sorted(buses_df["status"].dropna().astype(str).unique().tolist())
    chosen_status = st.selectbox("Bus status", ["All statuses"] + status_values)

    st.markdown("---")
    st.caption("Data source: local SQLite database")
    st.caption("AI engine: IBM watsonx.ai · Granite")
    if chosen_route != "All routes" and chosen_stop != "All Stops":
        st.caption("Stop selected for reference. Trip filtering by stop requires assigning each trip a stop in the database.")


# Apply filters to trip records.
filtered = trips_df.copy()
if not filtered.empty:
    if chosen_date != "All dates":
        filtered = filtered[filtered["trip_date"].astype(str) == chosen_date]
    if chosen_route != "All routes":
        filtered = filtered[filtered["route_name"] == chosen_route]
    if chosen_status != "All statuses":
        filtered = filtered[filtered["status"] == chosen_status]

filtered_buses = buses_df.copy()
if chosen_route != "All routes":
    filtered_buses = filtered_buses[filtered_buses["route_name"] == chosen_route]
if chosen_status != "All statuses":
    filtered_buses = filtered_buses[filtered_buses["status"].astype(str) == chosen_status]


# ---------------------------------------------------------
# Shared page header
# ---------------------------------------------------------
header_left, header_right = st.columns([4, 1])
with header_left:
    st.markdown('<div class="eyebrow">TRANSPORT OPERATIONS / CONTROL CENTER</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="page-title">{page}</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Monitor fleet activity, manage trips, and get answers from your bus data.</div>',
        unsafe_allow_html=True,
    )
with header_right:
    st.markdown(
        '<div style="text-align:right;padding-top:14px">'
        '<span class="status-pill">● LOCAL SYSTEM</span></div>',
        unsafe_allow_html=True,
    )

if chosen_date == "All dates":
    date_context = "All recorded dates"
else:
    date_context = chosen_date


# ---------------------------------------------------------
# Overview
# ---------------------------------------------------------
if page == "Overview":
    metric_buses = int(filtered_buses["bus_id"].nunique()) if not filtered_buses.empty else 0
    students_total = int(pd.to_numeric(filtered["students_count"], errors="coerce").fillna(0).sum()) if not filtered.empty else 0
    late_count = int((pd.to_numeric(filtered["delay_minutes"], errors="coerce") > 0).sum()) if not filtered.empty else 0
    valid_delays = pd.to_numeric(filtered["delay_minutes"], errors="coerce").dropna() if not filtered.empty else pd.Series(dtype=float)
    avg_delay = f"{valid_delays.mean():.1f} min" if not valid_delays.empty else "—"

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Fleet buses", metric_buses, help="Unique buses matching the sidebar filters")
    m2.metric("Students in selected trips", f"{students_total:,}", help="Sum of student counts across the selected trip records")
    m3.metric("Delayed trips", late_count, help="Trips departing later than schedule")
    m4.metric("Average departure delay", avg_delay, help="Average across records with both scheduled and actual times")

    st.markdown("<br>", unsafe_allow_html=True)
    left, right = st.columns([1.55, 1])

    with left:
        st.markdown('<div class="section-title">Departure performance</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-subtitle">Delay in minutes by route. Negative values mean early departure.</div>', unsafe_allow_html=True)
        chart_data = filtered.dropna(subset=["delay_minutes"]).copy() if not filtered.empty else pd.DataFrame()
        if not chart_data.empty:
            route_chart = chart_data.groupby("route_name", as_index=True)["delay_minutes"].mean().sort_values(ascending=False)
            st.bar_chart(route_chart, use_container_width=True)
        else:
            st.info("No departure times are available for the current filters.")

    with right:
        st.markdown('<div class="section-title">Students by route</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-subtitle">Based on the currently selected trip records.</div>', unsafe_allow_html=True)
        if not filtered.empty:
            route_students = filtered.groupby("route_name")["students_count"].sum().sort_values(ascending=False)
            st.bar_chart(route_students, use_container_width=True)
        else:
            st.info("No trip records match the selected filters.")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">Recent trip activity</div>', unsafe_allow_html=True)
    if not filtered.empty:
        recent = filtered.head(8).copy()
        recent = recent.rename(columns={
            "bus_id": "Bus ID",
            "registration_no": "Registration",
            "route_name": "Route",
            "driver_name": "Driver",
            "trip_date": "Trip date",
            "actual_departure": "Actual departure",
            "students_count": "Students",
            "delay_minutes": "Delay (min)",
        })
        cols = ["Bus ID", "Registration", "Route", "Driver", "Trip date", "Actual departure", "Students", "Delay (min)"]
        st.dataframe(recent[[c for c in cols if c in recent.columns]], use_container_width=True, hide_index=True)
    else:
        st.info("No trips match the current filters.")

    # Quick chat panel on the Overview page, in addition to the full AI Assistant page.
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">Ask FleetIQ · IBM Granite AI</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-subtitle">Ask a question about the bus, driver, route, student, or trip records shown in your database.</div>',
        unsafe_allow_html=True,
    )
    if "overview_granite_history" not in st.session_state:
        st.session_state["overview_granite_history"] = []

    with st.form("overview_granite_chat_form", clear_on_submit=True):
        overview_question = st.text_input(
            "Your question",
            placeholder="e.g. How many students are travelling on the Navalur route?",
            key="overview_granite_question",
        )
        overview_ask = st.form_submit_button("Ask Granite", type="primary")

    if overview_ask:
        if not overview_question.strip():
            st.warning("Enter a question first.")
        elif filtered.empty:
            st.warning("No trip records match the current filters. Adjust the sidebar filters and try again.")
        else:
            with st.spinner("Granite is reviewing your bus records..."):
                try:
                    overview_answer = ask_bus_assistant(
                        overview_question, filtered.to_dict(orient="records")
                    )
                    st.session_state["overview_granite_history"].append(
                        {"question": overview_question, "answer": overview_answer}
                    )
                except Exception as exc:
                    st.error(f"Granite request failed: {type(exc).__name__}: {exc}")

    for chat_item in st.session_state["overview_granite_history"]:
        with st.chat_message("user"):
            st.write(chat_item["question"])
        with st.chat_message("assistant"):
            st.markdown(chat_item["answer"])

    if st.session_state["overview_granite_history"]:
        if st.button("Clear overview chat", key="clear_overview_granite_chat"):
            st.session_state["overview_granite_history"] = []
            st.rerun()


# ---------------------------------------------------------
# Buses and drivers
# ---------------------------------------------------------
elif page == "Buses & Drivers":
    st.markdown('<div class="section-title">Fleet directory</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Bus registrations, assigned routes, and current status.</div>', unsafe_allow_html=True)

    if not filtered_buses.empty:
        bus_view = filtered_buses.rename(columns={
            "bus_id": "Bus ID",
            "registration_no": "Registration number",
            "route_name": "Route",
            "status": "Status",
        })
        st.dataframe(bus_view[["Bus ID", "Registration number", "Route", "Status"]], use_container_width=True, hide_index=True)
    else:
        st.info("No buses match the selected filters.")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">Driver directory</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Driver contact information and assigned bus.</div>', unsafe_allow_html=True)
    if not drivers_df.empty:
        driver_view = drivers_df.copy()
        if chosen_route != "All routes":
            driver_view = driver_view[driver_view["route_name"] == chosen_route]
        driver_view = driver_view.rename(columns={
            "driver_id": "Driver ID",
            "driver_name": "Driver name",
            "phone_no": "Phone number",
            "bus_id": "Assigned bus",
            "registration_no": "Registration",
            "route_name": "Route",
        })
        st.dataframe(driver_view[["Driver ID", "Driver name", "Phone number", "Assigned bus", "Registration", "Route"]], use_container_width=True, hide_index=True)
    else:
        st.info("No driver records found. Add driver assignments to the drivers table.")


# ---------------------------------------------------------
# Trip management
# ---------------------------------------------------------
elif page == "Trip Management":
    create_tab, edit_tab = st.tabs(["＋ Record departure", "✎ Edit existing trip"])

    with create_tab:
        st.markdown('<div class="section-title">Record a bus departure</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-subtitle">Create one trip record per bus per date.</div>', unsafe_allow_html=True)

        with st.form("create_trip_form", clear_on_submit=False):
            bus_lookup = {
                f"{b['bus_id']} · {b['registration_no']} · {b['route_name']}": b["bus_id"]
                for b in buses
            }
            bus_label = st.selectbox("Bus and route", list(bus_lookup.keys()))
            c1, c2, c3 = st.columns(3)
            with c1:
                trip_day = st.date_input("Trip date", value=date.today())
            with c2:
                actual_time = st.time_input("Actual departure", value=time(8, 0))
            with c3:
                student_count = st.number_input("Students travelling", min_value=0, max_value=500, value=0, step=1)
            save = st.form_submit_button("Save departure", type="primary", use_container_width=True)

        if save:
            ok, message = save_departure(
                bus_lookup[bus_label],
                trip_day.isoformat(),
                actual_time.strftime("%H:%M"),
                student_count,
            )
            if ok:
                st.success(message)
                st.rerun()
            else:
                st.error(message)

    with edit_tab:
        st.markdown('<div class="section-title">Correct an existing trip</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-subtitle">Update the departure time or passenger count without creating a duplicate.</div>', unsafe_allow_html=True)

        if not all_records:
            st.info("No trip records are available to edit.")
        else:
            trip_options = {
                f"Trip {r['trip_id']} · {r['bus_id']} · {r['trip_date']} · {r['actual_departure'] or 'No time'}": r
                for r in all_records
            }
            with st.form("edit_trip_form"):
                trip_label = st.selectbox("Select trip", list(trip_options.keys()))
                chosen_trip = trip_options[trip_label]
                old_time = chosen_trip.get("actual_departure") or "08:00"
                try:
                    default_time = time.fromisoformat(old_time)
                except ValueError:
                    default_time = time(8, 0)
                c1, c2 = st.columns(2)
                with c1:
                    corrected_time = st.time_input("Correct departure time", value=default_time)
                with c2:
                    corrected_students = st.number_input(
                        "Correct student count",
                        min_value=0,
                        max_value=500,
                        value=int(chosen_trip.get("students_count") or 0),
                        step=1,
                    )
                update = st.form_submit_button("Update trip", type="primary", use_container_width=True)

            if update:
                ok, message = edit_departure(
                    chosen_trip["trip_id"],
                    corrected_time.strftime("%H:%M"),
                    corrected_students,
                )
                if ok:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)


# ---------------------------------------------------------
# Reports and analytics
# ---------------------------------------------------------
elif page == "Reports & Analytics":
    st.markdown('<div class="section-title">Route passenger report</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Passenger counts are summed from the trips currently selected in the sidebar.</div>', unsafe_allow_html=True)

    if not filtered.empty:
        report = filtered.groupby("route_name", as_index=False).agg(
            Trips=("trip_id", "count"),
            Buses=("bus_id", "nunique"),
            Students=("students_count", "sum"),
            Average_delay_minutes=("delay_minutes", "mean"),
        )
        report["Average_delay_minutes"] = report["Average_delay_minutes"].round(1)
        report = report.sort_values("Students", ascending=False)
        st.dataframe(report.rename(columns={
            "route_name": "Route",
            "Average_delay_minutes": "Average delay (min)",
        }), use_container_width=True, hide_index=True)

        csv_data = filtered.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "Download filtered trip report (CSV)",
            data=csv_data,
            file_name="bus_trip_report.csv",
            mime="text/csv",
            type="primary",
        )
    else:
        st.info("No trip records match the current filters, so there is nothing to export.")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">Departure delay distribution</div>', unsafe_allow_html=True)
    if not filtered.empty:
        delay_data = filtered.dropna(subset=["delay_minutes"])
        if not delay_data.empty:
            st.bar_chart(delay_data.set_index("bus_id")["delay_minutes"], use_container_width=True)
        else:
            st.info("No delay values are available.")


# ---------------------------------------------------------
# IBM Granite assistant
# ---------------------------------------------------------
elif page == "AI Assistant":
    st.markdown('<div class="section-title">Ask your transport data</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-subtitle">Ask about drivers, assigned buses, passenger counts, routes, and recorded delays. Answers use the records supplied from SQLite.</div>',
        unsafe_allow_html=True,
    )

    sample_questions = [
        "Who is the driver of BUS05?",
        "How many students are travelling on the Navalur route?",
        "Which buses were delayed?",
        "Show the drivers and student counts for Navalur buses.",
    ]
    st.markdown("**Try asking**")
    prompt_cols = st.columns(2)
    for i, prompt in enumerate(sample_questions):
        with prompt_cols[i % 2]:
            if st.button(prompt, key=f"prompt_{i}", use_container_width=True):
                st.session_state["granite_question"] = prompt

    if "granite_history" not in st.session_state:
        st.session_state["granite_history"] = []

    with st.form("granite_chat_form", clear_on_submit=True):
        question = st.text_input(
            "Your question",
            value=st.session_state.pop("granite_question", ""),
            placeholder="e.g. How many students are travelling on Navalur today?",
        )
        ask = st.form_submit_button("Ask Granite", type="primary", use_container_width=True)

    if ask:
        if not question.strip():
            st.warning("Enter a question first.")
        elif not all_records:
            st.warning("There are no trip records to ask about yet.")
        else:
            # Apply sidebar filters to the context sent to the model.
            ai_records = filtered.to_dict(orient="records") if not filtered.empty else []
            if not ai_records:
                st.info("No trip records match the selected filters. Change the filters to provide relevant records.")
            else:
                with st.spinner("Granite is reviewing the selected bus records..."):
                    try:
                        answer = ask_bus_assistant(question, ai_records)
                        st.session_state["granite_history"].append(
                            {"question": question, "answer": answer}
                        )
                    except Exception as exc:
                        st.error(f"Granite request failed: {type(exc).__name__}: {exc}")

    for item in reversed(st.session_state["granite_history"]):
        with st.chat_message("user"):
            st.write(item["question"])
        with st.chat_message("assistant"):
            st.markdown(item["answer"])

    if st.session_state["granite_history"]:
        if st.button("Clear chat history"):
            st.session_state["granite_history"] = []
            st.rerun()


st.markdown(
    '<div class="footer-note">FleetIQ · AI Smart Bus Management Assistant · '
    'Local prototype using SQLite and IBM watsonx.ai Granite. '
    'Passenger and trip totals reflect recorded sample/application data, not live GPS tracking.</div>',
    unsafe_allow_html=True,
)
