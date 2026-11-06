import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk
import subprocess
from pathlib import Path
import matplotlib.pyplot as plt


# ================= FILE PATH CONFIGURATION =================

BASE_DIR = Path(__file__).resolve().parent

DB_PATH = BASE_DIR / "expenses.db"
DATA_PATH = BASE_DIR / "data.txt"
RESULT_PATH = BASE_DIR / "result.txt"

C_SOURCE = BASE_DIR / "analyze.c"
ANALYZER_EXE = BASE_DIR / "analyze.exe"


# ================= DATABASE SETUP =================

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    category TEXT NOT NULL,
    amount REAL NOT NULL,
    type TEXT NOT NULL
)
""")

conn.commit()


# ================= FUNCTIONS =================

def add_record():
    date = entry_date.get().strip()
    category = category_var.get().strip()
    amount = entry_amount.get().strip().replace(",", "")
    typ = type_var.get().strip().lower()

    if not date or not category or not amount or not typ:
        messagebox.showerror("Invalid Input", "All fields are required")
        return

    if typ not in ["income", "expense"]:
        messagebox.showerror("Invalid Input", "Type must be income or expense")
        return

    try:
        amount = float(amount)
        if amount <= 0:
            messagebox.showerror("Invalid Input", "Amount must be greater than zero")
            return
    except ValueError:
        messagebox.showerror("Invalid Input", "Amount must be a valid number")
        return

    cursor.execute(
        "INSERT INTO expenses(date, category, amount, type) VALUES (?, ?, ?, ?)",
        (date, category, amount, typ)
    )
    conn.commit()

    messagebox.showinfo("Success", "Record added successfully")

    entry_date.delete(0, tk.END)
    category_var.set("")
    entry_amount.delete(0, tk.END)
    type_var.set("")


def view_records():
    cursor.execute("SELECT * FROM expenses")
    rows = cursor.fetchall()

    output.delete("1.0", tk.END)

    if not rows:
        output.insert(tk.END, "No records found.\n")
        return

    output.insert(tk.END, "ID | Date | Category | Amount | Type\n")
    output.insert(tk.END, "-" * 60 + "\n")

    for row in rows:
        output.insert(
            tk.END,
            f"{row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]}\n"
        )


def export_data():
    cursor.execute("SELECT type, amount FROM expenses")
    rows = cursor.fetchall()

    with open(DATA_PATH, "w") as file:
        for typ, amount in rows:
            file.write(f"{typ} {amount}\n")



def run_analysis():
    cursor.execute("SELECT COUNT(*) FROM expenses")
    count = cursor.fetchone()[0]

    if count == 0:
        messagebox.showerror(
            "No Data",
            "No records available for analysis"
        )
        return

    export_data()

    # Check whether the C source file exists
    if not C_SOURCE.exists():
        messagebox.showerror(
            "Error",
            "analyze.c source file not found."
        )
        return

    try:
        # Compile the C program if necessary
        if (
            not ANALYZER_EXE.exists()
            or C_SOURCE.stat().st_mtime > ANALYZER_EXE.stat().st_mtime
        ):
            subprocess.run(
                ["gcc", str(C_SOURCE), "-o", str(ANALYZER_EXE)],
                cwd=BASE_DIR,
                check=True,
                capture_output=True,
                text=True
            )

        # Execute the compiled C program
        subprocess.run(
            [str(ANALYZER_EXE)],
            cwd=BASE_DIR,
            check=True,
            capture_output=True,
            text=True
        )

    except FileNotFoundError:
        messagebox.showerror(
            "Compiler Error",
            "GCC was not found. Please install GCC and add it to PATH."
        )
        return

    except subprocess.CalledProcessError as error:
        messagebox.showerror(
            "Execution Error",
            f"Analysis failed:\n{error.stderr or error}"
        )
        return

    # Check whether the result file was generated
    if not RESULT_PATH.exists():
        messagebox.showerror(
            "Error",
            "result.txt was not generated."
        )
        return

    with open(RESULT_PATH, "r") as file:
        result = file.read()

    messagebox.showinfo("Analysis Result", result)



def create_donut_chart(data, title):
    categories = [row[0] for row in data]
    amounts = [row[1] for row in data]

    plt.figure(figsize=(6, 6))

    colors = [
        "#388E3C",
        "#F57C00",
        "#9C2436",
        "#1DA1D8",
        "#5E236D",
        "#00796B",
        "#455A64",
        "#8BC34A",
        "#FFC107",
        "#795548",
        "#607D8B"
    ]

    plt.pie(
        amounts,
        labels=None,
        autopct="%1.1f%%",
        startangle=90,
        counterclock=False,
        colors=colors,
        pctdistance=0.75,
        wedgeprops={
            "width": 0.38,
            "edgecolor": "white",
            "linewidth": 2
        },
        textprops={
            "color": "white",
            "fontsize": 10,
            "weight": "bold"
        }
    )

    plt.title(title, fontsize=16, fontweight="bold")
    plt.legend(categories, loc="lower center", bbox_to_anchor=(0.5, -0.15), ncol=2)
    plt.axis("equal")
    plt.show()


def show_graph():
    cursor.execute("""
        SELECT category, SUM(amount)
        FROM expenses
        WHERE type = 'income'
        GROUP BY category
    """)
    income_data = cursor.fetchall()

    cursor.execute("""
        SELECT category, SUM(amount)
        FROM expenses
        WHERE type = 'expense'
        GROUP BY category
    """)
    expense_data = cursor.fetchall()

    if not income_data and not expense_data:
        messagebox.showerror("No Data", "No records available for graphs")
        return

    if expense_data:
        create_donut_chart(expense_data, "Expenses")
    else:
        messagebox.showinfo("Expense Graph", "No expense records available.")

    if income_data:
        create_donut_chart(income_data, "Incomes")
    else:
        messagebox.showinfo("Income Graph", "No income records available.")


def clear_records():
    confirm = messagebox.askyesno("Confirm", "Do you want to delete all records?")
    if confirm:
        cursor.execute("DELETE FROM expenses")
        conn.commit()
        output.delete("1.0", tk.END)
        messagebox.showinfo("Deleted", "All records deleted successfully")


# ================= GUI SETUP =================

root = tk.Tk()
root.title("Smart Expense & Spending Behaviour Analyzer")
root.geometry("650x600")

title = tk.Label(
    root,
    text="Smart Expense & Spending Behaviour Analyzer",
    font=("Arial", 16, "bold")
)
title.pack(pady=10)


frame = tk.Frame(root)
frame.pack(pady=10)


tk.Label(frame, text="Date").grid(row=0, column=0, padx=10, pady=5, sticky="w")
entry_date = tk.Entry(frame, width=30)
entry_date.grid(row=0, column=1, padx=10, pady=5)


tk.Label(frame, text="Category").grid(row=1, column=0, padx=10, pady=5, sticky="w")

category_var = tk.StringVar()

entry_category = ttk.Combobox(
    frame,
    textvariable=category_var,
    width=27,
    state="readonly"
)

entry_category["values"] = (
    "food and dining",
    "shopping",
    "travelling",
    "entertainment",
    "medical",
    "personal care",
    "education",
    "bills and utilities",
    "rent",
    "investments",
    "salary",
    "allowance",
    "bonus",
    "other"
)

entry_category.grid(row=1, column=1, padx=10, pady=5)


tk.Label(frame, text="Amount").grid(row=2, column=0, padx=10, pady=5, sticky="w")
entry_amount = tk.Entry(frame, width=30)
entry_amount.grid(row=2, column=1, padx=10, pady=5)


tk.Label(frame, text="Type").grid(row=3, column=0, padx=10, pady=5, sticky="w")

type_var = tk.StringVar()

type_dropdown = ttk.Combobox(
    frame,
    textvariable=type_var,
    width=27,
    state="readonly"
)

type_dropdown["values"] = ("income", "expense")
type_dropdown.grid(row=3, column=1, padx=10, pady=5)


button_frame = tk.Frame(root)
button_frame.pack(pady=10)

tk.Button(button_frame, text="Add Record", width=15, command=add_record).grid(row=0, column=0, padx=5)
tk.Button(button_frame, text="View Records", width=15, command=view_records).grid(row=0, column=1, padx=5)
tk.Button(button_frame, text="Analyze", width=15, command=run_analysis).grid(row=0, column=2, padx=5)
tk.Button(button_frame, text="Graphs", width=15, command=show_graph).grid(row=0, column=3, padx=5)

tk.Button(root, text="Clear All Records", width=20, command=clear_records).pack(pady=5)


output = tk.Text(root, height=18, width=75)
output.pack(pady=10)


root.mainloop()