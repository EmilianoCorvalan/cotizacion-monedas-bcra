import mysql.connector as mysql
import sys
import re
import traceback
import datetime 
import os

class DatabaseHelper:
    def __init__(self):
        self.server = "localhost"
        self.database = "moneda"
        self.username = "root"
        self.password = ""

        if self.password is None:
            self.password = ""

        self.conn = mysql.connect(user=self.username, password=self.password, host=self.server, database=self.database)
        self.cursor = self.conn.cursor(dictionary=True)

    def commit(self):
        self.conn.commit()

    def cerrarConexion(self):
        self.cursor.close()
        self.conn.close()

    def log(self, parsename, detail):
        if not os.path.exists("log"):
            os.makedirs("log")

        path = os.path.join("log", f"{parsename}.log")

        if not os.path.isfile(path):
            open(path, "w+").close()

        with open(path, "a") as f:
            f.write(f"Hora: {datetime.datetime.now()}\n")
            f.write(f"{detail}\n\n")

    def DBQuery(self, query):
        contador = 0
        while True:
            contador += 1
            try:
                self.cursor.execute(query)

                if "SELECT" in query or "select" in query:
                    result = self.cursor.fetchall()
                    return result
                else:
                    return True
                break
            except Exception as e:
                text = f"{traceback.format_exc()}\n{query}\n"
                self.log("DB", text)
                try:
                    self.conn = mysql.connect(user=self.username, password=self.password, host=self.server, database=self.database)
                    self.cursor = self.conn.cursor(dictionary=True)
                except Exception as e:
                    text = f"{traceback.format_exc()}\n{query}\n"
                    self.log("DB", text)
                if contador == 3:
                    break
        return None

    def ArreglarFecha(self, date):
        if date in ('null', '-'):
            return 'null'
        date = date.replace(' ', '')
        listDate = date.split("/")
        return f"{listDate[2]}/{listDate[1]}/{listDate[0]}"

    def constructorInsert(self, tabla, arrayValores):
        columnas = ''
        valores = []
        query = ''
        valoresstring = ''
        for valor in arrayValores:
            for col, val in valor.items():
                columnas += col + ','
                valores.append(val)
        for value in valores:
            if value is None:
                valoresstring += "null" + ","
                continue

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
