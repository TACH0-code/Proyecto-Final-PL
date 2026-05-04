import customtkinter as ctk
import sqlite3
import hashlib
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image
from reportlab.lib.styles import getSampleStyleSheet
import os

# CONFIGURACIÓN UI
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")


# BASE DE DATOS
def conectar():
    return sqlite3.connect("inventario.db")

def crear_tablas():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inventario (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        producto TEXT,
        cantidad INTEGER,
        precio REAL
    )
    """)

    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def crear_usuario():
    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO usuarios (username, password) VALUES (?, ?)",
                       ("admin", hash_password("1234")))
    except:
        pass
    conn.commit()
    conn.close()


# LOGIN
class Login(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Login - Inventario")
        self.geometry("400x400")

        frame = ctk.CTkFrame(self)
        frame.pack(expand=True, padx=40, pady=40)

        ctk.CTkLabel(frame, text="Sistema de Inventario", font=("Arial", 20)).pack(pady=20)

        self.user = ctk.CTkEntry(frame, placeholder_text="Usuario")
        self.user.pack(pady=10)

        self.password = ctk.CTkEntry(frame, placeholder_text="Contraseña", show="*")
        self.password.pack(pady=10)

        ctk.CTkButton(frame, text="Ingresar", command=self.login).pack(pady=20)

    def login(self):
        conn = conectar()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM usuarios WHERE username=? AND password=?",
                       (self.user.get(), hash_password(self.password.get())))

        if cursor.fetchone():
            self.destroy()
            app = App()
            app.mainloop()
        else:
            print("Credenciales incorrectas")
            self.user.delete(0, 'end')
            self.password.delete(0, 'end')

        conn.close()


# APP INVENTARIO
class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Sistema de Inventario")
        self.geometry("800x600")

        self.id_seleccionado = None

        ctk.CTkLabel(self, text="Gestión de Inventario", font=("Arial", 22)).pack(pady=10)

        #BUSCADOR
        self.buscar_entry = ctk.CTkEntry(self, placeholder_text="Buscar producto...")
        self.buscar_entry.pack(pady=5)

        ctk.CTkButton(self, text="Buscar", command=self.buscar).pack(pady=5)

        # FORMULARIO
        self.producto = ctk.CTkEntry(self, placeholder_text="Producto")
        self.producto.pack(pady=5)

        self.cantidad = ctk.CTkEntry(self, placeholder_text="Cantidad")
        self.cantidad.pack(pady=5)

        self.precio = ctk.CTkEntry(self, placeholder_text="Precio")
        self.precio.pack(pady=5)

        # BOTONES
        ctk.CTkButton(self, text="Agregar", command=self.agregar).pack(pady=5)
        ctk.CTkButton(self, text="Actualizar Seleccionado", command=self.actualizar).pack(pady=5)
        ctk.CTkButton(self, text="Eliminar Seleccionado", command=self.eliminar).pack(pady=5)

        ctk.CTkButton(self, text="Ver Gráfico", command=self.grafico).pack(pady=5)
        ctk.CTkButton(self, text="Exportar PDF", command=self.exportar_pdf).pack(pady=5)

        # LISTA
        self.lista = ctk.CTkTextbox(self, width=700, height=250)
        self.lista.pack(pady=10)

        # EVENTO CLICK
        self.lista.bind("<ButtonRelease-1>", self.seleccionar)

        self.cargar()

    # FUNCION PARA CARGAR DATOS
    def cargar(self):
        self.lista.delete("0.0", "end")
        conn = conectar()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM inventario")
        for row in cursor.fetchall():
            self.lista.insert("end", f"{row}\n")

        conn.close()


    # FUNCION DE BUSCAR
   
    def buscar(self):
        texto = self.buscar_entry.get()

        self.lista.delete("0.0", "end")

        conn = conectar()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM inventario WHERE producto LIKE ?", (f"%{texto}%",))
        resultados = cursor.fetchall()

        for row in resultados:
            self.lista.insert("end", f"{row}\n")

        conn.close()


    # SELECCION DE REGISTROS
    def seleccionar(self, event):
        try:
            linea = self.lista.get("insert linestart", "insert lineend")
            datos = eval(linea)

            self.id_seleccionado = datos[0]

            self.producto.delete(0, 'end')
            self.producto.insert(0, datos[1])

            self.cantidad.delete(0, 'end')
            self.cantidad.insert(0, datos[2])

            self.precio.delete(0, 'end')
            self.precio.insert(0, datos[3])

        except:
            pass


    # CRUD
    def agregar(self):
        conn = conectar()
        cursor = conn.cursor()

        cursor.execute("INSERT INTO inventario (producto, cantidad, precio) VALUES (?, ?, ?)",
                       (self.producto.get(), self.cantidad.get(), self.precio.get()))

        conn.commit()
        conn.close()
        self.cargar()

    def actualizar(self):
        if self.id_seleccionado is None:
            print("Selecciona un producto")
            return

        conn = conectar()
        cursor = conn.cursor()

        cursor.execute("""
        UPDATE inventario 
        SET producto=?, cantidad=?, precio=? 
        WHERE id=?
        """, (self.producto.get(), self.cantidad.get(), self.precio.get(), self.id_seleccionado))

        conn.commit()
        conn.close()
        self.cargar()

    def eliminar(self):
        if self.id_seleccionado is None:
            print("Selecciona un producto")
            return

        conn = conectar()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM inventario WHERE id=?", (self.id_seleccionado,))
        conn.commit()
        conn.close()

        self.cargar()

 
    # GRÁFICO
    def grafico(self):
        conn = conectar()
        cursor = conn.cursor()

        cursor.execute("SELECT producto, SUM(cantidad) FROM inventario GROUP BY producto")
        data = cursor.fetchall()

        productos = [x[0] for x in data]
        cantidades = [x[1] for x in data]

        plt.figure()
        plt.bar(productos, cantidades)
        plt.title("Stock por Producto")
        plt.show()

 
    # PDF
    def exportar_pdf(self):
        conn = conectar()
        cursor = conn.cursor()

        cursor.execute("SELECT producto, SUM(cantidad) FROM inventario GROUP BY producto")
        data = cursor.fetchall()

        productos = [x[0] for x in data]
        cantidades = [x[1] for x in data]

        plt.figure()
        plt.bar(productos, cantidades)
        plt.savefig("grafico.png")
        plt.close()

        doc = SimpleDocTemplate("reporte_inventario.pdf")
        styles = getSampleStyleSheet()

        content = []
        content.append(Paragraph("Reporte de Inventario", styles['Title']))
        content.append(Image("grafico.png"))

        doc.build(content)

        os.remove("grafico.png")

        print("PDF generado")

# MAIN
if __name__ == "__main__":
    crear_tablas()
    crear_usuario()

    login = Login()
    login.mainloop()