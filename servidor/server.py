import grpc
from concurrent import futures
import json
import random
import requests

from generate import login_auth_pb2_grpc, login_auth_pb2

# Base en memoria para guardar códigos 2FA generados
codigos_activos = {}

# Cargar usuarios desde JSON
def cargar_usuarios():
    with open('usuarios.json', 'r') as f:  # Asegúrate que la ruta es correcta
        return json.load(f)['users']

# Buscar usuario por correo (email)
def buscar_usuario(email, usuarios):
    for usuario in usuarios:
        if usuario['email'] == email:
            return usuario
    return None

# Enviar código 2FA por Telegram (incluyendo correo)
def enviar_codigo_telegram(bot_token, chat_id, email, codigo):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': f'Correo: {email}\nTu código de verificación es: {codigo}'
    }
    response = requests.post(url, data=payload)
    return response.ok

# Implementación del servicio gRPC
class LoginServiceServicer(login_auth_pb2_grpc.LoginServiceServicer):
    def __init__(self):
        self.usuarios = cargar_usuarios()

    def Login(self, request, context):
        usuario = request.usuario  # Aquí recibes el email
        contrasena = request.contrasena

        # Buscar usuario por correo
        user_data = buscar_usuario(usuario, self.usuarios)

        if user_data and user_data['password'] == contrasena:
            # Generar código 2FA
            codigo = str(random.randint(100000, 999999))
            codigos_activos[usuario] = codigo

            # Enviar código por Telegram (incluyendo correo)
            bot_token = user_data['bot_token']
            chat_id = user_data['chat_id']

            ok = enviar_codigo_telegram(bot_token, chat_id, usuario, codigo)

            if ok:
                return login_auth_pb2.LoginResponse(
                    exito=True,
                    mensaje="Credenciales correctas. Código 2FA enviado."
                )
            else:
                return login_auth_pb2.LoginResponse(
                    exito=False,
                    mensaje="Error al enviar código 2FA por Telegram."
                )
        else:
            return login_auth_pb2.LoginResponse(
                exito=False,
                mensaje="Usuario o contraseña incorrectos."
            )

    def VerificarCodigo(self, request, context):
        usuario = request.usuario
        codigo = request.codigo

        if usuario in codigos_activos and codigos_activos[usuario] == codigo:
            del codigos_activos[usuario]  # Código usado, eliminarlo
            return login_auth_pb2.CodigoResponse(
                exito=True,
                mensaje=f"Bienvenido, {usuario}!"
            )
        else:
            return login_auth_pb2.CodigoResponse(
                exito=False,
                mensaje="Código incorrecto."
            )

def servir():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    login_auth_pb2_grpc.add_LoginServiceServicer_to_server(LoginServiceServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Servidor gRPC iniciado en puerto 50051.")
    server.wait_for_termination()

if __name__ == '__main__':
    servir()
