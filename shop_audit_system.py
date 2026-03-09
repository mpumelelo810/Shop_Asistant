import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from PIL import Image, ImageTk
import sqlite3
from openpyxl import Workbook
import matplotlib.pyplot as plt
import smtplib
from email.mime.text import MIMEText
import threading
import schedule
import shutil
import time
import os

APP_NAME = "Shop Assistant Pro"
EMAIL = "datatechshopassistant@gmail.com"
EMAIL_PASSWORD = "*"

# ---------------- DATABASE ----------------
conn = sqlite3.connect("shop.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS goods(
id INTEGER PRIMARY KEY AUTOINCREMENT,
product TEXT,
date TEXT,
cost REAL,
items INTEGER,
price REAL,
selling REAL,
profit REAL
)
""")

# Ensure items column exists (Fix for old databases)
cursor.execute("PRAGMA table_info(goods)")
columns = [col[1] for col in cursor.fetchall()]

if "items" not in columns:
    cursor.execute("ALTER TABLE goods ADD COLUMN items INTEGER DEFAULT 0")
    conn.commit()

conn.commit()

# ---------------- SPLASH SCREEN ----------------

def splash():

    splash = tk.Tk()
    splash.overrideredirect(True)

    width = 420
    height = 340

    x = (splash.winfo_screenwidth()//2)-(width//2)
    y = (splash.winfo_screenheight()//2)-(height//2)

    splash.geometry(f"{width}x{height}+{x}+{y}")

    frame = tk.Frame(splash,bg="white")
    frame.pack(fill="both",expand=True)

    try:
        base = os.path.dirname(os.path.abspath(__file__))
        logo_path = os.path.join(base,"logo.png")

        img = Image.open(logo_path)
        img = img.resize((140,140))
        logo = ImageTk.PhotoImage(img)

        lbl = tk.Label(frame,image=logo,bg="white")
        lbl.image = logo
        lbl.pack(pady=10)

    except:
        pass

    tk.Label(frame,text=APP_NAME,font=("Arial",22,"bold"),bg="white").pack()

    progress = ttk.Progressbar(frame,length=300)
    progress.pack(pady=20)

    splash.update()

    for i in range(100):
        progress["value"] = i
        splash.update()
        time.sleep(0.02)

    splash.destroy()


# ---------------- EMAIL ----------------

def send_email():

    msg = MIMEText("Test email from Shop Assistant Pro")
    msg["Subject"] = ""
    msg["From"] = EMAIL
    msg["To"] = EMAIL

    try:

        server = smtplib.SMTP("smtp.gmail.com",587)
        server.starttls()
        server.login(EMAIL,EMAIL_PASSWORD)
        server.sendmail(EMAIL,EMAIL,msg.as_string())
        server.quit()

        messagebox.showinfo("Email","Email sent successfully")

    except Exception as e:

        messagebox.showerror("Email Error",str(e))


# ---------------- REMINDER EMAIL ----------------

def stock_reminder_email():

    msg = MIMEText("Reminder: Please check your shop stock.")
    msg["Subject"] = "Stock Reminder"
    msg["From"] = EMAIL
    msg["To"] = EMAIL

    try:

        server = smtplib.SMTP("smtp.gmail.com",587)
        server.starttls()
        server.login(EMAIL,EMAIL_PASSWORD)
        server.sendmail(EMAIL,EMAIL,msg.as_string())
        server.quit()

    except:
        pass


# ---------------- SCHEDULER ----------------

def scheduler():

    schedule.every().friday.at("09:00").do(stock_reminder_email)

    while True:
        schedule.run_pending()
        time.sleep(60)


# ---------------- AUTOCOMPLETE ----------------

def get_product_names():

    cursor.execute("SELECT DISTINCT product FROM goods")
    rows = cursor.fetchall()

    return [r[0] for r in rows]


def check_input(event):

    typed = product_entry.get()
    names = get_product_names()

    if typed == "":
        suggestion_box.place_forget()
        return

    data = []

    for item in names:
        if typed.lower() in item.lower():
            data.append(item)

    suggestion_box.delete(0,tk.END)

    for item in data:
        suggestion_box.insert(tk.END,item)

    if data:
        suggestion_box.place(x=product_entry.winfo_rootx()-app.winfo_rootx(),
                             y=product_entry.winfo_rooty()-app.winfo_rooty()+30,
                             width=200)
    else:
        suggestion_box.place_forget()


def fill_entry(event):

    try:

        selected = suggestion_box.get(tk.ACTIVE)

        product_entry.delete(0,tk.END)
        product_entry.insert(0,selected)

        suggestion_box.place_forget()

    except:
        pass


# ---------------- DASHBOARD ----------------

def update_dashboard():
    
    cursor.execute("SELECT COUNT(*) FROM goods")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(items) FROM goods")
    stock = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(profit) FROM goods")
    profit = cursor.fetchone()[0]

    if stock is None:
        stock = 0

    if profit is None:
        profit = 0

    dashboard.configure(
        text=f"Products: {total} | Stock Items: {stock} | Profit: {profit}"
    )

# ---------------- LOAD DATA ----------------

def load_data():

    for row in table.get_children():
        table.delete(row)

    cursor.execute("SELECT * FROM goods")

    for row in cursor.fetchall():
        table.insert("",tk.END,values=row)


# ---------------- ADD RECORD ----------------

def add_record():

    product = product_entry.get()

    try:

        cost = float(cost_entry.get())
        items = int(items_entry.get())
        price = float(price_entry.get())

    except:

        messagebox.showerror("Error","Invalid numbers")
        return

    selling = items * price
    profit = selling - cost

    cursor.execute("""
    INSERT INTO goods(product,date,cost,items,price,selling,profit)
    VALUES(?,?,?,?,?,?,?)
    """,(product,date_entry.get(),cost,items,price,selling,profit))

    conn.commit()

    load_data()
    update_dashboard()
    check_low_stock()

    product_entry.delete(0,"end")
    cost_entry.delete(0,"end")
    items_entry.delete(0,"end")
    price_entry.delete(0,"end")


# ---------------- DELETE ----------------

def delete_record():

    selected = table.selection()

    if not selected:
        return

    record_id = table.item(selected[0])["values"][0]

    cursor.execute("DELETE FROM goods WHERE id=?",(record_id,))
    conn.commit()

    load_data()
    update_dashboard()


# ---------------- SEARCH ----------------

def search_product():

    keyword = search_entry.get()

    for row in table.get_children():
        table.delete(row)

    cursor.execute(
        "SELECT * FROM goods WHERE product LIKE ?",
        ('%'+keyword+'%',)
    )

    for row in cursor.fetchall():
        table.insert("",tk.END,values=row)


# ---------------- LOW STOCK ----------------

def check_low_stock():

    cursor.execute("SELECT product,items FROM goods WHERE items < 5")
    rows = cursor.fetchall()

    if rows:

        msg = "Low Stock Warning\n\n"

        for r in rows:
            msg += f"{r[0]} : {r[1]} items\n"

        messagebox.showwarning("Low Stock",msg)


# ---------------- EXPORT ----------------

def export_excel():

    wb = Workbook()
    ws = wb.active

    ws.append(["Product","Date","Cost","Items","Price","Selling","Profit"])

    cursor.execute("SELECT product,date,cost,items,price,selling,profit FROM goods")

    for row in cursor.fetchall():
        ws.append(row)

    wb.save("shop_report.xlsx")

    messagebox.showinfo("Export","Excel report created")


# ---------------- GRAPH ----------------

def profit_graph():

    cursor.execute("SELECT product,profit FROM goods")

    products=[]
    profits=[]

    for row in cursor.fetchall():
        products.append(row[0])
        profits.append(row[1])

    if not products:
        messagebox.showinfo("Graph","No data available")
        return

    plt.bar(products,profits)
    plt.title("Profit per Product")
    plt.xticks(rotation=45)
    plt.show()


# ---------------- BACKUP ----------------

def backup_database():

    shutil.copy("shop.db","shop_backup.db")
    messagebox.showinfo("Backup","Database backup created")


# ---------------- DARK MODE ----------------

def toggle_theme():

    if theme_switch.get() == 1:
        ctk.set_appearance_mode("dark")
    else:
        ctk.set_appearance_mode("light")


# ---------------- START ----------------

if __name__ == "__main__":

    splash()

    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")

    app = ctk.CTk()
    app.title(APP_NAME)
    app.geometry("1100x720")

# ---------------- HEADER ----------------

    header = ctk.CTkFrame(app)
    header.pack(fill="x")

    # LEFT SIDE (Logo)
    left_frame = ctk.CTkFrame(header, fg_color="transparent")
    left_frame.pack(side="left", padx=10)

    try:
        base_path = os.path.dirname(os.path.abspath(__file__))
        logo_path = os.path.join(base_path, "logo.png")

        logo_img = Image.open(logo_path)
        logo_ctk = ctk.CTkImage(logo_img,size=(120,60))

        ctk.CTkLabel(left_frame,image=logo_ctk,text="").pack()

    except:
        pass

    # CENTER TITLE
    title_frame = ctk.CTkFrame(header, fg_color="transparent")
    title_frame.pack(side="left", expand=True)

    ctk.CTkLabel(title_frame,text=APP_NAME,font=("Arial",28,"bold")).pack()

    # RIGHT SIDE DARK MODE
    right_frame = ctk.CTkFrame(header, fg_color="transparent")
    right_frame.pack(side="right", padx=20)

    theme_switch = ctk.CTkSwitch(right_frame,text="Dark Mode",command=toggle_theme)
    theme_switch.pack()

# ---------------- DASHBOARD ----------------

    dashboard = ctk.CTkLabel(app,text="",font=("Arial",16,"bold"))
    dashboard.pack(pady=10)

# ---------------- SEARCH ----------------

    search_frame = ctk.CTkFrame(app)
    search_frame.pack(pady=5)

    search_entry = ctk.CTkEntry(search_frame,width=250)
    search_entry.pack(side="left",padx=5)

    ctk.CTkButton(search_frame,text="Search",command=search_product).pack(side="left")

# ---------------- FORM ----------------

    form = ctk.CTkFrame(app)
    form.pack(pady=10)

    product_entry = ctk.CTkEntry(form,placeholder_text="Product")
    product_entry.grid(row=0,column=0,padx=5,pady=5)
    product_entry.bind("<KeyRelease>",check_input)

    suggestion_box = tk.Listbox(app)
    suggestion_box.bind("<<ListboxSelect>>",fill_entry)

    date_entry = DateEntry(form)
    date_entry.grid(row=0,column=1)

    cost_entry = ctk.CTkEntry(form,placeholder_text="Cost")
    cost_entry.grid(row=1,column=0)

    items_entry = ctk.CTkEntry(form,placeholder_text="Items")
    items_entry.grid(row=1,column=1)

    price_entry = ctk.CTkEntry(form,placeholder_text="Price")
    price_entry.grid(row=2,column=0)

    ctk.CTkButton(form,text="Add Record",command=add_record).grid(row=2,column=1)

# ---------------- TABLE ----------------

    columns=("ID","Product","Date","Cost","Items","Price","Selling","Profit")

    table = ttk.Treeview(app,columns=columns,show="headings")

    for col in columns:
        table.heading(col,text=col)
        table.column(col,width=120)

    table.pack(fill="both",expand=True,padx=20,pady=10)

# ---------------- BUTTONS ----------------

    btn_frame = ctk.CTkFrame(app)
    btn_frame.pack(pady=10)

    ctk.CTkButton(btn_frame,text="Delete",fg_color="red",command=delete_record).pack(side="left",padx=5)
    ctk.CTkButton(btn_frame,text="Export Excel",command=export_excel).pack(side="left",padx=5)
    ctk.CTkButton(btn_frame,text="Profit Graph",command=profit_graph).pack(side="left",padx=5)
    ctk.CTkButton(btn_frame,text="Send Test Email",command=send_email).pack(side="left",padx=5)
    ctk.CTkButton(btn_frame,text="Backup Database",command=backup_database).pack(side="left",padx=5)

# ---------------- FOOTER ----------------

    footer = ctk.CTkFrame(app,height=30)
    footer.pack(side="bottom",fill="x")

    footer_label = ctk.CTkLabel(
        footer,
        text="© 2026 DataTech | All Rights Reserved",
        font=("Arial",12)
    )

    footer_label.pack(pady=6)

# ---------------- INIT ----------------

    load_data()
    update_dashboard()

    scheduler_thread = threading.Thread(target=scheduler,daemon=True)
    scheduler_thread.start()

    app.mainloop()