from flask import Flask, render_template_string, request, session, jsonify
import random
import os
import time
from datetime import datetime, timedelta
import hashlib

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'  # Change this in production

# Rate limiting storage (in production, use Redis)
user_requests = {}
COOLDOWN_HOURS = 24  # 24 hour cooldown per user

def get_user_id():
    """Generate unique user ID based on IP and User-Agent"""
    ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    user_agent = request.headers.get('User-Agent', '')
    return hashlib.md5(f"{ip}:{user_agent}".encode()).hexdigest()

def is_rate_limited():
    """Check if user is rate limited"""
    user_id = get_user_id()
    current_time = datetime.now()
    
    if user_id in user_requests:
        last_request = user_requests[user_id]
        if current_time - last_request < timedelta(hours=COOLDOWN_HOURS):
            return True
    
    return False

def update_rate_limit():
    """Update user's last request time"""
    user_id = get_user_id()
    user_requests[user_id] = datetime.now()

def get_random_account():
    """Get random account from accounts.txt"""
    try:
        if not os.path.exists('accounts.txt'):
            return None
        
        with open('accounts.txt', 'r') as f:
            accounts = [line.strip() for line in f if line.strip() and ':' in line]
        
        if not accounts:
            return None
        
        return random.choice(accounts)
    except Exception as e:
        print(f"Error reading accounts: {e}")
        return None

# HTML Template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CrunchyFree - Premium Account Hub</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Arial', sans-serif;
            background: linear-gradient(135deg, #000 0%, #1a1a1a 100%);
            color: white;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .container {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 107, 53, 0.3);
            border-radius: 20px;
            padding: 40px;
            text-align: center;
            max-width: 500px;
            width: 90%;
            box-shadow: 0 25px 45px rgba(0, 0, 0, 0.3);
        }

        .logo {
            font-size: 2.5em;
            font-weight: bold;
            color: #FF6B35;
            margin-bottom: 10px;
            text-shadow: 0 0 20px rgba(255, 107, 53, 0.5);
        }

        .subtitle {
            color: #ccc;
            margin-bottom: 30px;
            font-size: 1.1em;
        }

        .account-box {
            background: rgba(255, 107, 53, 0.1);
            border: 2px solid #FF6B35;
            border-radius: 15px;
            padding: 20px;
            margin: 20px 0;
            font-family: 'Courier New', monospace;
            word-break: break-all;
        }

        .account-text {
            font-size: 1.2em;
            color: #FF6B35;
            font-weight: bold;
        }

        .btn {
            background: linear-gradient(45deg, #FF6B35, #ff8c42);
            color: white;
            border: none;
            padding: 15px 30px;
            font-size: 1.1em;
            border-radius: 25px;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 10px 20px rgba(255, 107, 53, 0.3);
            font-weight: bold;
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 15px 30px rgba(255, 107, 53, 0.4);
        }

        .btn:disabled {
            background: #666;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }

        .copy-btn {
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid #FF6B35;
            color: #FF6B35;
            padding: 8px 15px;
            margin-top: 10px;
            border-radius: 20px;
            font-size: 0.9em;
        }

        .warning {
            background: rgba(255, 255, 0, 0.1);
            border: 1px solid #ffcc00;
            border-radius: 10px;
            padding: 15px;
            margin: 20px 0;
            color: #ffcc00;
            font-size: 0.9em;
        }

        .error {
            background: rgba(255, 0, 0, 0.1);
            border: 1px solid #ff4444;
            border-radius: 10px;
            padding: 15px;
            margin: 20px 0;
            color: #ff4444;
        }

        .cooldown {
            color: #ff4444;
            font-size: 1.1em;
            margin: 20px 0;
        }

        .footer {
            margin-top: 30px;
            color: #666;
            font-size: 0.8em;
        }

        .pulse {
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.7; }
            100% { opacity: 1; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo pulse">CrunchyFree</div>
        <div class="subtitle">Premium Account Hub</div>
        
        {% if error %}
            <div class="error">{{ error }}</div>
        {% elif cooldown %}
            <div class="cooldown">
                ⏰ Please wait {{ cooldown }} hours before getting another account
            </div>
        {% elif account %}
            <div class="account-box">
                <div class="account-text">{{ account }}</div>
                <button class="btn copy-btn" onclick="copyAccount()">📋 Copy Account</button>
            </div>
            <div class="warning">
                ⚠️ One account per 24 hours | Account shared with multiple users | Change password after first login
            </div>
        {% else %}
            <button class="btn" onclick="getAccount()" id="getBtn">
                🎁 Get Free Premium Account
            </button>
        {% endif %}
        
        <div class="footer">
            Powered by CrunchyFree Hub | Legitimate Licensed Provider
        </div>
    </div>

    <script>
        function getAccount() {
            const btn = document.getElementById('getBtn');
            btn.disabled = true;
            btn.innerHTML = '⏳ Getting Account...';
            
            fetch('/get-account', {method: 'POST'})
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        location.reload();
                    } else {
                        alert(data.error);
                        btn.disabled = false;
                        btn.innerHTML = '🎁 Get Free Premium Account';
                    }
                })
                .catch(error => {
                    alert('Error occurred. Please try again later.');
                    btn.disabled = false;
                    btn.innerHTML = '🎁 Get Free Premium Account';
                });
        }

        function copyAccount() {
            const accountText = document.querySelector('.account-text').textContent;
            navigator.clipboard.writeText(accountText).then(() => {
                const btn = event.target;
                const originalText = btn.innerHTML;
                btn.innerHTML = '✅ Copied!';
                setTimeout(() => {
                    btn.innerHTML = originalText;
                }, 2000);
            });
        }

        // Prevent refresh exploitation
        if (performance.navigation.type === performance.navigation.TYPE_RELOAD) {
            if (sessionStorage.getItem('accountGiven')) {
                // User already got account this session
            }
        }

        // Disable common refresh shortcuts
        document.addEventListener('keydown', function(e) {
            if (e.key === 'F5' || (e.ctrlKey && e.key === 'r')) {
                if (document.querySelector('.account-text')) {
                    e.preventDefault();
                    alert('Please wait 24 hours before getting another account');
                }
            }
        });
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    # Check if user is coming from pocolinks.com
    referer = request.headers.get('Referer', '')
    if 'pocolinks.com' not in referer and request.args.get('source') != 'pocolinks':
        # Optional: You can add stricter referrer checking here
        pass
    
    account = session.get('account')
    error = session.get('error')
    cooldown_hours = None
    
    # Clear session messages
    session.pop('error', None)
    
    # Check cooldown
    if is_rate_limited() and not account:
        user_id = get_user_id()
        if user_id in user_requests:
            time_diff = datetime.now() - user_requests[user_id]
            remaining = timedelta(hours=COOLDOWN_HOURS) - time_diff
            cooldown_hours = round(remaining.total_seconds() / 3600, 1)
    
    return render_template_string(HTML_TEMPLATE, 
                                account=account, 
                                error=error, 
                                cooldown=cooldown_hours)

@app.route('/get-account', methods=['POST'])
def get_account():
    # Rate limiting check
    if is_rate_limited():
        return jsonify({'success': False, 'error': 'Please wait 24 hours between requests'})
    
    # Check if user already has account in session
    if session.get('account'):
        return jsonify({'success': False, 'error': 'You already have an account for this session'})
    
    # Get random account
    account = get_random_account()
    if not account:
        return jsonify({'success': False, 'error': 'No accounts available at the moment'})
    
    # Update rate limit and session
    update_rate_limit()
    session['account'] = account
    session.permanent = True
    
    return jsonify({'success': True})

@app.route('/health')
def health():
    """Health check endpoint"""
    account_count = 0
    try:
        if os.path.exists('accounts.txt'):
            with open('accounts.txt', 'r') as f:
                account_count = len([line for line in f if line.strip() and ':' in line])
    except:
        pass
    
    return jsonify({
        'status': 'healthy',
        'accounts_available': account_count,
        'active_users': len(user_requests)
    })

if __name__ == '__main__':
    # Set session lifetime
    app.permanent_session_lifetime = timedelta(hours=24)
    
    # Create accounts.txt if it doesn't exist
    if not os.path.exists('accounts.txt'):
        with open('accounts.txt', 'w') as f:
            f.write("demo@example.com:password123\ntest@example.com:password456\n")
    
    app.run(debug=False, host='0.0.0.0', port=5000)