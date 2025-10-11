"""
Kite Connect Web Flow Integration for IPO Reminder
"""
import os
import json
import logging
from kiteconnect import KiteConnect
from flask import Flask, request, redirect, url_for, session, jsonify
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')

# Kite Connect API credentials
KITE_API_KEY = os.getenv('KITE_API_KEY')
KITE_API_SECRET = os.getenv('KITE_API_SECRET')
REDIRECT_URL = os.getenv('KITE_REDIRECT_URL', 'http://localhost:5000/callback')

# Initialize Kite Connect
kite = KiteConnect(api_key=KITE_API_KEY)

# Store access tokens (in production, use a proper database)
access_tokens = {}

@app.route('/')
def home():
    """Home page with login link"""
    if 'request_token' in session and session['request_token'] in access_tokens:
        return """
            <h1>IPO Reminder - Kite Connected</h1>
            <p>You are already authenticated with Kite!</p>
            <p><a href="/portfolio">View Portfolio</a></p>
            <p><a href="/logout">Logout</a></p>
        """
    return """
        <h1>IPO Reminder - Kite Connect</h1>
        <p><a href="/login">Login with Kite</a></p>
    """

@app.route('/login')
def login():
    ""
    Redirect to Kite's login page to get the request token
    """
    # Generate login URL
    login_url = kite.login_url()
    return redirect(login_url)

@app.route('/callback')
def callback():
    """
    Handle the callback from Kite after successful authentication
    """
    try:
        # Get the request token from the URL
        request_token = request.args.get('request_token')
        if not request_token:
            return "Error: No request token received", 400
        
        # Generate session data
        data = kite.generate_session(request_token, api_secret=KITE_API_SECRET)
        
        # Store the access token (in production, use a secure storage)
        access_tokens[request_token] = data['access_token']
        session['request_token'] = request_token
        
        # Set the access token for the Kite instance
        kite.set_access_token(data['access_token'])
        
        return """
            <h1>Successfully connected to Kite!</h1>
            <p>You can now close this window and return to the application.</p>
            <script>
                // Close the window after 3 seconds
                setTimeout(function() {
                    window.close();
                }, 3000);
            </script>
        """
    except Exception as e:
        logger.error(f"Error in callback: {str(e)}")
        return f"Error: {str(e)}", 500

@app.route('/portfolio')
def portfolio():
    """Example endpoint to fetch and display portfolio"""
    if 'request_token' not in session or session['request_token'] not in access_tokens:
        return redirect(url_for('login'))
    
    try:
        # Set the access token
        kite.set_access_token(access_tokens[session['request_token']])
        
        # Fetch portfolio
        portfolio = kite.holdings()
        return f"""
            <h1>Your Portfolio</h1>
            <pre>{json.dumps(portfolio, indent=2)}</pre>
            <p><a href="/">Home</a> | <a href="/logout">Logout</a></p>
        """
    except Exception as e:
        logger.error(f"Error fetching portfolio: {str(e)}")
        return f"Error: {str(e)}", 500

@app.route('/api/ipo_apply', methods=['POST'])
def apply_ipo():
    """API endpoint to apply for an IPO"""
    if 'request_token' not in session or session['request_token'] not in access_tokens:
        return jsonify({"error": "Not authenticated"}), 401
    
    try:
        data = request.json
        kite.set_access_token(access_tokens[session['request_token']])
        
        # Example: Apply for an IPO
        # Replace with actual IPO application logic
        result = {
            "status": "success",
            "message": "IPO application submitted successfully",
            "data": data
        }
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error applying for IPO: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/logout')
def logout():
    """Logout and clear session"""
    if 'request_token' in session:
        if session['request_token'] in access_tokens:
            del access_tokens[session['request_token']]
        session.pop('request_token', None)
    return redirect(url_for('home'))

def check_kite_credentials():
    """Check if Kite API credentials are set"""
    if not KITE_API_KEY or not KITE_API_SECRET:
        logger.error("Kite API credentials not found in environment variables")
        logger.info("Please set KITE_API_KEY and KITE_API_SECRET in your .env file")
        return False
    return True

if __name__ == '__main__':
    if check_kite_credentials():
        logger.info("Starting Kite Connect web server...")
        logger.info(f"Login URL: http://localhost:5000")
        app.run(debug=True)
    else:
        logger.error("Cannot start server: Missing Kite API credentials")
