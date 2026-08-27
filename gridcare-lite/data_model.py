import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
import bcrypt
import csv
from datetime import datetime
from pathlib import Path


SCHEMA_PATH = Path(__file__).resolve().parent / "db" / "schema.sql"
GRID_DATA_DIR = Path(__file__).resolve().parent.parent / "grid-analysis" / "data"

DEFAULT_USERS = [
    ("admin", "admin123", "admin"),
    ("engineer", "engineer123", "engineer"),
    ("technician", "tech123", "technician"),
    ("customer_service", "service123", "customer_service"),
]


# handles the database stuff
class Database:

    def __init__(self, database_name="gridcare.db"):
        self.database_name = database_name
        self.init_db()

    def connect(self):
        conn = sqlite3.connect(self.database_name)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def init_db(self):
        conn = self.connect()
        try:
            conn.executescript(SCHEMA_PATH.read_text())
            conn.commit()
        finally:
            conn.close()

        self.create_default_users()

    def create_default_users(self):
        conn = self.connect()
        cursor = conn.cursor()

        for username, password, role in DEFAULT_USERS:
            password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

            try:
                cursor.execute(
                    "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                    (username, password_hash.decode("utf-8"), role),
                )
            except sqlite3.IntegrityError:
                pass  # user already exists

        conn.commit()
        conn.close()

    def import_substations(self, filename=None):
        filename = filename or (GRID_DATA_DIR / "substations.csv")

        try:
            conn = self.connect()
            cursor = conn.cursor()

            with open(filename, "r", newline="", encoding="utf-8-sig") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    substation_id = row.get("Substation ID") or row.get("substation_id") or row.get("ID")
                    name = row.get("Name") or row.get("name") or row.get("Substation")
                    region = row.get("Region") or row.get("region")

                    if substation_id and name and region:
                        cursor.execute(
                            "INSERT OR REPLACE INTO substations (substation_id, name, region) VALUES (?, ?, ?)",
                            (int(substation_id), name, region),
                        )

            conn.commit()
            conn.close()

        except FileNotFoundError:
            print(f"{filename} was not found.")
        except (sqlite3.Error, ValueError) as error:
            print("Error importing substations:", error)

    def import_lines(self, filename=None):
        filename = filename or (GRID_DATA_DIR / "lines.csv")

        try:
            conn = self.connect()
            cursor = conn.cursor()

            with open(filename, "r", newline="", encoding="utf-8-sig") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    source = row.get("Source Substation") or row.get("source_substation")
                    destination = row.get("Destination Substation") or row.get("destination_substation")
                    length = row.get("Length (km)") or row.get("length_km")
                    voltage = row.get("Voltage (kV)") or row.get("voltage_kv")

                    if source and destination:
                        cursor.execute(
                            """INSERT INTO lines
                               (source_substation, destination_substation, length_km, voltage_kv)
                               VALUES (?, ?, ?, ?)""",
                            (source, destination, length, voltage),
                        )

            conn.commit()
            conn.close()

        except FileNotFoundError:
            print(f"{filename} was not found.")
        except (sqlite3.Error, ValueError) as error:
            print("Error importing lines:", error)

    def verify_login(self, username, password):
        # checks the password, returns the user or none
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_id, username, role, password_hash FROM users WHERE username = ?",
            (username,),
        )
        row = cursor.fetchone()
        conn.close()

        if row is None:
            return None

        user_id, db_username, role, password_hash = row
        if not bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8")):
            return None

        return (user_id, db_username, role)

    def substation_exists(self, substation_id):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM substations WHERE substation_id = ?", (substation_id,))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists

    def log_outage(self, substation_id, reported_by, description, severity):
        if not self.substation_exists(substation_id):
            raise ValueError(f"Substation {substation_id} does not exist.")
        if not description or not description.strip():
            raise ValueError("Description is required.")

        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO outages (substation_id, reported_by, description, severity, status)
               VALUES (?, ?, ?, ?, 'Open')""",
            (substation_id, reported_by, description.strip(), severity),
        )
        conn.commit()
        outage_id = cursor.lastrowid
        conn.close()
        return outage_id

    def list_outages(self):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT outages.outage_id, substations.name, substations.region,
                   outages.severity, outages.description, outages.status, outages.reported_at
            FROM outages
            JOIN substations ON outages.substation_id = substations.substation_id
            ORDER BY outages.reported_at DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        return rows

    def _outage_status(self, outage_id):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM outages WHERE outage_id = ?", (outage_id,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None

    def _user_has_role(self, user_id, role):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE user_id = ? AND role = ?", (user_id, role))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists

    def assign_work_order(self, outage_id, technician_id, scheduled_date):
        status = self._outage_status(outage_id)
        if status is None:
            raise ValueError(f"Outage {outage_id} does not exist.")
        if status == "Resolved":
            raise ValueError(f"Outage {outage_id} is already resolved.")
        if not self._user_has_role(technician_id, "technician"):
            raise ValueError(f"User {technician_id} is not a technician.")

        try:
            datetime.strptime(scheduled_date, "%Y-%m-%d")
        except (ValueError, TypeError):
            raise ValueError("Scheduled date must be in YYYY-MM-DD format.")

        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO work_orders (outage_id, assigned_technician, scheduled_date, status)
               VALUES (?, ?, ?, 'Scheduled')""",
            (outage_id, technician_id, scheduled_date),
        )
        cursor.execute(
            "UPDATE outages SET status = 'In Progress' WHERE outage_id = ?",
            (outage_id,),
        )
        conn.commit()
        work_order_id = cursor.lastrowid
        conn.close()
        return work_order_id

    def list_work_orders_for_technician(self, technician_id):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT work_orders.work_order_id, work_orders.outage_id, substations.name,
                   work_orders.scheduled_date, work_orders.status
            FROM work_orders
            JOIN outages ON work_orders.outage_id = outages.outage_id
            JOIN substations ON outages.substation_id = substations.substation_id
            WHERE work_orders.assigned_technician = ?
        """, (technician_id,))
        rows = cursor.fetchall()
        conn.close()
        return rows

    def complete_work_order(self, work_order_id, technician_id):
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT outage_id FROM work_orders WHERE work_order_id = ? AND assigned_technician = ?",
            (work_order_id, technician_id),
        )
        row = cursor.fetchone()
        if row is None:
            conn.close()
            raise ValueError("Work order not found for this technician.")
        outage_id = row[0]

        cursor.execute(
            "UPDATE work_orders SET status = 'Completed' WHERE work_order_id = ?",
            (work_order_id,),
        )
        cursor.execute(
            "UPDATE outages SET status = 'Resolved', resolved_at = CURRENT_TIMESTAMP WHERE outage_id = ?",
            (outage_id,),
        )
        conn.commit()
        conn.close()
        return outage_id

    def log_complaint(self, customer_name, description, outage_id=None):
        if not customer_name or not customer_name.strip():
            raise ValueError("Customer name is required.")
        if not description or not description.strip():
            raise ValueError("Complaint description is required.")
        if outage_id is not None:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM outages WHERE outage_id = ?", (outage_id,))
            exists = cursor.fetchone() is not None
            conn.close()
            if not exists:
                raise ValueError(f"Outage {outage_id} does not exist.")

        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO complaints (customer_name, description, outage_id) VALUES (?, ?, ?)",
            (customer_name.strip(), description.strip(), outage_id),
        )
        conn.commit()
        complaint_id = cursor.lastrowid
        conn.close()
        return complaint_id

    def get_reports(self):
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM outages")
        total_outages = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM outages WHERE status != 'Resolved'")
        open_outages = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM outages WHERE status = 'Resolved'")
        resolved_outages = cursor.fetchone()[0]

        cursor.execute("""
            SELECT AVG((julianday(resolved_at) - julianday(reported_at)) * 24)
            FROM outages WHERE resolved_at IS NOT NULL
        """)
        average_hours = cursor.fetchone()[0] or 0.0

        cursor.execute("""
            SELECT substations.region, COUNT(outages.outage_id)
            FROM outages
            JOIN substations ON outages.substation_id = substations.substation_id
            GROUP BY substations.region
        """)
        by_region = cursor.fetchall()

        conn.close()

        return {
            "total_outages": total_outages,
            "open_outages": open_outages,
            "resolved_outages": resolved_outages,
            "average_resolution_hours": average_hours,
            "outages_by_region": by_region,
        }


# the login screen
class LoginWindow(tk.Frame):

    def __init__(self, master, database, on_success):
        super().__init__(master)

        self.master = master
        self.database = database
        self.on_success = on_success

        master.title("GridCare-Lite - Login")
        master.geometry("450x350")

        ttk.Label(self, text="GridCare-Lite", font=("Arial", 24, "bold")).grid(
            row=0, column=0, columnspan=2, pady=20)

        ttk.Label(self, text="Username:").grid(row=1, column=0, padx=8, pady=8, sticky="e")
        self.username_entry = ttk.Entry(self, width=30)
        self.username_entry.grid(row=1, column=1, padx=8, pady=8)

        ttk.Label(self, text="Password:").grid(row=2, column=0, padx=8, pady=8, sticky="e")
        self.password_entry = ttk.Entry(self, show="*", width=30)
        self.password_entry.grid(row=2, column=1, padx=8, pady=8)

        ttk.Button(self, text="Log In", command=self.attempt_login).grid(
            row=3, column=0, columnspan=2, pady=15)

        ttk.Label(
            self,
            text=(
                "Test Accounts\n\n"
                "admin / admin123\n"
                "engineer / engineer123\n"
                "technician / tech123\n"
                "customer_service / service123"
            ),
            justify="center",
        ).grid(row=4, column=0, columnspan=2, pady=10)

        self.pack(padx=20, pady=20)

    def attempt_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()

        if not username or not password:
            messagebox.showerror("Login Failed", "Please enter both a username and password.")
            return

        try:
            user = self.database.verify_login(username, password)
        except sqlite3.Error as error:
            messagebox.showerror("Database Error", f"Could not verify credentials: {error}")
            return

        if user is None:
            messagebox.showerror("Login Failed", "Incorrect username or password.")
            return

        self.on_success(user)


# the main screen after logging in
class Dashboard(tk.Frame):

    def __init__(self, master, database, user, logout):
        super().__init__(master)

        self.master = master
        self.database = database
        self.user = user
        self.logout = logout

        user_id, username, role = user

        master.title(f"GridCare-Lite - Dashboard ({username})")
        master.geometry("900x600")

        ttk.Label(self, text="GridCare-Lite", font=("Arial", 24, "bold")).pack(pady=15)
        ttk.Label(self, text=f"Welcome {username} | Role: {role}", font=("Arial", 12)).pack(pady=5)

        button_frame = ttk.Frame(self)
        button_frame.pack(pady=25)

        if role == "engineer":
            ttk.Button(button_frame, text="Report New Outage", command=self.new_outage).pack(pady=8, ipadx=20)
            ttk.Button(button_frame, text="View Outages", command=self.outage_dashboard).pack(pady=8, ipadx=20)

        elif role == "admin":
            ttk.Button(button_frame, text="View Outages", command=self.outage_dashboard).pack(pady=8, ipadx=20)
            ttk.Button(button_frame, text="Assign Work Order", command=self.assign_work_order).pack(pady=8, ipadx=20)
            ttk.Button(button_frame, text="Reports", command=self.reports).pack(pady=8, ipadx=20)

        elif role == "technician":
            ttk.Button(button_frame, text="My Work Orders", command=self.technician_orders).pack(pady=8, ipadx=20)

        elif role == "customer_service":
            ttk.Button(button_frame, text="View Outages", command=self.outage_dashboard).pack(pady=8, ipadx=20)
            ttk.Button(button_frame, text="Log Customer Complaint", command=self.complaint).pack(pady=8, ipadx=20)

        ttk.Button(self, text="Log Out", command=self.logout).pack(pady=20)

        self.pack(fill="both", expand=True)

    def outage_dashboard(self):
        window = tk.Toplevel(self.master)
        window.title("GridCare-Lite - Outage Dashboard")
        window.geometry("850x500")

        columns = ("outage_id", "substation", "region", "severity", "description", "status", "reported_at")
        tree = ttk.Treeview(window, columns=columns, show="headings")
        for column in columns:
            tree.heading(column, text=column.replace("_", " ").title())
        tree.pack(fill="both", expand=True, padx=10, pady=10)

        def load_outages():
            for row in tree.get_children():
                tree.delete(row)
            for row in self.database.list_outages():
                tree.insert("", "end", values=row)

        ttk.Button(window, text="Refresh", command=load_outages).pack(pady=5)
        load_outages()

    def new_outage(self):
        window = tk.Toplevel(self.master)
        window.title("GridCare-Lite - New Outage")
        window.geometry("500x450")

        ttk.Label(window, text="Report New Outage", font=("Arial", 18, "bold")).pack(pady=15)

        ttk.Label(window, text="Substation:").pack(pady=5)
        substation_box = ttk.Combobox(window, state="readonly", width=45)
        substation_box.pack()

        conn = self.database.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT substation_id, name FROM substations ORDER BY name")
        substations = cursor.fetchall()
        conn.close()

        substation_values = [f"{sid} - {name}" for sid, name in substations]
        substation_box["values"] = substation_values
        if substation_values:
            substation_box.current(0)

        ttk.Label(window, text="Description:").pack(pady=(15, 5))
        description = tk.Text(window, width=50, height=6)
        description.pack()

        ttk.Label(window, text="Severity:").pack(pady=(15, 5))
        severity_box = ttk.Combobox(window, values=["Low", "Medium", "High", "Critical"], state="readonly")
        severity_box.pack()
        severity_box.current(0)

        def save_outage():
            if not substation_box.get():
                messagebox.showerror("Error", "Please select a substation.")
                return

            outage_description = description.get("1.0", tk.END).strip()
            substation_id = int(substation_box.get().split(" - ")[0])
            severity = severity_box.get()

            try:
                self.database.log_outage(substation_id, self.user[0], outage_description, severity)
            except ValueError as error:
                messagebox.showerror("Error", str(error))
                return
            except sqlite3.Error as error:
                messagebox.showerror("Database Error", f"Could not save the outage: {error}")
                return

            messagebox.showinfo("Success", "Outage successfully reported.")
            window.destroy()

        ttk.Button(window, text="Submit Outage", command=save_outage).pack(pady=20)

    def assign_work_order(self):
        window = tk.Toplevel(self.master)
        window.title("GridCare-Lite - Work Order Assignment")
        window.geometry("550x450")

        ttk.Label(window, text="Assign Work Order", font=("Arial", 18, "bold")).pack(pady=15)

        ttk.Label(window, text="Select Outage:").pack(pady=5)
        outage_box = ttk.Combobox(window, state="readonly", width=50)
        outage_box.pack()

        conn = self.database.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT outages.outage_id, substations.name, outages.severity
            FROM outages
            JOIN substations ON outages.substation_id = substations.substation_id
            WHERE outages.status != 'Resolved'
        """)
        outages = cursor.fetchall()
        conn.close()

        outage_values = [f"{oid} - {name} - {severity}" for oid, name, severity in outages]
        outage_box["values"] = outage_values
        if outage_values:
            outage_box.current(0)

        ttk.Label(window, text="Assign Technician:").pack(pady=(15, 5))
        technician_box = ttk.Combobox(window, state="readonly", width=40)
        technician_box.pack()

        conn = self.database.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, username FROM users WHERE role = 'technician'")
        technicians = cursor.fetchall()
        conn.close()

        technician_values = [f"{tid} - {name}" for tid, name in technicians]
        technician_box["values"] = technician_values
        if technician_values:
            technician_box.current(0)

        ttk.Label(window, text="Scheduled Date (YYYY-MM-DD):").pack(pady=(15, 5))
        date_entry = ttk.Entry(window, width=30)
        date_entry.pack()

        def save_work_order():
            if not outage_box.get():
                messagebox.showerror("Error", "Please select an outage.")
                return
            if not technician_box.get():
                messagebox.showerror("Error", "Please select a technician.")
                return

            outage_id = int(outage_box.get().split(" - ")[0])
            technician_id = int(technician_box.get().split(" - ")[0])
            scheduled_date = date_entry.get().strip()

            try:
                self.database.assign_work_order(outage_id, technician_id, scheduled_date)
            except ValueError as error:
                messagebox.showerror("Error", str(error))
                return
            except sqlite3.Error as error:
                messagebox.showerror("Database Error", f"Could not assign the work order: {error}")
                return

            messagebox.showinfo("Success", "Work order assigned successfully.")
            window.destroy()

        ttk.Button(window, text="Assign Work Order", command=save_work_order).pack(pady=20)

    def technician_orders(self):
        window = tk.Toplevel(self.master)
        window.title("GridCare-Lite - Technician Work Orders")
        window.geometry("800x500")

        ttk.Label(window, text="My Work Orders", font=("Arial", 18, "bold")).pack(pady=15)

        columns = ("work_order_id", "outage_id", "substation", "scheduled_date", "status")
        tree = ttk.Treeview(window, columns=columns, show="headings")
        for column in columns:
            tree.heading(column, text=column.replace("_", " ").title())
        tree.pack(fill="both", expand=True, padx=10, pady=10)

        def load_orders():
            for item in tree.get_children():
                tree.delete(item)
            for row in self.database.list_work_orders_for_technician(self.user[0]):
                tree.insert("", "end", values=row)

        def complete_selected_work_order():
            selected = tree.selection()
            if not selected:
                messagebox.showerror("Error", "Select a work order first.")
                return

            work_order_id = tree.item(selected[0])["values"][0]

            try:
                self.database.complete_work_order(work_order_id, self.user[0])
            except ValueError as error:
                messagebox.showerror("Error", str(error))
                return
            except sqlite3.Error as error:
                messagebox.showerror("Database Error", f"Could not complete the work order: {error}")
                return

            messagebox.showinfo("Success", "Work order completed and outage resolved.")
            load_orders()

        ttk.Button(window, text="Mark Selected Work Order Complete", command=complete_selected_work_order).pack(pady=10)
        load_orders()

    def complaint(self):
        window = tk.Toplevel(self.master)
        window.title("GridCare-Lite - Customer Complaint")
        window.geometry("500x450")

        ttk.Label(window, text="Customer Complaint", font=("Arial", 18, "bold")).pack(pady=15)

        ttk.Label(window, text="Customer Name:").pack(pady=5)
        customer_name = ttk.Entry(window, width=40)
        customer_name.pack()

        ttk.Label(window, text="Known Outage ID (optional):").pack(pady=(15, 5))
        outage_id_entry = ttk.Entry(window, width=30)
        outage_id_entry.pack()

        ttk.Label(window, text="Complaint:").pack(pady=(15, 5))
        complaint_text = tk.Text(window, width=50, height=7)
        complaint_text.pack()

        def save_complaint():
            name = customer_name.get().strip()
            description = complaint_text.get("1.0", tk.END).strip()
            outage_text = outage_id_entry.get().strip()

            outage_id = None
            if outage_text:
                try:
                    outage_id = int(outage_text)
                except ValueError:
                    messagebox.showerror("Error", "Outage ID must be a number.")
                    return

            try:
                self.database.log_complaint(name, description, outage_id)
            except ValueError as error:
                messagebox.showerror("Error", str(error))
                return
            except sqlite3.Error as error:
                messagebox.showerror("Database Error", f"Could not save the complaint: {error}")
                return

            messagebox.showinfo("Success", "Customer complaint recorded.")
            window.destroy()

        ttk.Button(window, text="Save Complaint", command=save_complaint).pack(pady=20)

    def reports(self):
        window = tk.Toplevel(self.master)
        window.title("GridCare-Lite - Reports")
        window.geometry("600x500")

        ttk.Label(window, text="GridCare-Lite Reports", font=("Arial", 20, "bold")).pack(pady=20)

        data = self.database.get_reports()

        ttk.Label(window, text=f"Total Outages: {data['total_outages']}", font=("Arial", 14)).pack(pady=10)
        ttk.Label(window, text=f"Open Outages: {data['open_outages']}", font=("Arial", 14)).pack(pady=10)
        ttk.Label(window, text=f"Resolved Outages: {data['resolved_outages']}", font=("Arial", 14)).pack(pady=10)
        ttk.Label(
            window,
            text=f"Average Resolution Time: {data['average_resolution_hours']:.2f} hours",
            font=("Arial", 14),
        ).pack(pady=10)

        ttk.Label(window, text="Outages by Region", font=("Arial", 16, "bold")).pack(pady=15)

        region_table = ttk.Treeview(window, columns=("region", "count"), show="headings")
        region_table.heading("region", text="Region")
        region_table.heading("count", text="Outages")
        region_table.pack(fill="both", expand=True, padx=20)

        for row in data["outages_by_region"]:
            region_table.insert("", "end", values=row)


# starts the whole app
def main():
    database = Database()
    database.import_substations()
    database.import_lines()

    root = tk.Tk()

    def show_dashboard(user):
        for widget in root.winfo_children():
            widget.destroy()
        Dashboard(root, database, user, show_login)

    def show_login():
        for widget in root.winfo_children():
            widget.destroy()
        LoginWindow(root, database, show_dashboard)

    show_login()
    root.mainloop()


if __name__ == "__main__":
    main()
