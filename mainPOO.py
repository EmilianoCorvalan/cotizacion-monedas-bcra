import datetime
import socket
from requests import Session
from lxml import html
from DatabaseHelperPOO import DatabaseHelper
from decimal import Decimal

class ObtenerCotizaciones:
    def __init__(self):
        self.s = Session()
        self.monedas = [
            {"nombre": "Pesos", "codigo": 5},
            {"nombre": "Pesos Chilenos", "codigo": 7},
            {"nombre": "Real", "codigo": 12},
            {"nombre": "Dolar estadounidense", "codigo": 2}
        ]
        self.dbh = DatabaseHelper()

    def obtener_cotizaciones(self):
        self.s.get("http://www.bcra.gob.ar/PublicacionesEstadisticas/Evolucion_moneda.asp")

        self.dbh.DBQuery("delete from cotizacion_historico")

        for moneda in self.monedas:
            payload = {
                "Fecha": "2013.1.1", #historico desde 2013
                "Moneda": moneda['codigo']
            }
            r = self.s.post(url="http://www.bcra.gob.ar/PublicacionesEstadisticas/Evolucion_moneda_2.asp", data=payload)

            tree = html.fromstring(r.text)
            filas = tree.xpath("//table/tr")

            for fila in filas:
                arrayValores = []
                arrayValores.append({"fecha": fila[0].text.replace("\r", "").replace("\n", "")})
                arrayValores.append({"equivausd": fila[1].text})
                equivapesoComa = fila[2].text.replace("\r", "").replace("\n", "") #guardo en variable el numero recibido con coma.
                equivapeso = Decimal(equivapesoComa.replace(',','.')) #paso a decimal el numero con coma.
                arrayValores.append({"equivapeso": equivapeso})
                arrayValores.append({"moneda": moneda['codigo']})
                self.dbh.DBQuery(self.dbh.constructorInsert("cotizacion_historico", arrayValores))
                print("Insertado: " + str(fila[0].text.replace("\r", "").replace("\n", "")) + "   " + moneda['nombre'])

        self.dbh.commit()

    def menu(self):
        while True:
            print("\nMenú:")
            print("1. Histórico desde 2013 al:")
            print("2. Actualización")
            print("3. Consulta Específica")
            print("4. Consulta por Rango")
            print("5. Diferencia")
            print("6. Servidor")
            print("7. Salir")

            opcion = input("Seleccione una opción: ")

            if opcion == '1':
                fechaLimite = input("Ingrese la fecha limite en formato (YYYY-MM-DD): ")
                self.dbh.historico2013(fechaLimite)

            elif opcion == '2':
                self.obtener_cotizaciones()

            elif opcion == '3':
                fecha = input("Ingrese la fecha (YYYY-MM-DD): ")
                print("\nLos tipos de moneda disponibles para ingresar son:")
                print("Dolar estadounidense \nPesos \nPesos chilenos \nReal\n")
                tipo_moneda = input("Ingrese el tipo de moneda: ")
                self.consulta_especifica(fecha, tipo_moneda.capitalize())

            elif opcion == '4':
                fecha_inicio = input("Ingrese la fecha de inicio (YYYY-MM-DD): ")
                fecha_fin = input("Ingrese la fecha de fin (YYYY-MM-DD): ")
                print("\nLos tipos de moneda disponibles para ingresar son:")
                print("Dolar estadounidense \nPesos \nPesos chilenos \nReal\n")
                tipo_moneda = input("Ingrese el tipo de moneda: ")
                self.consulta_por_rango(fecha_inicio, fecha_fin, tipo_moneda)

            elif opcion == '5':
                fecha_inicio = input("Ingrese la fecha de inicio (YYYY-MM-DD): ")
                fecha_fin = input("Ingrese la fecha de fin (YYYY-MM-DD): ")
                print("\nLos tipos de moneda disponibles para ingresar son:")
                print("Dolar estadounidense \nPesos \nPesos chilenos \nReal\n")
                tipo_moneda = input("Ingrese el tipo de moneda: ")
                self.diferencia(fecha_inicio, fecha_fin, tipo_moneda)

            elif opcion == '6':
                self.servidor()

            elif opcion == '7':
                print("Saliendo del programa...")
                break

            else:
                print("Opción no válida. Inténtelo de nuevo.")

    

    def consulta_especifica(self, fecha, tipo_moneda):
        # Lógica para consultar un valor específico en una fecha y tipo de moneda
        query = (
            f"SELECT cotizacion_historico.equivapeso "
            f"FROM cotizacion_historico "
            f"JOIN moneda ON cotizacion_historico.moneda = moneda.id_moneda "
            f"WHERE cotizacion_historico.fecha = '{fecha}' AND moneda.nombre = '{tipo_moneda}'"
        )

        resultado = self.dbh.DBQuery(query)

        if resultado:
            valor = resultado[0]['equivapeso']
            print("\n" + "-" * 50 )
            print(f"\nValor para la fecha {fecha} y tipo de moneda {tipo_moneda}: {valor}")
            print("\n" + "-" * 50)
            return valor
        else:
            print(f"No se encontraron resultados para la fecha {fecha} y tipo de moneda {tipo_moneda}.")
            return None
        

    def consulta_por_rango(self, fecha_inicio, fecha_fin, tipo_moneda):
        # Lógica para consultar valores en un rango de fechas para un tipo de moneda
        query = (
            f"SELECT cotizacion_historico.fecha, cotizacion_historico.equivausd, cotizacion_historico.equivapeso "
            f"FROM cotizacion_historico "
            f"JOIN moneda ON cotizacion_historico.moneda = moneda.id_moneda "
            f"WHERE cotizacion_historico.fecha BETWEEN '{fecha_inicio}' AND '{fecha_fin}' "
            f"AND moneda.nombre = '{tipo_moneda}'"
        )
        resultados = self.dbh.DBQuery(query)

        if resultados:
            valores = [(resultado['fecha'], resultado['equivausd'], resultado['equivapeso']) for resultado in resultados]
            for fecha, valorUSD, valorPesos in valores:
                print(f"Moneda: {tipo_moneda}, Fecha: {fecha}, Valor USD: {valorUSD}, Valor Pesos: {valorPesos}")
            return valores
        else:
            print(f"No se encontraron resultados para el rango de fechas y tipo de moneda proporcionados.")
            return []

    def diferencia(self, fecha_inicio, fecha_fin, tipo_moneda):
        # Lógica para calcular la diferencia entre valores en un rango de fechas para un tipo de moneda
        query = (
            f"SELECT cotizacion_historico.equivausd "
            f"FROM cotizacion_historico "
            f"JOIN moneda ON cotizacion_historico.moneda = moneda.id_moneda "
            f"WHERE (cotizacion_historico.fecha = '{fecha_inicio}' OR cotizacion_historico.fecha = '{fecha_fin}') "
            f"AND moneda.nombre = '{tipo_moneda}'"
        )
        resultados = self.dbh.DBQuery(query)

        if len(resultados) == 2:
            valor_inicio = resultados[0]['equivausd']
            valor_fin = resultados[1]['equivausd']

            if valor_inicio is not None and valor_fin is not None:
                diferencia_porcentual = ((valor_fin - valor_inicio) / valor_inicio) * 100
                print(f"Diferencia porcentual entre {fecha_inicio} y {fecha_fin} para {tipo_moneda}: {diferencia_porcentual:.2f}%")
                return diferencia_porcentual
            else:
                print("No se pueden calcular diferencias con valores nulos.")
                return None
        else:
            print(f"No se encontraron valores para las fechas proporcionadas y el tipo de moneda.")
            return None

    def servidor(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidor:
            servidor.bind(('127.0.0.1', 2345))
            servidor.listen()

            print("Servidor en espera de conexiones en el puerto 2345...")

            while True:
                conn, addr = servidor.accept()
                with conn:
                    print('Conexión establecida desde', addr)
                    fecha_cliente = conn.recv(1024).decode('utf-8')
                    valor_moneda = self.consulta_especifica(fecha_cliente, 'Dolar estadounidense')
                    if valor_moneda is not None:
                        conn.sendall(f"El valor de la moneda Dólar estadounidense en la fecha {fecha_cliente} es: {valor_moneda}".encode('utf-8'))
                    else:
                        conn.sendall("No se encontraron resultados para la fecha proporcionada.".encode('utf-8'))


if __name__ == "__main__":
    cotizaciones = ObtenerCotizaciones()
    cotizaciones.menu()
    #cotizaciones.obtener_cotizaciones()