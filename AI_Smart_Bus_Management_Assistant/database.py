import sqlite3
from pathlib import Path
from datetime import date
DB_NAME = str(Path(__file__).with_name('bus_management.db'))

def get_connection():
    c=sqlite3.connect(DB_NAME, timeout=10); c.row_factory=sqlite3.Row; c.execute('PRAGMA foreign_keys=ON'); return c

def init_db():
    with get_connection() as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS routes(route_id TEXT PRIMARY KEY, route_name TEXT NOT NULL UNIQUE, scheduled_departure TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS buses(bus_id TEXT PRIMARY KEY, registration_no TEXT NOT NULL UNIQUE, route_id TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'Active', capacity INTEGER NOT NULL DEFAULT 40, FOREIGN KEY(route_id) REFERENCES routes(route_id));
        CREATE TABLE IF NOT EXISTS drivers(driver_id TEXT PRIMARY KEY, driver_name TEXT NOT NULL, phone_no TEXT NOT NULL, bus_id TEXT UNIQUE, FOREIGN KEY(bus_id) REFERENCES buses(bus_id));
        CREATE TABLE IF NOT EXISTS route_stops(stop_id INTEGER PRIMARY KEY AUTOINCREMENT, route_id TEXT NOT NULL, stop_name TEXT NOT NULL, stop_order INTEGER NOT NULL, FOREIGN KEY(route_id) REFERENCES routes(route_id), UNIQUE(route_id,stop_name), UNIQUE(route_id,stop_order));
        CREATE TABLE IF NOT EXISTS bus_trips(trip_id INTEGER PRIMARY KEY AUTOINCREMENT, bus_id TEXT NOT NULL, trip_date TEXT NOT NULL, actual_departure TEXT NOT NULL, students_count INTEGER NOT NULL DEFAULT 0 CHECK(students_count>=0), UNIQUE(bus_id,trip_date), FOREIGN KEY(bus_id) REFERENCES buses(bus_id));
        ''')
        route_rows=[('R01','Sholinganallur','08:00'),('R02','Navalur','08:10'),('R03','Tambaram','08:20'),('R04','Tiruvallur','08:30'),('R05','MGR Central','08:40')]
        for r in route_rows:c.execute('INSERT OR IGNORE INTO routes VALUES(?,?,?)',r)
        for i in range(1,11):
            rid=route_rows[(i-1)%len(route_rows)][0]
            c.execute('INSERT OR IGNORE INTO buses(bus_id,registration_no,route_id,status,capacity) VALUES(?,?,?,?,?)',(f'BUS{i:02d}',f'TN-01-AB-{1000+i}',rid,'Active',40))
        names=['Arun Kumar','Bala Kumar','Charan Raj','Deepak S','Ezhil V','Farhan A','Gokul R','Hari P','Inba S','Jeeva M']
        for i,n in enumerate(names,1):c.execute('INSERT OR IGNORE INTO drivers VALUES(?,?,?,?)',(f'D{i:03d}',n,f'90000000{i:02d}',f'BUS{i:02d}'))
        stopmap={'R01':['Sholinganallur','Perungudi','Thoraipakkam','Taramani'],'R02':['Navalur','Siruseri','Kelambakkam'],'R03':['Tambaram','Perungalathur','Vandalur'],'R04':['Tiruvallur','Veppampattu','Tiruninravur'],'R05':['MGR Central','Egmore','Guindy']}
        for rid,stops in stopmap.items():
            for order,name in enumerate(stops,1):c.execute('INSERT OR IGNORE INTO route_stops(route_id,stop_name,stop_order) VALUES(?,?,?)',(rid,name,order))
        if c.execute('SELECT COUNT(*) FROM bus_trips').fetchone()[0]==0:
            samples=[('BUS01','08:10',38),('BUS02','08:13',42),('BUS03','08:35',35),('BUS04','08:30',40),('BUS05','08:47',32)]
            for bid,actual,students in samples:c.execute('INSERT OR IGNORE INTO bus_trips(bus_id,trip_date,actual_departure,students_count) VALUES(?,?,?,?)',(bid,date.today().isoformat(),actual,students))
