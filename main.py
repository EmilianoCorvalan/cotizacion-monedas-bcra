import requests
from requests import Session
from lxml import etree, html
from DatabaseHelper import DatabaseHelper

s= Session()

s.get("http://www.bcra.gob.ar/PublicacionesEstadisticas/Evolucion_moneda.asp")
Monedas=[{"nombre": "Pesos", "codigo": 5},
    {"nombre": "Pesos Chilenos", "codigo": 7},
    {"nombre": "Real", "codigo": 12},
    {"nombre": "Dolar estadounidense", "codigo": 2}]

dbh= DatabaseHelper()
#dbh.DBQuery("LOCK TABLES cotizacion_historico WRITE")
dbh.DBQuery("delete from cotizacion_historico")
for moneda in Monedas:
    payload={
        "Fecha":"2010.1.1",
        "Moneda":moneda['codigo']
    }
    r=s.post(url="http://www.bcra.gob.ar/PublicacionesEstadisticas/Evolucion_moneda_2.asp", data=payload)

    tree = html.fromstring(r.text)
    filas= tree.xpath("//table/tr")
    for fila in filas:
        arrayValores=[]
        arrayValores.append({"fecha":fila[0].text.replace("\r","").replace("\n","")})
        arrayValores.append({"equivausd":fila[1].text})
        arrayValores.append({"equivapeso":fila[2].text})
        arrayValores.append({"moneda":moneda['nombre']})
        dbh.DBQuery(dbh.constructorInsert("cotizacion_historico", arrayValores))
        print("Insertado: "+str(fila[0].text.replace("\r","").replace("\n",""))+"   "+ moneda['nombre'])

dbh.commit() 

dbh.DBQuery("UNLOCK TABLES")
