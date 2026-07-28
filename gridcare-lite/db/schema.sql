CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin', 'engineer', 'technician', 'customer_service'))
);

CREATE TABLE substations (
    substation_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    region TEXT NOT NULL
);

CREATE TABLE outages (
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

CREATE TABLE work_orders (
    work_order_id INTEGER PRIMARY KEY AUTOINCREMENT,
    outage_id INTEGER NOT NULL,
    assigned_technician INTEGER,
    scheduled_date TEXT,
    status TEXT DEFAULT 'Pending' CHECK (status IN ('Pending', 'Scheduled', 'Completed')),
    FOREIGN KEY (outage_id) REFERENCES outages(outage_id),
    FOREIGN KEY (assigned_technician) REFERENCES users(user_id)
);

CREATE TABLE complaints (
    complaint_id INTEGER PRIMARY KEY AUTOINCREMENT,
    outage_id INTEGER,
    logged_by INTEGER NOT NULL,
    description TEXT,
    logged_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (outage_id) REFERENCES outages(outage_id),
    FOREIGN KEY (logged_by) REFERENCES users(user_id)
);
