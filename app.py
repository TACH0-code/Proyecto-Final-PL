import customtkinter as ctk
import mysql.connector
import hashlib
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image
from reportlab.lib.styles import getSampleStyleSheet
import os

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")


# CONEXIÓN MYSQL

def conectar():
    return mysql.connector.connect(
        host="localhost",
        user="admin",
        password="1234",
        database="inventario_db"
    )

# HASH
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# LOGIN
class Login(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Login")
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

        cursor.execute(
            "SELECT * FROM usuarios WHERE username=%s AND password=%s",
            (self.user.get(), hash_password(self.password.get()))
        )

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

        # BUSCADOR
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
        ctk.CTkButton(self, text="Actualizar", command=self.actualizar).pack(pady=5)
        ctk.CTkButton(self, text="Eliminar", command=self.eliminar).pack(pady=5)

        ctk.CTkButton(self, text="Ver Gráfico", command=self.grafico).pack(pady=5)
        ctk.CTkButton(self, text="Exportar PDF", command=self.exportar_pdf).pack(pady=5)

        # LISTA
        self.lista = ctk.CTkTextbox(self, width=700, height=250)
        self.lista.pack(pady=10)

        self.lista.bind("<ButtonRelease-1>", self.seleccionar)

        self.cargar()


    # CARGAR DATOS
    def cargar(self):
        self.lista.delete("0.0", "end")
        conn = conectar()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM inventario")
        for row in cursor.fetchall():
            self.lista.insert("end", f"{row[0]} | {row[1]} | {row[2]} | {row[3]}\n")

        conn.close()

    # BUSCAR
    def buscar(self):
        texto = self.buscar_entry.get()

        self.lista.delete("0.0", "end")

        conn = conectar()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM inventario WHERE producto LIKE %s", (f"%{texto}%",))
        resultados = cursor.fetchall()

        for row in resultados:
            self.lista.insert("end", f"{row[0]} | {row[1]} | {row[2]} | {row[3]}\n")

        conn.close()

    
    # SELECCIONAR
    def seleccionar(self, event):
        try:
            linea = self.lista.get("insert linestart", "insert lineend")
            datos = linea.split(" | ")

            self.id_seleccionado = int(datos[0])

            self.producto.delete(0, 'end')
            self.producto.insert(0, datos[1])

            self.cantidad.delete(0, 'end')
            self.cantidad.insert(0, datos[2])

            self.precio.delete(0, 'end')
            self.precio.insert(0, datos[3])

        except Exception as e:
            print("Error al seleccionar:", e)


    # CRUD
    def agregar(self):
        conn = conectar()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO inventario (producto, cantidad, precio) VALUES (%s, %s, %s)",
            (self.producto.get(), self.cantidad.get(), self.precio.get())
        )

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
            SET producto=%s, cantidad=%s, precio=%s 
            WHERE id=%s
        """, (self.producto.get(), self.cantidad.get(), self.precio.get(), self.id_seleccionado))

        conn.commit()
        conn.close()
        self.cargar()

    def eliminar(self):
        if self.id_seleccionado is None:
            print("Selecciona un producto primero")
            return

        conn = conectar()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM inventario WHERE id=%s", (self.id_seleccionado,))
        conn.commit()

        print("Eliminado ID:", self.id_seleccionado)

        conn.close()

        self.id_seleccionado = None
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
    login = Login()
    login.mainloop()