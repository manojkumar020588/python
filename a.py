

# =============================================================================
# # Replace these values with your Cerner app credentials
# CLIENT_ID = 'd9a79904-a8d5-4917-95ee-a535c9ece724'
# REDIRECT_URI = 'http://127.0.0.1:5000/callback'  # This must match the redirect URI in Cerner portal
# FHIR_BASE_URL = 'https://fhir-ehr.sandboxcerner.com/r4/ec2458f2-1e24-41c8-b71b-0e701af7583d'  # Replace with your tenant ID (EHR org ID)
# AUTH_URL = 'https://authorization.cerner.com/tenants/ec2458f2-1e24-41c8-b71b-0e701af7583d/protocols/oauth2/profiles/smart-v1/personas/provider/authorize'
# TOKEN_URL = 'https://authorization.cerner.com/tenants/ec2458f2-1e24-41c8-b71b-0e701af7583d/protocols/oauth2/profiles/smart-v1/token'
# SCOPES = 'launch openid fhirUser patient/Patient.read'  # Scope for reading patient data
# 
# 
# =============================================================================
import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import requests
from urllib.parse import urlencode
import uuid
import json

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Configuration - replace these with your actual Cerner credentials
CERNER_CONFIG = {
    'client_id': os.getenv('CERNER_CLIENT_ID', 'd9a79904-a8d5-4917-95ee-a535c9ece724'),
    'client_secret': os.getenv('CERNER_CLIENT_SECRET', None),  # Optional
    'auth_url': 'https://authorization.cerner.com/tenants/your-tenant-id/protocols/oauth2/profiles/smart-v1/personas/provider/authorize',
    'token_url': 'https://authorization.cerner.com/tenants/your-tenant-id/protocols/oauth2/profiles/smart-v1/token',
    'redirect_uri': 'http://127.0.0.1:5000/callback',
    'scope': 'patient/Patient.read patient/Observation.read launch online_access openid profile',
    'fhir_base_url': 'https://fhir-ehr-code.cerner.com/r4/ec2458f2-1e24-41c8-b71b-0e701af7583d'
}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login')
def login():
    # Generate a unique state value for CSRF protection
    state = str(uuid.uuid4())
    session['oauth_state'] = state
    
    # Create the authorization URL
    params = {
        'response_type': 'code',
        'client_id': CERNER_CONFIG['client_id'],
        'redirect_uri': CERNER_CONFIG['redirect_uri'],
        'scope': CERNER_CONFIG['scope'],
        'state': state,
        'aud': CERNER_CONFIG['fhir_base_url']
    }
    
    auth_url = f"{CERNER_CONFIG['auth_url']}?{urlencode(params)}"
    return redirect(auth_url)

@app.route('/callback')
def callback():
    # Verify the state matches what we sent
    if request.args.get('state') != session.get('oauth_state'):
        return "State mismatch error", 400
    
    code = request.args.get('code')
    if not code:
        return "Authorization code missing", 400
    
    # Prepare token request
    token_data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': CERNER_CONFIG['redirect_uri'],
        'client_id': CERNER_CONFIG['client_id']
    }
    
    # Include client_secret only if it's provided
    if CERNER_CONFIG['client_secret']:
        token_data['client_secret'] = CERNER_CONFIG['client_secret']
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json'
    }
    
    # Request tokens
    response = requests.post(
        CERNER_CONFIG['token_url'],
        data=token_data,
        headers=headers
    )
    
    if response.status_code != 200:
        return f"Token request failed: {response.text}", 400
    
    tokens = response.json()
    session['access_token'] = tokens['access_token']
    session['patient_id'] = tokens.get('patient')  # SMART launch context may provide patient ID
    
    return redirect(url_for('patient_data'))

@app.route('/patient-data')
def patient_data():
    if 'access_token' not in session:
        return redirect(url_for('login'))
    
    return render_template('patient.html')

@app.route('/api/patient')
def get_patient():
    if 'access_token' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    patient_id = session.get('patient_id')
    if not patient_id:
        return jsonify({'error': 'No patient ID in session'}), 400
    
    headers = {
        'Authorization': f'Bearer {session["access_token"]}',
        'Accept': 'application/json'
    }
    
    # Fetch patient details
    patient_url = f"{CERNER_CONFIG['fhir_base_url']}/Patient/{patient_id}"
    response = requests.get(patient_url, headers=headers)
    
    if response.status_code != 200:
        return jsonify({'error': 'Failed to fetch patient data', 'details': response.text}), 400
    
    patient_data = response.json()
    
    # Fetch patient observations (example of additional data)
    observations_url = f"{CERNER_CONFIG['fhir_base_url']}/Observation?patient={patient_id}&category=vital-signs&_count=10"
    observations_response = requests.get(observations_url, headers=headers)
    observations = observations_response.json() if observations_response.status_code == 200 else None
    
    return jsonify({
        'patient': patient_data,
        'observations': observations
    })

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)