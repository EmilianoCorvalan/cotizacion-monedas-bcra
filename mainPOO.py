from requests import Session
from lxml import html
from DatabaseHelperPOO import DatabaseHelper

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
                "Fecha": "2010.1.1",
                "Moneda": moneda['codigo']
            }
            r = self.s.post(url="http://www.bcra.gob.ar/PublicacionesEstadisticas/Evolucion_moneda_2.asp", data=payload)

            tree = html.fromstring(r.text)
            filas = tree.xpath("//table/tr")

            for fila in filas:
                arrayValores = []
                arrayValores.append({"fecha": fila[0].text.replace("\r", "").replace("\n", "")})
                arrayValores.append({"equivausd": fila[1].text})
                arrayValores.append({"equivapeso": fila[2].text})
                arrayValores.append({"moneda": moneda['codigo']})
                self.dbh.DBQuery(self.dbh.constructorInsert("cotizacion_historico", arrayValores))
                print("Insertado: " + str(fila[0].text.replace("\r", "").replace("\n", "")) + "   " + moneda['nombre'])

        self.dbh.commit()




if __name__ == "__main__":
    cotizaciones = ObtenerCotizaciones()
    cotizaciones.obtener_cotizaciones()