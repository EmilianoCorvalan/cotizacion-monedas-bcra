import mysql.connector as mysql #interactua con la bd desde python
import sys #acceso a variables de sistema
import re   #operaciones con expresiones regulares
import traceback    #funciones para obtener y formatear info de seguimiento de excepciones
import datetime    #fecha y hora
import os #interactuar con el sistema operativo

class DatabaseHelper:
    def __init__(self): #config de la bd
        self.server = "localhost"
        self.database = "moneda"
        self.username = "root"
        self.password = ""

        if self.password is None: #verifica si es None, y la crea como como un string vacio
            self.password = ""
        #conexion a la bd y crea un cursor con diccionario
        self.conn = mysql.connect(user=self.username, password=self.password, host=self.server, database=self.database)
        self.cursor = self.conn.cursor(dictionary=True)

    def commit(self):
        self.conn.commit() #confirmacion en la bd

    def cerrarConexion(self):   #cierra el cursor y la conexion a la bd
        self.cursor.close() 
        self.conn.close()

    def log(self, parsename, detail):
        if not os.path.exists("log"): #si no existe el archivo log, lo crea.
            os.makedirs("log")

        path = os.path.join("log", f"{parsename}.log") #ruta de archivo

        if not os.path.isfile(path): #crea el archivo si no existe
            open(path, "w+").close()

        with open(path, "a") as f: #abre el archivo en modo escritura, agrega hora y detalles.
            f.write(f"Hora: {datetime.datetime.now()}\n")
            f.write(f"{detail}\n\n")

    def DBQuery(self, query):
        contador = 0
        while True:
            contador += 1
            try:
                self.cursor.execute(query) #intenta ejecutar la query

                if "SELECT" in query or "select" in query: #si es select devuelve los resultados
                    result = self.cursor.fetchall()
                    return result
                else:
                    return True #si es UPDATE,INSERT,DELETE devuelve True
                break
            except Exception as e:
                text = f"{traceback.format_exc()}\n{query}\n" #Si hay error registra la excepcion y la query en el log.
                self.log("DB", text)
                try: #intenta nuevamente la conexion
                    self.conn = mysql.connect(user=self.username, password=self.password, host=self.server, database=self.database)
                    self.cursor = self.conn.cursor(dictionary=True)
                except Exception as e: #si falla, registra otra vez la excepcion en el log
                    text = f"{traceback.format_exc()}\n{query}\n"
                    self.log("DB", text)
                if contador == 3: #si el contador alcanza 3 intentos, rompe el bucle.
                    break
        return None

    def ArreglarFecha(self, date): #formatear fechas
        if date in ('null', '-'): #verifica nulls
            return 'null'
        date = date.replace(' ', '') #elimina espacios en blanco y las divide con /
        listDate = date.split("/")
        return f"{listDate[2]}/{listDate[1]}/{listDate[0]}" #retorna la fecha formateada

    def constructorInsert(self, tabla, arrayValores): #variables para almacenar columnas y valores de la consulta
        columnas = ''
        valores = []
        query = ''
        valoresstring = ''
        for valor in arrayValores: #itera los valores
            for col, val in valor.items(): 
                columnas += col + ',' #concatena el nombre de la columna a la cadena de columnas
                valores.append(val) #agrega el valor a la lista de valores
        for value in valores: #itera para construir la cadena de valores
            if value is None:
                valoresstring += "null" + ","
                continue
            #procesa distintos tipos de valores y los agrega a la cadena.
            value = str(value).replace("\n", "").replace("  ", "").replace("'", '"')
            if value is None or value in ("None", "none", "NONE", "S/N", "s/n", "-", "null", "Null", "NULL", ""):
                valoresstring += "null" + ","
            elif isinstance(value, int):
                valoresstring += str(value).replace(',', '') + ","
            elif len(re.findall(r"[\d]{1,2}/[\d]{1,2}/[\d]{4}", value)) > 0:
                valoresstring += f"'{self.ArreglarFecha(value)}',"
            elif re.match("^[^a-zA-Z]*[^a-zA-Z]$", value):
                valoresstring += f"'{value.replace(',', '.').replace('$', '').replace('--------','1')}'," #quito este .replace('.', '')
            elif re.match("^[A-Za-z0-9_-]*$", value):
                valoresstring += f"'{value}',"
            else:
                valoresstring += f"'{value}',"
        query = f"REPLACE into {tabla}({columnas[:-1]}) values({valoresstring[:-1]}) "
        return query

    def historico2013(self, fecha_inicio, fecha_fin): #funcion para obtener el historico
        try:
            #consulta para obtener el historial
            query = ("SELECT cotizacion_historico.id, "
                    "DATE_FORMAT(cotizacion_historico.fecha, '%d-%m-%Y') AS fecha_formateada, "
                    "cotizacion_historico.equivausd, cotizacion_historico.equivapeso, "
                    "moneda.nombre AS nombre_moneda, cotizacion_historico.updated_at "
                    "FROM cotizacion_historico "
                    "JOIN moneda ON cotizacion_historico.moneda = moneda.id_moneda "
                    f"WHERE cotizacion_historico.fecha BETWEEN '{fecha_inicio}' AND '{fecha_fin}'")
            
            resultados = self.DBQuery(query)

            #mostrar en consola
            if resultados:
                for resultado in resultados:
                    print("ID:", resultado['id'])
                    print("Fecha:", resultado['fecha_formateada'])
                    print("Equivalente USD:", resultado['equivausd'])
                    print("Equivalente Peso:", resultado['equivapeso'])
                    print("Moneda:", resultado['nombre_moneda'])
                    print("Actualizado el:", resultado['updated_at'])
                    print("\n" + "-" * 50)  # Separador de guiones
            else:
                print("No se encontraron resultados en el historial.")

        except Exception as e:
            print(f"Error al obtener el historial: {e}")