import socket

def cliente():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as cliente:
        cliente.connect(('127.0.0.1', 2345)) #conexion con el server en el puerto 2345, en la ip dada.

        fecha = input("Ingrese la fecha en formato YYYY-MM-DD: ") #solicita fecha para consultar al server

        #envia la fecha al servidor
        cliente.sendall(fecha.encode('utf-8'))

        #recibe la respuesta del servidor
        respuesta = cliente.recv(1024).decode('utf-8')

        print(respuesta)

if __name__ == "__main__":
    cliente() #ejecuta la funcion cuando el script se ejecuta como programa independiente.