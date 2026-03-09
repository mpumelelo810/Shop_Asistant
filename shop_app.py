import tkinter as tk
from tkinter import ttk
import sqlite3
from datetime import date
from openpyxl import Workbook

# DATABASE CONNECTION
conn = sqlite3.connect("shop.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS goods(
id INTEGER PRIMARY KEY AUTOINCREMENT,
product TEXT,
date TEXT,
cost_per_pack REAL,
items_per_pack INTEGER,
price_per_item REAL,
selling_price REAL,
profit REAL
)
""")

conn.commit()


# ADD GOODS
def add_goods():

    product = product_entry.get()
    cost_pack = float(cost_entry.get())
    items_pack = int(items_entry.get())
    price_item = float(price_entry.get())

    selling_price = items_pack * price_item
    profit = selling_price - cost_pack

    today = str(date.today())

    cursor.execute("""
    INSERT INTO goods(product,date,cost_per_pack,items_per_pack,price_per_item,selling_price,profit)
    VALUES (?,?,?,?,?,?,?)
    """,(product,today,cost_pack,items_pack,price_item,selling_price,profit))

    conn.commit()

    result_label.config(text=f"Profit for pack: {profit}")

    load_data()


# LOAD TABLE
def load_data():

    for row in table.get_children():
        table.delete(row)

    cursor.execute("SELECT * FROM goods")

    for row in cursor.fetchall():
        table.insert("",tk.END,values=row)


# EXPORT MONTHLY REPORT
def export_excel():

    month = month_entry.get()

    cursor.execute("""
    SELECT product,
    COUNT(product),
    cost_per_pack,
    items_per_pack,
    price_per_item,
    selling_price,
    profit
    FROM goods
    WHERE strftime('%m',date)=?
    GROUP BY product
    """,(month,))

    results = cursor.fetchall()

    wb = Workbook()
    ws = wb.active

    ws.append([
    "Product",
    "Times Recorded",
    "Cost Per Pack",
    "Items Per Pack",
    "Price Per Item",
    "Selling Price",
    "Profit"
    ])

    for r in results:
        ws.append(r)

    wb.save("monthly_report.xlsx")

    report_label.config(text="Excel report created!")


# GUI
root = tk.Tk()
root.title("Shop Goods System")
root.geometry("900x600")


frame = tk.Frame(root)
frame.pack(pady=10)


tk.Label(frame,text="Product").grid(row=0,column=0)
product_entry = tk.Entry(frame)
product_entry.grid(row=0,column=1)


tk.Label(frame,text="Cost Per Pack").grid(row=1,column=0)
cost_entry = tk.Entry(frame)
cost_entry.grid(row=1,column=1)


tk.Label(frame,text="Items Per Pack").grid(row=2,column=0)
items_entry = tk.Entry(frame)
items_entry.grid(row=2,column=1)


tk.Label(frame,text="Price Per Item").grid(row=3,column=0)
price_entry = tk.Entry(frame)
price_entry.grid(row=3,column=1)


tk.Button(frame,text="Add Goods",command=add_goods).grid(row=4,columnspan=2,pady=10)

result_label = tk.Label(frame,text="")
result_label.grid(row=5,columnspan=2)


columns = ("ID","Product","Date","CostPack","ItemsPack","PriceItem","SellingPrice","Profit")

table = ttk.Treeview(root,columns=columns,show="headings")

for col in columns:
    table.heading(col,text=col)

table.pack(fill="both",expand=True)


report_frame = tk.Frame(root)
report_frame.pack(pady=10)

tk.Label(report_frame,text="Month (01-12)").grid(row=0,column=0)

month_entry = tk.Entry(report_frame)
month_entry.grid(row=0,column=1)

tk.Button(report_frame,text="Export Excel Report",command=export_excel).grid(row=0,column=2)

report_label = tk.Label(root,text="")
report_label.pack()


load_data()

root.mainloop()