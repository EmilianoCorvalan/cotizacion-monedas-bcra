import socket

def cliente():
    # Lógica para el programa cliente
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as cliente:
        cliente.connect(('127.0.0.1', 2345))

        fecha = input("Ingrese la fecha en formato YYYY-MM-DD: ")

        # Envia la fecha al servidor
        cliente.sendall(fecha.encode('utf-8'))

        # Recibe la respuesta del servidor
        respuesta = cliente.recv(1024).decode('utf-8')

        print(respuesta)

if __name__ == "__main__":
    cliente()