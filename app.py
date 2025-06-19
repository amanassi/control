from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)
DB = "pagos.db"

def init_db():
    with sqlite3.connect(DB) as conn:
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS proveedores (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nombre TEXT,
                        contacto TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS facturas (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        proveedor_id INTEGER,
                        descripcion TEXT,
                        monto REAL,
                        fecha TEXT,
                        estado TEXT DEFAULT 'pendiente',
                        FOREIGN KEY (proveedor_id) REFERENCES proveedores(id))""")
        c.execute("""CREATE TABLE IF NOT EXISTS pagos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        factura_id INTEGER,
                        monto REAL,
                        fecha TEXT,
                        FOREIGN KEY (factura_id) REFERENCES facturas(id))""")

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/proveedores', methods=["GET", "POST"])
def proveedores():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    if request.method == "POST":
        nombre = request.form["nombre"]
        contacto = request.form["contacto"]
        c.execute("INSERT INTO proveedores (nombre, contacto) VALUES (?, ?)", (nombre, contacto))
        conn.commit()
        return redirect(url_for('proveedores'))
    c.execute("SELECT * FROM proveedores")
    proveedores = c.fetchall()
    conn.close()
    return render_template("proveedores.html", proveedores=proveedores)

@app.route('/facturas', methods=["GET", "POST"])
def facturas():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    if request.method == "POST":
        proveedor_id = request.form["proveedor_id"]
        descripcion = request.form["descripcion"]
        monto = request.form["monto"]
        fecha = datetime.now().strftime("%Y-%m-%d")
        c.execute("INSERT INTO facturas (proveedor_id, descripcion, monto, fecha) VALUES (?, ?, ?, ?)",
                  (proveedor_id, descripcion, monto, fecha))
        conn.commit()
        return redirect(url_for('facturas'))
    c.execute("SELECT id, nombre FROM proveedores")
    proveedores = c.fetchall()
    c.execute("""SELECT f.id, p.nombre, f.descripcion, f.monto, f.fecha, f.estado 
                 FROM facturas f JOIN proveedores p ON f.proveedor_id = p.id""")
    facturas = c.fetchall()
    conn.close()
    return render_template("facturas.html", facturas=facturas, proveedores=proveedores)

@app.route('/pagos/<int:factura_id>', methods=["GET", "POST"])
def pagos(factura_id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    if request.method == "POST":
        monto = float(request.form["monto"])
        fecha = datetime.now().strftime("%Y-%m-%d")
        c.execute("INSERT INTO pagos (factura_id, monto, fecha) VALUES (?, ?, ?)", (factura_id, monto, fecha))
        c.execute("SELECT monto FROM facturas WHERE id = ?", (factura_id,))
        monto_total = c.fetchone()[0]
        c.execute("SELECT SUM(monto) FROM pagos WHERE factura_id = ?", (factura_id,))
        total_pagado = c.fetchone()[0] or 0
        if total_pagado >= monto_total:
            estado = "pagada"
        elif total_pagado > 0:
            estado = "parcialmente pagada"
        else:
            estado = "pendiente"
        c.execute("UPDATE facturas SET estado = ? WHERE id = ?", (estado, factura_id))
        conn.commit()
        return redirect(url_for('facturas'))

    c.execute("SELECT monto, fecha FROM pagos WHERE factura_id = ?", (factura_id,))
    pagos = c.fetchall()
    conn.close()
    return render_template("pagos.html", pagos=pagos, factura_id=factura_id)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
