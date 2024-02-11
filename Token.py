import os
import requests
from dotenv import load_dotenv

load_dotenv(".env.local")


client_id = os.getenv('TWITCH_CLIENT_ID')
client_secret = os.getenv('TWITCH_CLIENT_SECRET')
grant_type = 'client_credentials'
scope = 'chat:read chat:edit'  # Adjust the scope based on your bot's requirements

# Make the HTTP POST request
response = requests.post(
    'https://id.twitch.tv/oauth2/token',
    params={
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': grant_type,
        'scope': scope
    }
)

# Parse the JSON response
data = response.json()

# Extract the OAuth token
oauth_token = data['access_token']

print("OAuth Token:", oauth_token)
