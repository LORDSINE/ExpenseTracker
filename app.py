from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from datetime import datetime, date
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# Database configuration - use in-memory SQLite for Vercel
if os.environ.get('VERCEL'):
    # For Vercel deployment - use in-memory SQLite
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
else:
    # For local development
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expense_tracker.db'
    
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# Database initialization functions (defined early to avoid circular imports)
_db_initialized = False

def ensure_db():
    """Ensure database is initialized before use"""
    global _db_initialized
    if not _db_initialized:
        try:
            with app.app_context():
                db.create_all()
                _db_initialized = True
                print("Database initialized on demand")
        except Exception as e:
            print(f"Error initializing database on demand: {str(e)}")
    return _db_initialized

def init_db():
    """Initialize database tables if they don't exist"""
    return ensure_db()

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    try:
        # Ensure database is ready before querying
        if not ensure_db():
            return None
        return User.query.get(int(user_id))
    except Exception as e:
        print(f"Error loading user {user_id}: {str(e)}")
        return None

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with transactions
    transactions = db.relationship('Transaction', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.username}>'

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(10), nullable=False)  # 'income' or 'expense'
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200))
    date = db.Column(db.Date, nullable=False, default=date.today)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign key to link with user
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f'<Transaction {self.type}: {self.amount}>'

# Categories for different transaction types
INCOME_CATEGORIES = [
    ('salary', 'Salary'),
    ('freelance', 'Freelance'),
    ('investment', 'Investment'),
    ('business', 'Business'),
    ('gift', 'Gift'),
    ('other_income', 'Other Income')
]

EXPENSE_CATEGORIES = [
    ('food', 'Food & Dining'),
    ('transportation', 'Transportation'),
    ('shopping', 'Shopping'),
    ('entertainment', 'Entertainment'),
    ('bills', 'Bills & Utilities'),
    ('healthcare', 'Healthcare'),
    ('education', 'Education'),
    ('travel', 'Travel'),
    ('housing', 'Housing'),
    ('other_expense', 'Other Expense')
]

# Error Handlers
@app.errorhandler(500)
def internal_error(error):
    """Handle internal server errors"""
    print(f"Internal server error: {str(error)}")
    try:
        db.session.rollback()
    except Exception as db_error:
        print(f"Could not rollback database session: {str(db_error)}")
    return "Internal Server Error", 500

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    return redirect(url_for('login'))

@app.errorhandler(Exception)
def handle_exception(e):
    """Handle all unhandled exceptions"""
    print(f"Unhandled exception: {str(e)}")
    try:
        db.session.rollback()
    except Exception as db_error:
        print(f"Could not rollback database session: {str(db_error)}")
    return redirect(url_for('login'))

# Routes
@app.route('/health')
def health_check():
    """Simple health check that doesn't depend on database or auth"""
    return {
        'status': 'ok', 
        'message': 'Flask app is running',
        'environment': 'vercel' if os.environ.get('VERCEL') else 'local'
    }

@app.route('/test')
def test_route():
    """Test route for debugging"""
    try:
        return f"<h1>Flask Test Route</h1><p>Environment: {os.environ.get('VERCEL', 'local')}</p>"
    except Exception as e:
        return f"<h1>Error in test route</h1><p>{str(e)}</p>"

@app.route('/init-db')
def init_db_route():
    """Initialize database on demand"""
    try:
        success = init_db()
        if success:
            return {"status": "success", "message": "Database initialized"}
        else:
            return {"status": "error", "message": "Failed to initialize database"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.route('/debug')
def debug_info():
    """Debug information route"""
    try:
        import sys
        return {
            "status": "ok",
            "python_version": sys.version,
            "flask_version": app.config.get('VERSION', 'unknown'),
            "environment_vars": {
                "VERCEL": os.environ.get('VERCEL', 'not set'),
                "FLASK_ENV": os.environ.get('FLASK_ENV', 'not set')
            },
            "database_config": app.config.get('SQLALCHEMY_DATABASE_URI', 'not set')
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Simple login page that doesn't require database
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Simple login page"""
    try:
        if request.method == 'POST':
            try:
                if not ensure_db():
                    return "<h1>Database Error</h1><p>Could not initialize database</p><a href='/login'>Try Again</a>"
                    
                username = request.form.get('username')
                password = request.form.get('password')
                
                user = User.query.filter_by(username=username).first()
                
                if user and bcrypt.check_password_hash(user.password_hash, password):
                    login_user(user)
                    return redirect(url_for('dashboard'))
                else:
                    return "<h1>Login Failed</h1><p>Invalid credentials</p><a href='/login'>Try Again</a>"
            except Exception as e:
                return f"<h1>Login Error</h1><p>{str(e)}</p><a href='/login'>Try Again</a>"
        
        # Try to render template, fallback to plain HTML if it fails
        try:
            return render_template('login.html')
        except:
            return """
            <html>
            <head><title>Login - Expense Tracker</title></head>
            <body>
                <h1>Login</h1>
                <form method="POST">
                    <p>
                        <label>Username:</label><br>
                        <input type="text" name="username" required>
                    </p>
                    <p>
                        <label>Password:</label><br>
                        <input type="password" name="password" required>
                    </p>
                    <p>
                        <input type="submit" value="Log In">
                    </p>
                </form>
                <p><a href="/register">Don't have an account? Sign up</a></p>
            </body>
            </html>
            """
    
    except Exception as e:
        # Fallback to simple HTML form if template fails
        return f"""
        <html>
        <head><title>Login - Expense Tracker</title></head>
        <body>
            <h1>Login</h1>
            <p>Error: {str(e)}</p>
            <form method="POST">
                <p>Username: <input type="text" name="username" required></p>
                <p>Password: <input type="password" name="password" required></p>
                <p><input type="submit" value="Login"></p>
            </form>
            <p><a href="/register">Register</a></p>
        </body>
        </html>
        """

@app.route('/register', methods=['GET', 'POST'])  
def register():
    """User registration"""
    try:
        if request.method == 'POST':
            try:
                if not ensure_db():
                    return "<h1>Database Error</h1><p>Could not initialize database</p><a href='/register'>Try Again</a>"
                
                # Get form data directly
                first_name = request.form.get('first_name')
                last_name = request.form.get('last_name')
                username = request.form.get('username')
                email = request.form.get('email')
                password = request.form.get('password')
                
                if not all([first_name, last_name, username, email, password]):
                    return "<h1>Registration Error</h1><p>All fields are required</p><a href='/register'>Try Again</a>"
                
                # Check if user already exists
                existing_user = User.query.filter(
                    (User.username == username) | 
                    (User.email == email)
                ).first()
                
                if existing_user:
                    return "<h1>Registration Error</h1><p>Username or email already exists</p><a href='/register'>Try Again</a>"
                
                # Create new user
                hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
                user = User(
                    first_name=first_name,
                    last_name=last_name,
                    username=username,
                    email=email,
                    password_hash=hashed_password
                )
                
                db.session.add(user)
                db.session.commit()
                
                return "<h1>Success!</h1><p>Registration successful!</p><a href='/login'>Login Now</a>"
                
            except Exception as e:
                try:
                    db.session.rollback()
                except:
                    pass
                return f"<h1>Registration Error</h1><p>{str(e)}</p><a href='/register'>Try Again</a>"
        
        # Try to render template, fallback to simple HTML
        try:
            return render_template('register.html')
        except Exception as template_error:
            return """
            <html>
            <head><title>Register - Expense Tracker</title></head>
            <body>
                <h1>Register</h1>
                <form method="POST">
                    <p>First Name: <input type="text" name="first_name" required></p>
                    <p>Last Name: <input type="text" name="last_name" required></p>
                    <p>Username: <input type="text" name="username" required></p>
                    <p>Email: <input type="email" name="email" required></p>
                    <p>Password: <input type="password" name="password" required></p>
                    <p><input type="submit" value="Register"></p>
                </form>
                <p><a href="/login">Already have an account? Login</a></p>
            </body>
            </html>
            """
    
    except Exception as e:
        return f"<h1>System Error</h1><p>{str(e)}</p><a href='/'>Home</a>"

@app.route('/')
def landing():
    """Landing page that redirects based on authentication status"""
    try:
        # Ensure database is initialized
        ensure_db()
        
        # Safe check for authentication in serverless environment
        try:
            if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
                return redirect(url_for('dashboard'))
        except Exception as auth_error:
            print(f"Authentication check error: {str(auth_error)}")
        
        # Default to login page
        return redirect(url_for('login'))
    except Exception as e:
        print(f"Error in landing route: {str(e)}")
        return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        # Ensure database is initialized
        if not ensure_db():
            raise Exception("Database initialization failed")
            
        # Get recent transactions for current user
        recent_transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.created_at.desc()).limit(10).all()
        
        # Calculate totals for current user
        total_income = db.session.query(db.func.sum(Transaction.amount)).filter_by(user_id=current_user.id, type='income').scalar() or 0
        total_expense = db.session.query(db.func.sum(Transaction.amount)).filter_by(user_id=current_user.id, type='expense').scalar() or 0
        balance = total_income - total_expense
        
        return render_template('index.html', 
                             transactions=recent_transactions,
                             total_income=total_income,
                             total_expense=total_expense,
                             balance=balance)
    except Exception as e:
        print(f"Error in dashboard route: {str(e)}")
        # Return a simple page if database operations fail
        return render_template('index.html', 
                             transactions=[],
                             total_income=0,
                             total_expense=0,
                             balance=0)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/favicon.ico')
def favicon():
    return redirect(url_for('static', filename='favicon.ico'))

if __name__ == '__main__':
    init_db()
    app.run()
else:
    # For serverless deployment (Vercel) - delay database initialization
    pass

# For Vercel deployment
vercel_app = app