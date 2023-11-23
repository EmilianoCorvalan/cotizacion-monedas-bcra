import datetime #libreria para trabajar con fechas
import socket #libreria para sockets
from requests import Session #biblioteca http para realizar solicitudes web
from lxml import html #analiza y manipula docs HTML y XML
from DatabaseHelperPOO import DatabaseHelper #libreria con metodos para interactuar con la bd
from decimal import Decimal #precision decimal para guardar en la bd

class ObtenerCotizaciones:
    def __init__(self):
        self.s = Session() #variable de sesion
        self.monedas = [ #guardamos nombre de moneda y su codigo para scrapear.
            {"nombre": "Pesos", "codigo": 5},
            {"nombre": "Pesos Chilenos", "codigo": 7},
            {"nombre": "Real", "codigo": 12},
            {"nombre": "Dolar estadounidense", "codigo": 2}
        ]
        self.dbh = DatabaseHelper()

    def obtener_cotizaciones(self):
        self.s.get("http://www.bcra.gob.ar/PublicacionesEstadisticas/Evolucion_moneda.asp") #hace un get al sitio del BCRA

        self.dbh.DBQuery("delete from cotizacion_historico") #elimina registros antiguos de la bd

        for moneda in self.monedas: #itera sobre las monedas para obtener datos historicos
            payload = {
                "Fecha": "2013.1.1", #historico desde 2013
                "Moneda": moneda['codigo']
            }
            r = self.s.post(url="http://www.bcra.gob.ar/PublicacionesEstadisticas/Evolucion_moneda_2.asp", data=payload) #hace un post para traer los datos del bcra

            tree = html.fromstring(r.text) #parsea el html obtenido para extraer datos de la tabla
            filas = tree.xpath("//table/tr")

            for fila in filas: #itera y almacena informacion en la bd
                arrayValores = [] #inicia la lista para guardar los datos de la fila como diccionario
                arrayValores.append({"fecha": fila[0].text.replace("\r", "").replace("\n", "")}) #los replace se usan para eliminar retorno de carro(r) y las nuevas lineas(n)
                arrayValores.append({"equivausd": fila[1].text})
                equivapesoComa = fila[2].text.replace("\r", "").replace("\n", "") #guardo en variable el numero recibido con coma.
                equivapeso = Decimal(equivapesoComa.replace(',','.')) #paso a decimal el numero con coma.
                arrayValores.append({"equivapeso": equivapeso})
                arrayValores.append({"moneda": moneda['codigo']})
                self.dbh.DBQuery(self.dbh.constructorInsert("cotizacion_historico", arrayValores))
                print("Insertado: " + str(fila[0].text.replace("\r", "").replace("\n", "")) + "   " + moneda['nombre'])

        self.dbh.commit() #confirma los cambios en BD

    def menu(self): #genera un menu de opciones principal
        while True:
            print("\nMenú:")
            print("1. Histórico desde 2013:")
            print("2. Actualización")
            print("3. Consulta Específica")
            print("4. Consulta por Rango")
            print("5. Diferencia")
            print("6. Servidor")
            print("7. Salir")

            opcion = input("Seleccione una opción: ")
            #logica para las opciones seleccionadas en el menu
            if opcion == '1': #obtenemos el historico desde el 2013, mediante un rango de fechas seleccionada
                fecha_inicio = input("Ingrese la fecha de inicio en formato (YYYY-MM-DD): ") #pide al usuario fecha inicio
                fecha_fin = input("Ingrese la fecha de fin en formato (YYYY-MM-DD): ") #pide al user fecha de fin
                self.dbh.historico2013(fecha_inicio, fecha_fin) #ejecuto el metodo historico2013 que se encuentra en la DatabaseHelperPOO.py

            elif opcion == '2':
                self.obtener_cotizaciones() #actualiza la bd

            elif opcion == '3': #realiza una consulta especifica ingresando fecha y moneda
                fecha = input("Ingrese la fecha (YYYY-MM-DD): ")
                print("\nLos tipos de moneda disponibles para ingresar son:")
                print("Dolar estadounidense \nPesos \nPesos chilenos \nReal\n")
                tipo_moneda = input("Ingrese el tipo de moneda: ")
                self.consulta_especifica(fecha, tipo_moneda.capitalize()) #capitalize pone la primer letra del string en mayuscula

            elif opcion == '4': #realiza una consulta por rango de fechas
                fecha_inicio = input("Ingrese la fecha de inicio (YYYY-MM-DD): ") #pide al usuario fecha inicio
                fecha_fin = input("Ingrese la fecha de fin (YYYY-MM-DD): ") #pide al user fecha de fin
                print("\nLos tipos de moneda disponibles para ingresar son:")
                print("Dolar estadounidense \nPesos \nPesos chilenos \nReal\n")
                tipo_moneda = input("Ingrese el tipo de moneda: ")
                self.consulta_por_rango(fecha_inicio, fecha_fin, tipo_moneda.capitalize())

            elif opcion == '5': #calcula la diferencia entre valores en un rango de fechas
                fecha_inicio = input("Ingrese la fecha de inicio (YYYY-MM-DD): ") #pide al usuario fecha inicio
                fecha_fin = input("Ingrese la fecha de fin (YYYY-MM-DD): ") #pide al user fecha de fin
                print("\nLos tipos de moneda disponibles para ingresar son:")
                print("Dolar estadounidense \nPesos \nPesos chilenos \nReal\n")
                tipo_moneda = input("Ingrese el tipo de moneda: ")
                self.diferencia(fecha_inicio, fecha_fin, tipo_moneda.capitalize())

            elif opcion == '6': #inicia un servidor y queda en escucha activa.
                self.servidor()

            elif opcion == '7': #sale del programa
                print("Saliendo del programa...")
                break

            else:
                print("Opción no válida. Inténtelo de nuevo.")

    

    def consulta_especifica(self, fecha, tipo_moneda):
        #consulta un valor especifico en una fecha y tipo de moneda
        query = ( #en esta variable se guarda la consulta SELECT a la bd.
            f"SELECT cotizacion_historico.equivapeso "
            f"FROM cotizacion_historico "
            f"JOIN moneda ON cotizacion_historico.moneda = moneda.id_moneda "
            f"WHERE cotizacion_historico.fecha = '{fecha}' AND moneda.nombre = '{tipo_moneda}'"
        )

        resultado = self.dbh.DBQuery(query) #consulta la bd y muestra el resultado

        if resultado:
            valor = resultado[0]['equivapeso']
            print("\n" + "-" * 50 ) #linea de guiones para separar
            print(f"\nValor para la fecha {fecha} y tipo de moneda {tipo_moneda}: {valor}")
            print("\n" + "-" * 50)
            return valor
        else:
            print(f"No se encontraron resultados para la fecha {fecha} y tipo de moneda {tipo_moneda}.")
            return None
        

    def consulta_por_rango(self, fecha_inicio, fecha_fin, tipo_moneda):
        #consulta valores en un rango de fechas para un tipo de moneda
        query = (
            f"SELECT cotizacion_historico.fecha, cotizacion_historico.equivausd, cotizacion_historico.equivapeso "
            f"FROM cotizacion_historico "
            f"JOIN moneda ON cotizacion_historico.moneda = moneda.id_moneda "
            f"WHERE cotizacion_historico.fecha BETWEEN '{fecha_inicio}' AND '{fecha_fin}' "
            f"AND moneda.nombre = '{tipo_moneda}'"
        )
        resultados = self.dbh.DBQuery(query)

        if resultados: #formatea y muestra los resultados de la consulta por rango
            valores = [(resultado['fecha'], resultado['equivausd'], resultado['equivapeso']) for resultado in resultados]
            for fecha, valorUSD, valorPesos in valores:
                print(f"Moneda: {tipo_moneda}, Fecha: {fecha}, Valor USD: {valorUSD}, Valor Pesos: {valorPesos}")
            return valores
        else:
            print(f"No se encontraron resultados para el rango de fechas y tipo de moneda proporcionados.")
            return []

    def diferencia(self, fecha_inicio, fecha_fin, tipo_moneda):
        #calcula la diferencia entre valores en un rango de fechas para un tipo de moneda
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
                #calcula y muestra la diferencia porcentual entre valores en un rango de fechas
                diferencia_porcentual = ((valor_fin - valor_inicio) / valor_inicio) * 100
                print(f"Diferencia porcentual entre {fecha_inicio} y {fecha_fin} para {tipo_moneda}: {diferencia_porcentual:.2f}%")
                return diferencia_porcentual
            else:
                print("No se pueden calcular diferencias con valores nulos.")
                return None
        else:
            print(f"No se encontraron valores para las fechas proporcionadas y el tipo de moneda.")
            return None

    def servidor(self): #inicia un server socket y atiende conexiones entrantes
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidor:
            servidor.bind(('127.0.0.1', 2345)) #indica ip y puerto del socket
            servidor.listen() #entra en escucha

            print("\nServidor en espera de conexiones en el puerto 2345...")

            while True:
                conn, addr = servidor.accept() #acepta una conexion entrante
                with conn:  #se usa with para asegurar que el recurso se libere al finalizar el bloque
                    print('Conexión establecida desde', addr) 
                    fecha_cliente = conn.recv(1024).decode('utf-8') #recibe datos del cliente y los codifica en utf8
                    valor_moneda = self.consulta_especifica(fecha_cliente, 'Dolar estadounidense') #consulta para obtener el valor de la moneda
                    if valor_moneda is not None: #envia al cliente un mensaje con el valor de la moneda y fecha
                        conn.sendall(f"El valor de la moneda Dólar estadounidense en la fecha {fecha_cliente} es: {valor_moneda}".encode('utf-8'))
                        self.menu() #llama al menu
                    else:
                        conn.sendall("No se encontraron resultados para la fecha proporcionada.".encode('utf-8')) #mensaje en caso de no encontrar la fecha proporcionada


if __name__ == "__main__":
    cotizaciones = ObtenerCotizaciones() #creamos el objeto
    cotizaciones.menu() #inicializamos el menu con todas sus funciones internamente