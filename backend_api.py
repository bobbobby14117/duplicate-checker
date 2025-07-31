# backend_api.py - Secure backend API for Google Sheets integration
from flask import Flask, jsonify, request
from flask_cors import CORS
import gspread
from google.oauth2.service_account import Credentials
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for your frontend domain

# ⚠️ UPDATE THESE VALUES WITH YOUR ACTUAL INFORMATION ⚠️
SERVICE_ACCOUNT_PATH = '/Users/simonbramwit/Desktop/MVP/Client Automator/georgia-companies-websites-1132cbbeacfa.json'
MASTER_SPREADSHEET_ID = '12G4hPC6X8o9Z68EAvGMuzRQ6M5eY4f5pfcNpDHuoBKQ'
MASTER_TAB_NAME = 'Sheet1'  # Change this to your actual tab name

# Google Sheets API scopes
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly"
]

def get_sheets_client():
    """Initialize and return Google Sheets client"""
    try:
        import os
        import json
        
        # Check if we're in production (environment variable) or local development (file)
        if 'SERVICE_ACCOUNT_JSON' in os.environ:
            # Production: use environment variable
            print("Using environment variable for credentials")
            service_account_info = json.loads(os.environ['SERVICE_ACCOUNT_JSON'])
            creds = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
        else:
            # Local development: use file
            print(f"Using file for credentials: {SERVICE_ACCOUNT_PATH}")
            creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_PATH, scopes=SCOPES)
        
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        print(f"Error initializing Google Sheets client: {e}")
        raise

@app.route('/api/master-data', methods=['GET'])
def get_master_data():
    """Fetch master database from Google Sheets"""
    try:
        client = get_sheets_client()
        sheet = client.open_by_key(MASTER_SPREADSHEET_ID)
        worksheet = sheet.worksheet(MASTER_TAB_NAME)
        
        # Get all records as dictionaries
        records = worksheet.get_all_records()
        
        # Validate that required columns exist
        if records and len(records) > 0:
            required_columns = ['Company / Account', 'Email', 'Lead Owner']
            first_record = records[0]
            missing_columns = [col for col in required_columns if col not in first_record]
            
            if missing_columns:
                return jsonify({
                    'error': f'Missing required columns: {", ".join(missing_columns)}',
                    'available_columns': list(first_record.keys())
                }), 400
        
        # Clean up empty rows
        cleaned_records = [record for record in records if any(str(value).strip() for value in record.values())]
        
        return jsonify({
            'success': True,
            'data': cleaned_records,
            'count': len(cleaned_records),
            'last_updated': 'Recently updated',
            'timestamp': datetime.now().isoformat()
        })
        
    except gspread.exceptions.SpreadsheetNotFound:
        return jsonify({'error': 'Spreadsheet not found. Check the spreadsheet ID and ensure the service account has access.'}), 404
    except gspread.exceptions.WorksheetNotFound:
        return jsonify({'error': f'Worksheet "{MASTER_TAB_NAME}" not found. Check the tab name.'}), 404
    except FileNotFoundError:
        return jsonify({'error': 'Service account file not found. Check the SERVICE_ACCOUNT_PATH.'}), 500
    except Exception as e:
        return jsonify({'error': f'Failed to fetch data: {str(e)}'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy', 
        'service': 'sheets-api',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/test-connection', methods=['GET'])
def test_connection():
    """Test Google Sheets connection without fetching full data"""
    try:
        client = get_sheets_client()
        sheet = client.open_by_key(MASTER_SPREADSHEET_ID)
        worksheet = sheet.worksheet(MASTER_TAB_NAME)
        
        # Just get the header row to test connection
        headers = worksheet.row_values(1)
        
        return jsonify({
            'success': True,
            'message': 'Connection successful',
            'spreadsheet_title': sheet.title,
            'worksheet_title': worksheet.title,
            'headers': headers,
            'row_count': worksheet.row_count,
            'col_count': worksheet.col_count
        })
        
    except Exception as e:
        return jsonify({'error': f'Connection test failed: {str(e)}'}), 500

if __name__ == '__main__':
    # Validate configuration before starting
    print("=" * 50)
    print("🚀 STARTING FLASK BACKEND SERVER")
    print("=" * 50)
    
    if not os.path.exists(SERVICE_ACCOUNT_PATH):
        print(f"❌ WARNING: Service account file not found at: {SERVICE_ACCOUNT_PATH}")
        print("   Please update SERVICE_ACCOUNT_PATH with the correct path to your credentials file.")
    else:
        print(f"✅ Service account file found: {SERVICE_ACCOUNT_PATH}")
    
    if MASTER_SPREADSHEET_ID == 'your_master_spreadsheet_id_here':
        print("❌ WARNING: MASTER_SPREADSHEET_ID not configured.")
        print("   Please update with your actual spreadsheet ID.")
    else:
        print(f"✅ Spreadsheet ID configured: {MASTER_SPREADSHEET_ID}")
    
    print(f"✅ Tab name: {MASTER_TAB_NAME}")
    print()
    print("API endpoints available:")
    print("  - Health check: http://localhost:5000/api/health")
    print("  - Test connection: http://localhost:5000/api/test-connection")
    print("  - Master data: http://localhost:5000/api/master-data")
    print()
    print("Starting server on http://localhost:5000")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
