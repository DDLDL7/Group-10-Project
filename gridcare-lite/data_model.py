import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
import hashlib
import csv
from datetime import datetime


# ============================================================
# DATABASE CLASS
# ============================================================

class Database:

    def __init__(self, database_name="gridcare.db"):
        self.database_name = database_name
        self.init_db()

    # --------------------------------------------------------
    # Connect to database
    # --------------------------------------------------------

    def connect(self):
        conn = sqlite3.connect(self.database_name)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    # --------------------------------------------------------
    # Create database tables
    # --------------------------------------------------------

    def init_db(self):

        conn = self.connect()
        cursor = conn.cursor()

        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL
            )
        """)

        # Substations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS substations (
                substation_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                region TEXT NOT NULL
            )
        """)

        # Lines table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lines (
                line_id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_substation TEXT,
                destination_substation TEXT,
                length_km REAL,
                voltage_kv REAL
            )
        """)

        # Outages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS outages (
                outage_id INTEGER PRIMARY KEY AUTOINCREMENT,
                substation_id INTEGER NOT NULL,
                reported_by INTEGER NOT NULL,
                description TEXT,
                severity TEXT,
                status TEXT DEFAULT 'Open',
                reported_at TEXT DEFAULT CURRENT_TIMESTAMP,
                resolved_at TEXT,
                FOREIGN KEY (substation_id)
                    REFERENCES substations(substation_id),
                FOREIGN KEY (reported_by)
                    REFERENCES users(user_id)
            )
        """)

        # Work orders table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS work_orders (
                work_order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                outage_id INTEGER NOT NULL,
                assigned_technician INTEGER,
                scheduled_date TEXT,
                status TEXT DEFAULT 'Pending',
                FOREIGN KEY (outage_id)
                    REFERENCES outages(outage_id),
                FOREIGN KEY (assigned_technician)
                    REFERENCES users(user_id)
            )
        """)

        # Complaints table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS complaints (
                complaint_id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                description TEXT NOT NULL,
                outage_id INTEGER,
                reported_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (outage_id)
                    REFERENCES outages(outage_id)
            )
        """)

        conn.commit()
        conn.close()

        self.create_default_users()

    # --------------------------------------------------------
    # Create default users
    # --------------------------------------------------------

    def create_default_users(self):

        conn = self.connect()
        cursor = conn.cursor()

        users = [
            ("admin", "admin123", "admin"),
            ("engineer", "engineer123", "engineer"),
            ("technician", "tech123", "technician"),
            ("customer_service", "service123", "customer_service")
        ]

        for username, password, role in users:

            password_hash = hashlib.sha256(
                password.encode()
            ).hexdigest()

            try:

                cursor.execute("""
                    INSERT INTO users
                    (username, password_hash, role)
                    VALUES (?, ?, ?)
                """, (
                    username,
                    password_hash,
                    role
                ))

            except sqlite3.IntegrityError:
                # User already exists
                pass

        conn.commit()
        conn.close()

    # --------------------------------------------------------
    # Import substations.csv
    # --------------------------------------------------------

    def import_substations(self, filename="substations.csv"):

        try:

            conn = self.connect()
            cursor = conn.cursor()

            with open(
                filename,
                "r",
                newline="",
                encoding="utf-8-sig"
            ) as file:

                reader = csv.DictReader(file)

                for row in reader:

                    substation_id = (
                        row.get("substation_id")
                        or row.get("Substation ID")
                        or row.get("ID")
                    )

                    name = (
                        row.get("name")
                        or row.get("Name")
                        or row.get("Substation")
                        or row.get("Substation Name")
                    )

                    region = (
                        row.get("region")
                        or row.get("Region")
                    )

                    if (
                        substation_id
                        and name
                        and region
                    ):

                        cursor.execute("""
                            INSERT OR REPLACE INTO substations
                            (
                                substation_id,
                                name,
                                region
                            )
                            VALUES (?, ?, ?)
                        """, (
                            int(substation_id),
                            name,
                            region
                        ))

            conn.commit()
            conn.close()

            print("Substations imported successfully.")

        except FileNotFoundError:

            print("substations.csv was not found.")

        except Exception as error:

            print(
                "Error importing substations:",
                error
            )

    # --------------------------------------------------------
    # Import lines.csv
    # --------------------------------------------------------

    def import_lines(self, filename="lines.csv"):

        try:

            conn = self.connect()
            cursor = conn.cursor()

            with open(
                filename,
                "r",
                newline="",
                encoding="utf-8-sig"
            ) as file:

                reader = csv.DictReader(file)

                for row in reader:

                    source = (
                        row.get("source_substation")
                        or row.get("Source Substation")
                        or row.get("Source")
                    )

                    destination = (
                        row.get("destination_substation")
                        or row.get("Destination Substation")
                        or row.get("Destination")
                    )

                    length = (
                        row.get("length_km")
                        or row.get("Length (km)")
                        or row.get("Length")
                    )

                    voltage = (
                        row.get("voltage_kv")
                        or row.get("Voltage (kV)")
                        or row.get("Voltage")
                    )

                    if source and destination:

                        cursor.execute("""
                            INSERT INTO lines
                            (
                                source_substation,
                                destination_substation,
                                length_km,
                                voltage_kv
                            )
                            VALUES (?, ?, ?, ?)
                        """, (
                            source,
                            destination,
                            length,
                            voltage
                        ))

            conn.commit()
            conn.close()

            print("Lines imported successfully.")

        except FileNotFoundError:

            print("lines.csv was not found.")

        except Exception as error:

            print(
                "Error importing lines:",
                error
            )


# ============================================================
# LOGIN WINDOW
# ============================================================

class LoginWindow(tk.Frame):

    def __init__(self, master, database, on_success):

        super().__init__(master)

        self.master = master
        self.database = database
        self.on_success = on_success

        master.title("GridCare-Lite - Login")
        master.geometry("450x350")

        # Title
        ttk.Label(
            self,
            text="GridCare-Lite",
            font=("Arial", 24, "bold")
        ).grid(
            row=0,
            column=0,
            columnspan=2,
            pady=20
        )

        # Username
        ttk.Label(
            self,
            text="Username:"
        ).grid(
            row=1,
            column=0,
            padx=8,
            pady=8,
            sticky="e"
        )

        self.username_entry = ttk.Entry(
            self,
            width=30
        )

        self.username_entry.grid(
            row=1,
            column=1,
            padx=8,
            pady=8
        )

        # Password
        ttk.Label(
            self,
            text="Password:"
        ).grid(
            row=2,
            column=0,
            padx=8,
            pady=8,
            sticky="e"
        )

        self.password_entry = ttk.Entry(
            self,
            show="*",
            width=30
        )

        self.password_entry.grid(
            row=2,
            column=1,
            padx=8,
            pady=8
        )

        # Login button
        ttk.Button(
            self,
            text="Log In",
            command=self.attempt_login
        ).grid(
            row=3,
            column=0,
            columnspan=2,
            pady=15
        )

        # Test accounts
        ttk.Label(
            self,
            text=(
                "Test Accounts\n\n"
                "admin / admin123\n"
                "engineer / engineer123\n"
                "technician / tech123\n"
                "customer_service / service123"
            ),
            justify="center"
        ).grid(
            row=4,
            column=0,
            columnspan=2,
            pady=10
        )

        self.pack(
            padx=20,
            pady=20
        )

    # --------------------------------------------------------
    # Check login details
    # --------------------------------------------------------

    def attempt_login(self):

        username = self.username_entry.get().strip()
        password = self.password_entry.get()

        if not username or not password:

            messagebox.showerror(
                "Login Failed",
                "Please enter both a username and password."
            )

            return

        password_hash = hashlib.sha256(
            password.encode()
        ).hexdigest()

        conn = self.database.connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT user_id, username, role
            FROM users
            WHERE username = ?
            AND password_hash = ?
        """, (
            username,
            password_hash
        ))

        user = cursor.fetchone()

        conn.close()

        if user is None:

            messagebox.showerror(
                "Login Failed",
                "Incorrect username or password."
            )

            return

        self.on_success(user)


# ============================================================
# MAIN DASHBOARD
# ============================================================

class Dashboard(tk.Frame):

    def __init__(self, master, database, user, logout):

        super().__init__(master)

        self.master = master
        self.database = database
        self.user = user
        self.logout = logout

        user_id = user[0]
        username = user[1]
        role = user[2]

        master.title(
            f"GridCare-Lite - Dashboard ({username})"
        )

        master.geometry("900x600")

        # Title
        ttk.Label(
            self,
            text="GridCare-Lite",
            font=("Arial", 24, "bold")
        ).pack(pady=15)

        ttk.Label(
            self,
            text=f"Welcome {username} | Role: {role}",
            font=("Arial", 12)
        ).pack(pady=5)

        # Buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(pady=25)

        # Engineer
        if role == "engineer":

            ttk.Button(
                button_frame,
                text="Report New Outage",
                command=self.new_outage
            ).pack(
                pady=8,
                ipadx=20
            )

            ttk.Button(
                button_frame,
                text="View Outages",
                command=self.outage_dashboard
            ).pack(
                pady=8,
                ipadx=20
            )

        # Admin
        elif role == "admin":

            ttk.Button(
                button_frame,
                text="View Outages",
                command=self.outage_dashboard
            ).pack(
                pady=8,
                ipadx=20
            )

            ttk.Button(
                button_frame,
                text="Assign Work Order",
                command=self.assign_work_order
            ).pack(
                pady=8,
                ipadx=20
            )

            ttk.Button(
                button_frame,
                text="Reports",
                command=self.reports
            ).pack(
                pady=8,
                ipadx=20
            )

        # Technician
        elif role == "technician":

            ttk.Button(
                button_frame,
                text="My Work Orders",
                command=self.technician_orders
            ).pack(
                pady=8,
                ipadx=20
            )

        # Customer service
        elif role == "customer_service":

            ttk.Button(
                button_frame,
                text="View Outages",
                command=self.outage_dashboard
            ).pack(
                pady=8,
                ipadx=20
            )

            ttk.Button(
                button_frame,
                text="Log Customer Complaint",
                command=self.complaint
            ).pack(
                pady=8,
                ipadx=20
            )

        # Logout
        ttk.Button(
            self,
            text="Log Out",
            command=self.logout
        ).pack(pady=20)

        self.pack(
            fill="both",
            expand=True
        )

    # ========================================================
    # OUTAGE DASHBOARD
    # ========================================================

    def outage_dashboard(self):

        window = tk.Toplevel(self.master)

        window.title(
            "GridCare-Lite - Outage Dashboard"
        )

        window.geometry(
            "850x500"
        )

        columns = (
            "outage_id",
            "substation",
            "region",
            "severity",
            "description",
            "status",
            "reported_at"
        )

        tree = ttk.Treeview(
            window,
            columns=columns,
            show="headings"
        )

        for column in columns:

            tree.heading(
                column,
                text=column.replace(
                    "_",
                    " "
                ).title()
            )

        tree.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )

        def load_outages():

            for row in tree.get_children():
                tree.delete(row)

            conn = self.database.connect()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    outages.outage_id,
                    substations.name,
                    substations.region,
                    outages.severity,
                    outages.description,
                    outages.status,
                    outages.reported_at

                FROM outages

                JOIN substations
                ON outages.substation_id =
                   substations.substation_id

                ORDER BY outages.reported_at DESC
            """)

            rows = cursor.fetchall()

            conn.close()

            for row in rows:

                tree.insert(
                    "",
                    "end",
                    values=row
                )

        ttk.Button(
            window,
            text="Refresh",
            command=load_outages
        ).pack(pady=5)

        load_outages()

    # ========================================================
    # NEW OUTAGE FORM
    # ========================================================

    def new_outage(self):

        window = tk.Toplevel(self.master)

        window.title(
            "GridCare-Lite - New Outage"
        )

        window.geometry(
            "500x450"
        )

        ttk.Label(
            window,
            text="Report New Outage",
            font=("Arial", 18, "bold")
        ).pack(pady=15)

        # Substation
        ttk.Label(
            window,
            text="Substation:"
        ).pack(pady=5)

        substation_box = ttk.Combobox(
            window,
            state="readonly",
            width=45
        )

        substation_box.pack()

        conn = self.database.connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT substation_id, name
            FROM substations
            ORDER BY name
        """)

        substations = cursor.fetchall()

        conn.close()

        substation_values = []

        for substation in substations:

            substation_values.append(
                f"{substation[0]} - {substation[1]}"
            )

        substation_box["values"] = substation_values

        if substation_values:
            substation_box.current(0)

        # Description
        ttk.Label(
            window,
            text="Description:"
        ).pack(pady=(15, 5))

        description = tk.Text(
            window,
            width=50,
            height=6
        )

        description.pack()

        # Severity
        ttk.Label(
            window,
            text="Severity:"
        ).pack(pady=(15, 5))

        severity_box = ttk.Combobox(
            window,
            values=[
                "Low",
                "Medium",
                "High",
                "Critical"
            ],
            state="readonly"
        )

        severity_box.pack()

        severity_box.current(0)

        # Save outage
        def save_outage():

            if not substation_box.get():

                messagebox.showerror(
                    "Error",
                    "Please select a substation."
                )

                return

            outage_description = (
                description.get(
                    "1.0",
                    tk.END
                ).strip()
            )

            if not outage_description:

                messagebox.showerror(
                    "Error",
                    "Please enter a description."
                )

                return

            selected_substation = (
                substation_box.get()
            )

            substation_id = int(
                selected_substation.split(" - ")[0]
            )

            severity = severity_box.get()

            conn = self.database.connect()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO outages
                (
                    substation_id,
                    reported_by,
                    description,
                    severity,
                    status
                )
                VALUES (?, ?, ?, ?, 'Open')
            """, (
                substation_id,
                self.user[0],
                outage_description,
                severity
            ))

            conn.commit()
            conn.close()

            messagebox.showinfo(
                "Success",
                "Outage successfully reported."
            )

            window.destroy()

        ttk.Button(
            window,
            text="Submit Outage",
            command=save_outage
        ).pack(pady=20)

    # ========================================================
    # WORK ORDER ASSIGNMENT
    # ========================================================

    def assign_work_order(self):

        window = tk.Toplevel(self.master)

        window.title(
            "GridCare-Lite - Work Order Assignment"
        )

        window.geometry(
            "550x450"
        )

        ttk.Label(
            window,
            text="Assign Work Order",
            font=("Arial", 18, "bold")
        ).pack(pady=15)

        # Outage
        ttk.Label(
            window,
            text="Select Outage:"
        ).pack(pady=5)

        outage_box = ttk.Combobox(
            window,
            state="readonly",
            width=50
        )

        outage_box.pack()

        conn = self.database.connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                outages.outage_id,
                substations.name,
                outages.severity

            FROM outages

            JOIN substations
            ON outages.substation_id =
               substations.substation_id

            WHERE outages.status != 'Resolved'
        """)

        outages = cursor.fetchall()

        conn.close()

        outage_values = []

        for outage in outages:

            outage_values.append(
                f"{outage[0]} - "
                f"{outage[1]} - "
                f"{outage[2]}"
            )

        outage_box["values"] = outage_values

        if outage_values:
            outage_box.current(0)

        # Technician
        ttk.Label(
            window,
            text="Assign Technician:"
        ).pack(pady=(15, 5))

        technician_box = ttk.Combobox(
            window,
            state="readonly",
            width=40
        )

        technician_box.pack()

        conn = self.database.connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT user_id, username
            FROM users
            WHERE role = 'technician'
        """)

        technicians = cursor.fetchall()

        conn.close()

        technician_values = []

        for technician in technicians:

            technician_values.append(
                f"{technician[0]} - {technician[1]}"
            )

        technician_box["values"] = technician_values

        if technician_values:
            technician_box.current(0)

        # Scheduled date
        ttk.Label(
            window,
            text="Scheduled Date (YYYY-MM-DD):"
        ).pack(pady=(15, 5))

        date_entry = ttk.Entry(
            window,
            width=30
        )

        date_entry.pack()

        # Save
        def save_work_order():

            if not outage_box.get():

                messagebox.showerror(
                    "Error",
                    "Please select an outage."
                )

                return

            if not technician_box.get():

                messagebox.showerror(
                    "Error",
                    "Please select a technician."
                )

                return

            scheduled_date = (
                date_entry.get().strip()
            )

            try:

                datetime.strptime(
                    scheduled_date,
                    "%Y-%m-%d"
                )

            except ValueError:

                messagebox.showerror(
                    "Error",
                    "Date must be YYYY-MM-DD."
                )

                return

            outage_id = int(
                outage_box.get().split(" - ")[0]
            )

            technician_id = int(
                technician_box.get().split(" - ")[0]
            )

            conn = self.database.connect()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO work_orders
                (
                    outage_id,
                    assigned_technician,
                    scheduled_date,
                    status
                )
                VALUES (?, ?, ?, 'Scheduled')
            """, (
                outage_id,
                technician_id,
                scheduled_date
            ))

            cursor.execute("""
                UPDATE outages
                SET status = 'In Progress'
                WHERE outage_id = ?
            """, (
                outage_id,
            ))

            conn.commit()
            conn.close()

            messagebox.showinfo(
                "Success",
                "Work order assigned successfully."
            )

            window.destroy()

        ttk.Button(
            window,
            text="Assign Work Order",
            command=save_work_order
        ).pack(pady=20)

    # ========================================================
    # TECHNICIAN WORK ORDERS
    # ========================================================

    def technician_orders(self):

        window = tk.Toplevel(self.master)

        window.title(
            "GridCare-Lite - Technician Work Orders"
        )

        window.geometry(
            "800x500"
        )

        ttk.Label(
            window,
            text="My Work Orders",
            font=("Arial", 18, "bold")
        ).pack(pady=15)

        columns = (
            "work_order_id",
            "outage_id",
            "substation",
            "scheduled_date",
            "status"
        )

        tree = ttk.Treeview(
            window,
            columns=columns,
            show="headings"
        )

        for column in columns:

            tree.heading(
                column,
                text=column.replace(
                    "_",
                    " "
                ).title()
            )

        tree.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )

        def load_orders():

            for item in tree.get_children():
                tree.delete(item)

            conn = self.database.connect()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    work_orders.work_order_id,
                    work_orders.outage_id,
                    substations.name,
                    work_orders.scheduled_date,
                    work_orders.status

                FROM work_orders

                JOIN outages
                ON work_orders.outage_id =
                   outages.outage_id

                JOIN substations
                ON outages.substation_id =
                   substations.substation_id

                WHERE work_orders.assigned_technician = ?
            """, (
                self.user[0],
            ))

            rows = cursor.fetchall()

            conn.close()

            for row in rows:

                tree.insert(
                    "",
                    "end",
                    values=row
                )

        def complete_work_order():

            selected = tree.selection()

            if not selected:

                messagebox.showerror(
                    "Error",
                    "Select a work order first."
                )

                return

            values = tree.item(
                selected[0]
            )["values"]

            work_order_id = values[0]
            outage_id = values[1]

            conn = self.database.connect()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE work_orders
                SET status = 'Completed'
                WHERE work_order_id = ?
                AND assigned_technician = ?
            """, (
                work_order_id,
                self.user[0]
            ))

            cursor.execute("""
                UPDATE outages
                SET status = 'Resolved',
                    resolved_at = CURRENT_TIMESTAMP
                WHERE outage_id = ?
            """, (
                outage_id,
            ))

            conn.commit()
            conn.close()

            messagebox.showinfo(
                "Success",
                "Work order completed and outage resolved."
            )

            load_orders()

        ttk.Button(
            window,
            text="Mark Selected Work Order Complete",
            command=complete_work_order
        ).pack(pady=10)

        load_orders()

    # ========================================================
    # CUSTOMER COMPLAINT
    # ========================================================

    def complaint(self):

        window = tk.Toplevel(self.master)

        window.title(
            "GridCare-Lite - Customer Complaint"
        )

        window.geometry(
            "500x450"
        )

        ttk.Label(
            window,
            text="Customer Complaint",
            font=("Arial", 18, "bold")
        ).pack(pady=15)

        # Customer name
        ttk.Label(
            window,
            text="Customer Name:"
        ).pack(pady=5)

        customer_name = ttk.Entry(
            window,
            width=40
        )

        customer_name.pack()

        # Outage ID
        ttk.Label(
            window,
            text="Known Outage ID (optional):"
        ).pack(
            pady=(15, 5)
        )

        outage_id_entry = ttk.Entry(
            window,
            width=30
        )

        outage_id_entry.pack()

        # Description
        ttk.Label(
            window,
            text="Complaint:"
        ).pack(
            pady=(15, 5)
        )

        complaint_text = tk.Text(
            window,
            width=50,
            height=7
        )

        complaint_text.pack()

        def save_complaint():

            name = customer_name.get().strip()

            description = (
                complaint_text.get(
                    "1.0",
                    tk.END
                ).strip()
            )

            outage_text = (
                outage_id_entry.get().strip()
            )

            if not name:

                messagebox.showerror(
                    "Error",
                    "Enter the customer's name."
                )

                return

            if not description:

                messagebox.showerror(
                    "Error",
                    "Enter the complaint."
                )

                return

            if outage_text == "":
                outage_id = None

            else:

                try:
                    outage_id = int(outage_text)

                except ValueError:

                    messagebox.showerror(
                        "Error",
                        "Outage ID must be a number."
                    )

                    return

            conn = self.database.connect()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO complaints
                (
                    customer_name,
                    description,
                    outage_id
                )
                VALUES (?, ?, ?)
            """, (
                name,
                description,
                outage_id
            ))

            conn.commit()
            conn.close()

            messagebox.showinfo(
                "Success",
                "Customer complaint recorded."
            )

            window.destroy()

        ttk.Button(
            window,
            text="Save Complaint",
            command=save_complaint
        ).pack(pady=20)

    # ========================================================
    # BASIC REPORTS
    # ========================================================

    def reports(self):

        window = tk.Toplevel(self.master)

        window.title(
            "GridCare-Lite - Reports"
        )

        window.geometry(
            "600x500"
        )

        ttk.Label(
            window,
            text="GridCare-Lite Reports",
            font=("Arial", 20, "bold")
        ).pack(pady=20)

        conn = self.database.connect()
        cursor = conn.cursor()

        # Total outages
        cursor.execute("""
            SELECT COUNT(*)
            FROM outages
        """)

        total_outages = cursor.fetchone()[0]

        # Open outages
        cursor.execute("""
            SELECT COUNT(*)
            FROM outages
            WHERE status != 'Resolved'
        """)

        open_outages = cursor.fetchone()[0]

        # Resolved outages
        cursor.execute("""
            SELECT COUNT(*)
            FROM outages
            WHERE status = 'Resolved'
        """)

        resolved_outages = cursor.fetchone()[0]

        # Average resolution time
        cursor.execute("""
            SELECT AVG(
                (
                    julianday(resolved_at)
                    -
                    julianday(reported_at)
                ) * 24
            )
            FROM outages
            WHERE resolved_at IS NOT NULL
        """)

        average_time = cursor.fetchone()[0]

        if average_time is None:
            average_time = 0

        conn.close()

        ttk.Label(
            window,
            text=f"Total Outages: {total_outages}",
            font=("Arial", 14)
        ).pack(pady=10)

        ttk.Label(
            window,
            text=f"Open Outages: {open_outages}",
            font=("Arial", 14)
        ).pack(pady=10)

        ttk.Label(
            window,
            text=f"Resolved Outages: {resolved_outages}",
            font=("Arial", 14)
        ).pack(pady=10)

        ttk.Label(
            window,
            text=(
                f"Average Resolution Time: "
                f"{average_time:.2f} hours"
            ),
            font=("Arial", 14)
        ).pack(pady=10)

        # Outages by region
        ttk.Label(
            window,
            text="Outages by Region",
            font=("Arial", 16, "bold")
        ).pack(pady=15)

        region_table = ttk.Treeview(
            window,
            columns=(
                "region",
                "count"
            ),
            show="headings"
        )

        region_table.heading(
            "region",
            text="Region"
        )

        region_table.heading(
            "count",
            text="Outages"
        )

        region_table.pack(
            fill="both",
            expand=True,
            padx=20
        )

        conn = self.database.connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                substations.region,
                COUNT(outages.outage_id)

            FROM outages

            JOIN substations
            ON outages.substation_id =
               substations.substation_id

            GROUP BY substations.region
        """)

        rows = cursor.fetchall()

        conn.close()

        for row in rows:

            region_table.insert(
                "",
                "end",
                values=row
            )


# ============================================================
# MAIN APPLICATION
# ============================================================

def main():

    # Create database
    database = Database()

    # Import reference data
    database.import_substations()
    database.import_lines()

    # Create main window
    root = tk.Tk()

    # --------------------------------------------------------
    # Show dashboard after successful login
    # --------------------------------------------------------

    def show_dashboard(user):

        # Remove current screen
        for widget in root.winfo_children():
            widget.destroy()

        # Create dashboard
        Dashboard(
            root,
            database,
            user,
            show_login
        )

    # --------------------------------------------------------
    # Show login screen
    # --------------------------------------------------------

    def show_login():

        for widget in root.winfo_children():
            widget.destroy()

        LoginWindow(
            root,
            database,
            show_dashboard
        )

    # Start with login
    show_login()

    # Start GUI loop
    root.mainloop()


# ============================================================
# PROGRAM START
# ============================================================

if __name__ == "__main__":
    main()