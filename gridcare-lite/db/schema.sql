-- GridCare-Lite database schema (SQLite)

CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin', 'engineer', 'technician', 'customer_service'))
);

CREATE TABLE IF NOT EXISTS substations (
    substation_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    region TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS lines (
    line_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_substation TEXT,
    destination_substation TEXT,
    length_km REAL,
    voltage_kv REAL
);

CREATE TABLE IF NOT EXISTS outages (
    outage_id INTEGER PRIMARY KEY AUTOINCREMENT,
    substation_id INTEGER NOT NULL,
    reported_by INTEGER NOT NULL,
    description TEXT,
    severity TEXT,
    status TEXT DEFAULT 'Open' CHECK (status IN ('Open', 'In Progress', 'Resolved')),
    reported_at TEXT DEFAULT CURRENT_TIMESTAMP,
    resolved_at TEXT,
    FOREIGN KEY (substation_id) REFERENCES substations(substation_id),
    FOREIGN KEY (reported_by) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS work_orders (
    work_order_id INTEGER PRIMARY KEY AUTOINCREMENT,
    outage_id INTEGER NOT NULL,
    assigned_technician INTEGER,
    scheduled_date TEXT,
    status TEXT DEFAULT 'Pending' CHECK (status IN ('Pending', 'Scheduled', 'Completed')),
    FOREIGN KEY (outage_id) REFERENCES outages(outage_id),
    FOREIGN KEY (assigned_technician) REFERENCES users(user_id)
);

-- `customer_name` extends the base spec's complaints table (which only
-- requires outage_id, logged_by, description, logged_at) so a customer
-- service rep can record who actually complained, not just which staff
-- member logged it.
CREATE TABLE IF NOT EXISTS complaints (
    complaint_id INTEGER PRIMARY KEY AUTOINCREMENT,
    outage_id INTEGER,
    logged_by INTEGER NOT NULL,
    customer_name TEXT NOT NULL,
    description TEXT NOT NULL,
    logged_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (outage_id) REFERENCES outages(outage_id),
    FOREIGN KEY (logged_by) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS status_history (
    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    outage_id INTEGER NOT NULL,
    old_status TEXT,
    new_status TEXT NOT NULL,
    changed_by INTEGER NOT NULL,
    changed_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (outage_id) REFERENCES outages(outage_id),
    FOREIGN KEY (changed_by) REFERENCES users(user_id)
);
