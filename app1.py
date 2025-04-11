from flask import Flask, render_template, request, redirect, session, url_for
import requests
from urllib.parse import quote, urlencode  # Using Python's built-in instead
import os
from config import FHIR_SERVER, CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, SCOPE

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Helper function for FHIR requests
def make_fhir_request(url, access_token, params=None):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json'
    }
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/launch')
def launch():
    # Generate the authorization URL using standard library only
    auth_params = {
        'response_type': 'code',
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'scope': SCOPE,
        'aud': FHIR_SERVER,
        'state': '123'  # Should be random in production
    }
    
    if CLIENT_SECRET:
        auth_params['client_secret'] = CLIENT_SECRET
    
    auth_url = f"{FHIR_SERVER}/auth/authorize?{urlencode(auth_params)}"
    return redirect(auth_url)

@app.route('/callback')
def callback():
    # Handle callback
    code = request.args.get('code')
    if not code:
        return "Authorization failed: no code returned", 400
    
    # Token request using standard library only
    token_data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID
    }
    
    if CLIENT_SECRET:
        token_data['client_secret'] = CLIENT_SECRET
    
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    token_url = f"{FHIR_SERVER}/auth/token"
    
    try:
        response = requests.post(token_url, data=token_data, headers=headers)
        response.raise_for_status()
        token_response = response.json()
        
        session['access_token'] = token_response['access_token']
        session['patient_id'] = token_response.get('patient')
        
        return redirect(url_for('patient_details'))
    except requests.exceptions.RequestException as e:
        return f"Error during token exchange: {str(e)}", 500

@app.route('/patient')
def patient_details():
    if 'access_token' not in session or 'patient_id' not in session:
        return redirect(url_for('launch'))
    
    patient_url = f"{FHIR_SERVER}/Patient/{session['patient_id']}"
    patient_data = make_fhir_request(patient_url, session['access_token'])
    return render_template('patient.html', patient=patient_data)

@app.route('/observations')
def observations():
    if 'access_token' not in session or 'patient_id' not in session:
        return redirect(url_for('launch'))
    
    obs_url = f"{FHIR_SERVER}/Observation"
    params = {'patient': session['patient_id'], '_count': '100'}
    observations = make_fhir_request(obs_url, session['access_token'], params)
    return render_template('observations.html', observations=observations.get('entry', []))

@app.route('/documents')
def documents():
    if 'access_token' not in session or 'patient_id' not in session:
        return redirect(url_for('launch'))
    
    doc_url = f"{FHIR_SERVER}/DocumentReference"
    params = {'patient': session['patient_id'], '_count': '100'}
    documents = make_fhir_request(doc_url, session['access_token'], params)
    return render_template('documents.html', documents=documents.get('entry', []))

if __name__ == '__main__':
    app.run(port=8000, debug=True)