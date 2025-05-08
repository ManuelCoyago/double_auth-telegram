import grpc
from generate import login_auth_pb2, login_auth_pb2_grpc


def main():
    canal = grpc.insecure_channel('localhost:50051')
    cliente = login_auth_pb2_grpc.LoginServiceStub(canal)

    print("=== Login ===")
    usuario = input("Usuario: ")
    contrasena = input("Contraseña: ")

    # Paso 1: Login
    respuesta = cliente.Login(login_auth_pb2.LoginRequest(
        usuario=usuario,
        contrasena=contrasena
    ))

    print(respuesta.mensaje)
    if not respuesta.exito:
        return

    # Paso 2: Código 2FA
    codigo = input("Ingresa el código recibido por Telegram: ")

    verificacion = cliente.VerificarCodigo(login_auth_pb2.CodigoRequest(
        usuario=usuario,
        codigo=codigo
    ))

    print(verificacion.mensaje)

if __name__ == '__main__':
    main()
