# Configuration for SMART on FHIR app
FHIR_SERVER = "https://launch.smarthealthit.org/v/r4/fhir"  # Replace with your FHIR server
CLIENT_ID = "d9a79904-a8d5-4917-95ee-a535c9ece724"  # Replace with your client ID
CLIENT_SECRET = None  # Optional - set if your server requires it
REDIRECT_URI = "http://localhost:8000/callback"  # Must match your app registration
SCOPE =  "patient/Patient.rs patient/Observation.rs launch offline_access openid fhirUser"