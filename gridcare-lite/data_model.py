import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import hashlib
import csv
import os
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

        # USERS
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL
            )
        """)

        # SUBSTATIONS
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS substations (
                substation_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                region TEXT NOT NULL
            )
        """)

        # LINES
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lines (
                line_id INTEGER PRIMARY KEY,
                source_substation_id INTEGER NOT NULL,
                destination_substation_id INTEGER NOT NULL,
                length_km REAL,
                voltage_kv REAL,

                FOREIGN KEY (source_substation_id)
                    REFERENCES substations(substation_id),

                FOREIGN KEY (destination_substation_id)
                    REFERENCES substations(substation_id)
            )
        """)

        # OUTAGES
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS outages (
                outage_id INTEGER PRIMARY KEY AUTOINCREMENT,

                substation_id INTEGER NOT NULL,

                reported_by INTEGER NOT NULL,

                description TEXT NOT NULL,

                severity TEXT NOT NULL,

                status TEXT DEFAULT 'Open',

                reported_at TEXT DEFAULT CURRENT_TIMESTAMP,

                resolved_at TEXT,

                FOREIGN KEY (substation_id)
                    REFERENCES substations(substation_id),

                FOREIGN KEY (reported_by)
                    REFERENCES users(user_id)
            )
        """)

        # WORK ORDERS
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

        # COMPLAINTS
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

    # ========================================================
    # DEFAULT USERS
    # ========================================================

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
                pass

        conn.commit()
        conn.close()

    # ========================================================
    # IMPORT SUBSTATIONS CSV
    # ========================================================

    def import_substations(self, filename):

        conn = self.connect()
        cursor = conn.cursor()

        imported = 0
        skipped = 0

        try:

            with open(
                filename,
                "r",
                newline="",
                encoding="utf-8-sig"
            ) as file:

                reader = csv.DictReader(file)

                print("Substation CSV columns:")
                print(reader.fieldnames)

                for row in reader:

                    # Try different possible column names

                    substation_id = (
                        row.get("substation_id")
                        or row.get("Substation ID")
                        or row.get("ID")
                        or row.get("id")
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

                    # Make sure all required information exists

                    if not substation_id or not name or not region:

                        skipped += 1
                        continue

                    try:

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
                            name.strip(),
                            region.strip()
                        ))

                        imported += 1

                    except Exception as error:

                        print(
                            "Could not import substation:",
                            error
                        )

                        skipped += 1

            conn.commit()

            return imported, skipped

        except FileNotFoundError:

            raise FileNotFoundError(
                "The substations.csv file could not be found."
            )

        finally:

            conn.close()

    # ========================================================
    # IMPORT LINES CSV
    # ========================================================

    def import_lines(self, filename):

        conn = self.connect()
        cursor = conn.cursor()

        imported = 0
        skipped = 0

        try:

            with open(
                filename,
                "r",
                newline="",
                encoding="utf-8-sig"
            ) as file:

                reader = csv.DictReader(file)

                print("Line CSV columns:")
                print(reader.fieldnames)

                for row in reader:

                    source = (
                        row.get("source_substation_id")
                        or row.get("Source Substation ID")
                        or row.get("Source ID")
                        or row.get("Source")
                    )

                    destination = (
                        row.get("destination_substation_id")
                        or row.get("Destination Substation ID")
                        or row.get("Destination ID")
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

                    if not source or not destination:

                        skipped += 1
                        continue

                    try:

                        source_id = int(source)
                        destination_id = int(destination)

                        # Check that both substations exist

                        cursor.execute("""
                            SELECT substation_id
                            FROM substations
                            WHERE substation_id = ?
                        """, (source_id,))

                        source_exists = cursor.fetchone()

                        cursor.execute("""
                            SELECT substation_id
                            FROM substations
                            WHERE substation_id = ?
                        """, (destination_id,))

                        destination_exists = cursor.fetchone()

                        if not source_exists or not destination_exists:

                            print(
                                f"Skipping line: "
                                f"{source_id} -> {destination_id} "
                                f"(substation does not exist)"
                            )

                            skipped += 1
                            continue

                        cursor.execute("""
                            INSERT INTO lines
                            (
                                source_substation_id,
                                destination_substation_id,
                                length_km,
                                voltage_kv
                            )

                            VALUES (?, ?, ?, ?)
                        """, (
                            source_id,
                            destination_id,
                            length,
                            voltage
                        ))

                        imported += 1

                    except Exception as error:

                        print(
                            "Could not import line:",
                            error
                        )

                        skipped += 1

            conn.commit()

            return imported, skipped

        except FileNotFoundError:

            raise FileNotFoundError(
                "The lines.csv file could not be found."
            )

        finally:

            conn.close()

    # ========================================================
    # GET ALL SUBSTATIONS
    # ========================================================

    def get_substations(self):

        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                substation_id,
                name,
                region

            FROM substations

            ORDER BY name
        """)

        substations = cursor.fetchall()

        conn.close()

        return substations

    # ========================================================
    # CREATE OUTAGE
    # ========================================================

    def create_outage(
        self,
        substation_id,
        reported_by,
        description,
        severity
    ):

        conn = self.connect()
        cursor = conn.cursor()

        try:

            cursor.execute("""
                INSERT INTO outages
                (
                    substation_id,
                    reported_by,
                    description,
                    severity
                )

                VALUES (?, ?, ?, ?)
            """, (
                substation_id,
                reported_by,
                description,
                severity
            ))

            conn.commit()

        except sqlite3.IntegrityError:

            conn.rollback()

            raise ValueError(
                "The selected substation does not exist."
            )

        finally:

            conn.close()


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

        ttk.Label(
            self,
            text="Username:"
        ).grid(
            row=1,
            column=0,
            padx=8,
            pady=8
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

        ttk.Label(
            self,
            text="Password:"
        ).grid(
            row=2,
            column=0,
            padx=8,
            pady=8
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
    # LOGIN
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
            SELECT
                user_id,
                username,
                role

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
# DASHBOARD
# ============================================================

class Dashboard(tk.Frame):

    def __init__(
        self,
        master,
        database,
        user,
        logout
    ):

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

        master.geometry("800x600")

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

        # ----------------------------------------------------
        # ADMIN
        # ----------------------------------------------------

        if role == "admin":

            ttk.Button(
                self,
                text="Import Substations",
                command=self.import_substations
            ).pack(
                pady=8,
                ipadx=20
            )

            ttk.Button(
                self,
                text="Import Lines",
                command=self.import_lines
            ).pack(
                pady=8,
                ipadx=20
            )

            ttk.Button(
                self,
                text="View Substations",
                command=self.view_substations
            ).pack(
                pady=8,
                ipadx=20
            )

            ttk.Button(
                self,
                text="View Outages",
                command=self.view_outages
            ).pack(
                pady=8,
                ipadx=20
            )

        # ----------------------------------------------------
        # ENGINEER
        # ----------------------------------------------------

        elif role == "engineer":

            ttk.Button(
                self,
                text="Report New Outage",
                command=self.new_outage
            ).pack(
                pady=8,
                ipadx=20
            )

            ttk.Button(
                self,
                text="View Outages",
                command=self.view_outages
            ).pack(
                pady=8,
                ipadx=20
            )

        # ----------------------------------------------------
        # TECHNICIAN
        # ----------------------------------------------------

        elif role == "technician":

            ttk.Label(
                self,
                text="Technician Work Orders"
            ).pack(pady=20)

        # ----------------------------------------------------
        # CUSTOMER SERVICE
        # ----------------------------------------------------

        elif role == "customer_service":

            ttk.Button(
                self,
                text="View Outages",
                command=self.view_outages
            ).pack(
                pady=8,
                ipadx=20
            )

        # ----------------------------------------------------
        # LOGOUT
        # ----------------------------------------------------

        ttk.Button(
            self,
            text="Log Out",
            command=self.logout
        ).pack(pady=30)

        self.pack(
            fill="both",
            expand=True
        )

    # ========================================================
    # IMPORT SUBSTATIONS
    # ========================================================

    def import_substations(self):

        filename = filedialog.askopenfilename(
            title="Select substations.csv",
            filetypes=[
                ("CSV files", "*.csv"),
                ("All files", "*.*")
            ]
        )

        if not filename:
            return

        try:

            imported, skipped = (
                self.database.import_substations(filename)
            )

            messagebox.showinfo(
                "Import Complete",
                f"Substations imported: {imported}\n"
                f"Rows skipped: {skipped}"
            )

        except Exception as error:

            messagebox.showerror(
                "Import Error",
                str(error)
            )

    # ========================================================
    # IMPORT LINES
    # ========================================================

    def import_lines(self):

        filename = filedialog.askopenfilename(
            title="Select lines.csv",
            filetypes=[
                ("CSV files", "*.csv"),
                ("All files", "*.*")
            ]
        )

        if not filename:
            return

        try:

            imported, skipped = (
                self.database.import_lines(filename)
            )

            messagebox.showinfo(
                "Import Complete",
                f"Lines imported: {imported}\n"
                f"Rows skipped: {skipped}"
            )

        except Exception as error:

            messagebox.showerror(
                "Import Error",
                str(error)
            )

    # ========================================================
    # VIEW SUBSTATIONS
    # ========================================================

    def view_substations(self):

        window = tk.Toplevel(self.master)

        window.title("Substations")

        window.geometry("600x400")

        tree = ttk.Treeview(
            window,
            columns=(
                "id",
                "name",
                "region"
            ),
            show="headings"
        )

        tree.heading(
            "id",
            text="ID"
        )

        tree.heading(
            "name",
            text="Substation"
        )

        tree.heading(
            "region",
            text="Region"
        )

        tree.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )

        substations = (
            self.database.get_substations()
        )

        for substation in substations:

            tree.insert(
                "",
                "end",
                values=substation
            )

    # ========================================================
    # REPORT NEW OUTAGE
    # ========================================================

    def new_outage(self):

        window = tk.Toplevel(self.master)

        window.title(
            "Report New Outage"
        )

        window.geometry(
            "500x500"
        )

        ttk.Label(
            window,
            text="Report New Outage",
            font=("Arial", 18, "bold")
        ).pack(pady=20)

        # ----------------------------------------------------
        # SUBSTATION
        # ----------------------------------------------------

        ttk.Label(
            window,
            text="Substation:"
        ).pack(pady=5)

        substations = (
            self.database.get_substations()
        )

        substation_options = []

        for substation_id, name, region in substations:

            substation_options.append(
                f"{substation_id} - {name} ({region})"
            )

        substation_combo = ttk.Combobox(
            window,
            values=substation_options,
            state="readonly",
            width=40
        )

        substation_combo.pack(pady=5)

        # ----------------------------------------------------
        # SEVERITY
        # ----------------------------------------------------

        ttk.Label(
            window,
            text="Severity:"
        ).pack(pady=5)

        severity_combo = ttk.Combobox(
            window,
            values=[
                "Low",
                "Medium",
                "High",
                "Critical"
            ],
            state="readonly"
        )

        severity_combo.pack(pady=5)

        # ----------------------------------------------------
        # DESCRIPTION
        # ----------------------------------------------------

        ttk.Label(
            window,
            text="Description:"
        ).pack(pady=5)

        description = tk.Text(
            window,
            width=45,
            height=8
        )

        description.pack(pady=5)

        # ----------------------------------------------------
        # SAVE OUTAGE
        # ----------------------------------------------------

        def save_outage():

            selected = substation_combo.get()

            severity = severity_combo.get()

            description_text = (
                description.get(
                    "1.0",
                    tk.END
                ).strip()
            )

            if not selected:

                messagebox.showerror(
                    "Error",
                    "Please select a substation."
                )

                return

            if not severity:

                messagebox.showerror(
                    "Error",
                    "Please select the severity."
                )

                return

            if not description_text:

                messagebox.showerror(
                    "Error",
                    "Please enter a description."
                )

                return

            # Extract substation ID

            substation_id = int(
                selected.split(" - ")[0]
            )

            try:

                self.database.create_outage(
                    substation_id,
                    self.user[0],
                    description_text,
                    severity
                )

                messagebox.showinfo(
                    "Success",
                    "Outage successfully reported."
                )

                window.destroy()

            except Exception as error:

                messagebox.showerror(
                    "Error",
                    str(error)
                )

        ttk.Button(
            window,
            text="Save Outage",
            command=save_outage
        ).pack(pady=20)

    # ========================================================
    # VIEW OUTAGES
    # ========================================================

    def view_outages(self):

        window = tk.Toplevel(self.master)

        window.title(
            "Outages"
        )

        window.geometry(
            "900x400"
        )

        tree = ttk.Treeview(
            window,
            columns=(
                "id",
                "substation",
                "severity",
                "status",
                "description"
            ),
            show="headings"
        )

        tree.heading(
            "id",
            text="ID"
        )

        tree.heading(
            "substation",
            text="Substation"
        )

        tree.heading(
            "severity",
            text="Severity"
        )

        tree.heading(
            "status",
            text="Status"
        )

        tree.heading(
            "description",
            text="Description"
        )

        tree.column(
            "description",
            width=350
        )

        tree.pack(
            fill="both",
            expand=True
        )

        conn = self.database.connect()

        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                o.outage_id,
                s.name,
                o.severity,
                o.status,
                o.description

            FROM outages o

            JOIN substations s
                ON o.substation_id = s.substation_id

            ORDER BY o.outage_id DESC
        """)

        outages = cursor.fetchall()

        conn.close()

        for outage in outages:

            tree.insert(
                "",
                "end",
                values=outage
            )


# ============================================================
# MAIN APPLICATION
# ============================================================

class GridCareApp:

    def __init__(self):

        self.root = tk.Tk()

        self.database = Database()

        self.current_frame = None

        self.show_login()

    # --------------------------------------------------------
    # SHOW LOGIN
    # --------------------------------------------------------

    def show_login(self):

        if self.current_frame:

            self.current_frame.destroy()

        self.current_frame = LoginWindow(
            self.root,
            self.database,
            self.login_success
        )

    # --------------------------------------------------------
    # LOGIN SUCCESS
    # --------------------------------------------------------

    def login_success(self, user):

        if self.current_frame:

            self.current_frame.destroy()

        self.current_frame = Dashboard(
            self.root,
            self.database,
            user,
            self.logout
        )

    # --------------------------------------------------------
    # LOGOUT
    # --------------------------------------------------------

    def logout(self):

        self.show_login()

    # --------------------------------------------------------
    # RUN
    # --------------------------------------------------------

    def run(self):

        self.root.mainloop()


# ============================================================
# START PROGRAM
# ============================================================

if __name__ == "__main__":

    app = GridCareApp()

    app.run()