from bingads.authorization import OAuthDesktopMobileAuthCodeGrant
import webbrowser

CLIENT_ID = 'e4a874de-e38d-43a6-b310-adc38593708f'
ENVIRONMENT = 'production'

auth = OAuthDesktopMobileAuthCodeGrant(client_id=CLIENT_ID, env=ENVIRONMENT)
auth_url = auth.get_authorization_endpoint()

# Abre la URL en el navegador
webbrowser.open(auth_url)
print("Por favor, autoriza la aplicación en el navegador y copia la URL completa aquí:")

# Pide al usuario ingresar la URL completa después de autenticarse
response_uri = input("Ingresa la URL aquí: ")

# Solicita los tokens
tokens = auth.request_oauth_tokens_by_response_uri(response_uri=response_uri)

# Guarda el nuevo refresh token
with open("refresh.txt", "w") as file:
    file.write(tokens.refresh_token)

print("Nuevo refresh token guardado exitosamente.")
