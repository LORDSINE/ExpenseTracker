from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from datetime import datetime, date
import os
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config['DEBUG'] = True
app.config['TEMPLATES_AUTO_RELOAD'] = True

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
    return render_template('404.html', 
                         cache_buster=int(time.time()),
                         current_year=datetime.now().year), 404

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

@app.route('/add_transaction', methods=['GET', 'POST'])
@login_required
def add_transaction():
    """Add a new transaction"""
    try:
        if not ensure_db():
            return "<h1>Database Error</h1><p>Could not initialize database</p><a href='/dashboard'>Back to Dashboard</a>"
            
        if request.method == 'POST':
            try:
                transaction_type = request.form.get('type')
                amount = request.form.get('amount')
                category = request.form.get('category')
                description = request.form.get('description')
                date_str = request.form.get('date')
                
                if not all([transaction_type, amount, category, date_str]):
                    return "<h1>Error</h1><p>All fields are required</p><a href='/add_transaction'>Try Again</a>"
                
                # Parse date
                from datetime import datetime
                try:
                    transaction_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                except ValueError:
                    return "<h1>Error</h1><p>Invalid date format</p><a href='/add_transaction'>Try Again</a>"
                
                # Parse amount
                try:
                    amount_float = float(amount)
                    if amount_float <= 0:
                        return "<h1>Error</h1><p>Amount must be positive</p><a href='/add_transaction'>Try Again</a>"
                except ValueError:
                    return "<h1>Error</h1><p>Invalid amount</p><a href='/add_transaction'>Try Again</a>"
                
                # Create transaction
                transaction = Transaction(
                    user_id=current_user.id,
                    type=transaction_type,
                    amount=amount_float,
                    category=category,
                    description=description,
                    date=transaction_date
                )
                
                db.session.add(transaction)
                db.session.commit()
                
                return redirect(url_for('dashboard'))
                
            except Exception as e:
                try:
                    db.session.rollback()
                except:
                    pass
                return f"<h1>Transaction Error</h1><p>{str(e)}</p><a href='/add_transaction'>Try Again</a>"
        
        # GET request - return direct HTML instead of template
        return """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Add Transaction - Expense Tracker</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        </head>
        <body>
            <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
                <div class="container">
                    <a class="navbar-brand" href="/dashboard">
                        <i class="fas fa-chart-line me-2"></i>Expense Tracker
                    </a>
                </div>
            </nav>
            
            <div class="container mt-4">
                <div class="row justify-content-center">
                    <div class="col-md-8 col-lg-6">
                        <div class="card shadow">
                            <div class="card-header bg-primary text-white text-center">
                                <h2 class="mb-1">
                                    <i class="fas fa-plus-circle me-2"></i>Add New Transaction
                                </h2>
                                <p class="mb-0 opacity-75">Track your income and expenses</p>
                            </div>
                            <div class="card-body p-4">
                                <form method="POST">
                                    <div class="row mb-3">
                                        <div class="col-md-6">
                                            <label for="type" class="form-label fw-bold">
                                                <i class="fas fa-exchange-alt text-primary me-2"></i>Transaction Type
                                            </label>
                                            <select name="type" id="type" class="form-select form-select-lg" required>
                                                <option value="">Choose Type...</option>
                                                <option value="income">💰 Income</option>
                                                <option value="expense">💸 Expense</option>
                                            </select>
                                        </div>
                                        <div class="col-md-6">
                                            <label for="amount" class="form-label fw-bold">
                                                <i class="fas fa-dollar-sign text-success me-2"></i>Amount
                                            </label>
                                            <div class="input-group input-group-lg">
                                                <span class="input-group-text">Rs.</span>
                                                <input type="number" name="amount" id="amount" class="form-control" 
                                                       step="0.01" min="0.01" placeholder="0.00" required>
                                            </div>
                                        </div>
                                    </div>

                                    <div class="mb-3">
                                        <label for="category" class="form-label fw-bold">
                                            <i class="fas fa-tags text-info me-2"></i>Category
                                        </label>
                                        <select name="category" id="category" class="form-select form-select-lg" required>
                                            <option value="">Select Category...</option>
                                            <optgroup label="💰 Income Categories" id="income-categories" style="display: none;">
                                                <option value="salary">Salary</option>
                                                <option value="freelance">Freelance</option>
                                                <option value="investment">Investment</option>
                                                <option value="gift">Gift</option>
                                                <option value="other_income">Other Income</option>
                                            </optgroup>
                                            <optgroup label="💸 Expense Categories" id="expense-categories" style="display: none;">
                                                <option value="food">Food</option>
                                                <option value="transport">Transport</option>
                                                <option value="housing">Housing</option>
                                                <option value="utilities">Utilities</option>
                                                <option value="entertainment">Entertainment</option>
                                                <option value="health">Health</option>
                                                <option value="shopping">Shopping</option>
                                                <option value="other_expense">Other Expense</option>
                                            </optgroup>
                                        </select>
                                    </div>

                                    <div class="mb-3">
                                        <label for="description" class="form-label fw-bold">
                                            <i class="fas fa-sticky-note text-warning me-2"></i>Description 
                                            <small class="text-muted fw-normal">(Optional)</small>
                                        </label>
                                        <textarea name="description" id="description" class="form-control" 
                                                  rows="3" placeholder="Enter transaction details..."></textarea>
                                    </div>

                                    <div class="mb-4">
                                        <label for="date" class="form-label fw-bold">
                                            <i class="fas fa-calendar-alt text-danger me-2"></i>Date
                                        </label>
                                        <input type="date" name="date" id="date" class="form-control form-control-lg" required>
                                    </div>

                                    <div class="d-grid gap-2 mb-3">
                                        <button type="submit" class="btn btn-success btn-lg py-3">
                                            <i class="fas fa-plus-circle me-2"></i>Add Transaction
                                        </button>
                                    </div>
                                </form>
                                
                                <div class="text-center">
                                    <a href="/dashboard" class="btn btn-outline-secondary btn-lg">
                                        <i class="fas fa-arrow-left me-2"></i>Back to Dashboard
                                    </a>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <script>
            document.addEventListener('DOMContentLoaded', function() {
                console.log('Direct HTML template loaded - STYLING SHOULD WORK NOW!');
                
                const typeSelect = document.getElementById('type');
                const categorySelect = document.getElementById('category');
                const incomeCategories = document.getElementById('income-categories');
                const expenseCategories = document.getElementById('expense-categories');
                
                // Set today's date as default
                const dateInput = document.getElementById('date');
                const today = new Date().toISOString().split('T')[0];
                dateInput.value = today;
                
                typeSelect.addEventListener('change', function() {
                    console.log('Transaction type changed to:', this.value);
                    
                    categorySelect.value = '';
                    incomeCategories.style.display = 'none';
                    expenseCategories.style.display = 'none';
                    
                    if (this.value === 'income') {
                        incomeCategories.style.display = 'block';
                    } else if (this.value === 'expense') {
                        expenseCategories.style.display = 'block';
                    }
                });
            });
            </script>
        </body>
        </html>
        """
        
    except Exception as e:
        return f"<h1>Route Error</h1><p>{str(e)}</p><a href='/dashboard'>Back to Dashboard</a>"

@app.route('/transactions')
@login_required
def transactions():
    """View all transactions with pagination"""
    try:
        if not ensure_db():
            return "<h1>Database Error</h1><p>Could not initialize database</p><a href='/dashboard'>Back to Dashboard</a>"
            
        page = request.args.get('page', 1, type=int)
        transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.created_at.desc()).paginate(
            page=page, per_page=20, error_out=False)
        
        # Calculate totals
        total_income = db.session.query(db.func.sum(Transaction.amount)).filter_by(user_id=current_user.id, type='income').scalar() or 0
        total_expenses = db.session.query(db.func.sum(Transaction.amount)).filter_by(user_id=current_user.id, type='expense').scalar() or 0
        net_income = total_income - total_expenses
        
        # Build transactions table
        trans_rows = ""
        for t in transactions.items:
            amount_class = "text-success" if t.type == 'income' else "text-danger"
            amount_sign = "+" if t.type == 'income' else "-"
            type_icon = "fa-arrow-up text-success" if t.type == 'income' else "fa-arrow-down text-danger"
            
            trans_rows += f"""
            <tr>
                <td>{t.date.strftime('%b %d, %Y')}</td>
                <td><i class="fas {type_icon} me-2"></i>{t.type.title()}</td>
                <td>{t.category.replace('_', ' ').title()}</td>
                <td>{t.description or '-'}</td>
                <td class="{amount_class} fw-bold">{amount_sign}Rs.{t.amount:.2f}</td>
            </tr>
            """
        
        # Pagination links
        pagination_links = ""
        if transactions.has_prev:
            pagination_links += f'<a href="/transactions?page={transactions.prev_num}" class="btn btn-outline-primary me-2">← Previous</a>'
        if transactions.has_next:
            pagination_links += f'<a href="/transactions?page={transactions.next_num}" class="btn btn-outline-primary">Next →</a>'
        
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Transaction History - Expense Tracker</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        </head>
        <body>
            <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
                <div class="container">
                    <a class="navbar-brand" href="/dashboard">
                        <i class="fas fa-chart-line me-2"></i>Expense Tracker
                    </a>
                </div>
            </nav>
            
            <div class="container mt-4">
                <div class="row">
                    <div class="col-12">
                        <div class="d-flex justify-content-between align-items-center mb-4">
                            <h1><i class="fas fa-history me-2"></i>Transaction History</h1>
                            <div>
                                <a href="/add_transaction" class="btn btn-success me-2">
                                    <i class="fas fa-plus me-2"></i>Add Transaction
                                </a>
                                <a href="/dashboard" class="btn btn-outline-secondary">
                                    <i class="fas fa-arrow-left me-2"></i>Back to Dashboard
                                </a>
                            </div>
                        </div>
                        
                        <!-- Summary Cards -->
                        <div class="row mb-4">
                            <div class="col-md-4">
                                <div class="card bg-success text-white">
                                    <div class="card-body text-center">
                                        <h4>💰 Rs.{total_income:.2f}</h4>
                                        <p class="mb-0">Total Income</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="card bg-danger text-white">
                                    <div class="card-body text-center">
                                        <h4>💸 Rs.{total_expenses:.2f}</h4>
                                        <p class="mb-0">Total Expenses</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="card {'bg-success' if net_income >= 0 else 'bg-warning'} text-white">
                                    <div class="card-body text-center">
                                        <h4>{'📈' if net_income >= 0 else '📉'} Rs.{net_income:.2f}</h4>
                                        <p class="mb-0">Net Balance</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Transactions Table -->
                        {"<div class='card'>" if transactions.items else ""}
                            {"<div class='card-header'><h5 class='mb-0'><i class='fas fa-list me-2'></i>" + str(len(transactions.items)) + " Transaction" + ("s" if len(transactions.items) != 1 else "") + "</h5></div>" if transactions.items else ""}
                            {"<div class='card-body p-0'>" if transactions.items else ""}
                                {"<div class='table-responsive'><table class='table table-hover mb-0'>" if transactions.items else ""}
                                    {"<thead class='table-light'><tr><th>Date</th><th>Type</th><th>Category</th><th>Description</th><th>Amount</th></tr></thead>" if transactions.items else ""}
                                    {"<tbody>" + trans_rows + "</tbody>" if transactions.items else ""}
                                {"</table></div>" if transactions.items else ""}
                            {"</div>" if transactions.items else ""}
                        {"</div>" if transactions.items else ""}
                        
                        {"""
                        <div class="text-center py-5">
                            <i class="fas fa-receipt fa-3x text-muted mb-3"></i>
                            <h4 class="text-muted">No Transactions Found</h4>
                            <p class="text-muted">Start by adding your first income or expense transaction.</p>
                            <a href="/add_transaction" class="btn btn-success btn-lg">
                                <i class="fas fa-plus me-2"></i>Add Your First Transaction
                            </a>
                        </div>
                        """ if not transactions.items else ""}
                        
                        <!-- Pagination -->
                        {f"<div class='d-flex justify-content-center mt-4'>{pagination_links}</div>" if pagination_links else ""}
                    </div>
                </div>
            </div>
            
            <script>
            console.log('Transactions page loaded with styling - {len(transactions.items)} transactions found');
            </script>
        </body>
        </html>
        """
            
    except Exception as e:
        return f"<h1>System Error</h1><p>{str(e)}</p><a href='/dashboard'>Back to Dashboard</a>"

@app.route('/analytics')
@login_required
def analytics():
    """View analytics and charts"""
    try:
        if not ensure_db():
            return "<h1>Database Error</h1><p>Could not initialize database</p><a href='/dashboard'>Back to Dashboard</a>"
            
        # Income by category for current user
        income_by_category = db.session.query(
            Transaction.category, 
            db.func.sum(Transaction.amount).label('total')
        ).filter_by(user_id=current_user.id, type='income').group_by(Transaction.category).all()
        
        # Expense by category for current user
        expense_by_category = db.session.query(
            Transaction.category, 
            db.func.sum(Transaction.amount).label('total')
        ).filter_by(user_id=current_user.id, type='expense').group_by(Transaction.category).all()
        
        # Monthly trends (last 12 months) for current user
        monthly_data = db.session.query(
            db.func.strftime('%Y-%m', Transaction.date).label('month'),
            Transaction.type,
            db.func.sum(Transaction.amount).label('total')
        ).filter_by(user_id=current_user.id).group_by('month', Transaction.type).order_by('month').all()
        
        try:
            return render_template('analytics.html',
                                 income_by_category=income_by_category,
                                 expense_by_category=expense_by_category,
                                 monthly_data=monthly_data)
        except:
            # Fallback to simple analytics
            html = """
            <html>
            <head><title>Analytics - Expense Tracker</title></head>
            <body>
                <h1>Analytics</h1>
                <p><a href="/dashboard">Back to Dashboard</a></p>
                <h2>Income by Category</h2>
                <ul>
            """
            for category, total in income_by_category:
                html += f"<li>{category}: Rs.{total:.2f}</li>"
            html += "</ul><h2>Expenses by Category</h2><ul>"
            for category, total in expense_by_category:
                html += f"<li>{category}: Rs.{total:.2f}</li>"
            html += "</ul></body></html>"
            return html
            
    except Exception as e:
        return f"<h1>System Error</h1><p>{str(e)}</p><a href='/dashboard'>Back to Dashboard</a>"

@app.route('/profile')
@login_required
def profile():
    """User profile page"""
    try:
        if not ensure_db():
            return "<h1>Database Error</h1><p>Could not initialize database</p><a href='/dashboard'>Back to Dashboard</a>"
            
        # Get user statistics
        total_transactions = Transaction.query.filter_by(user_id=current_user.id).count()
        total_income = db.session.query(db.func.sum(Transaction.amount)).filter_by(
            user_id=current_user.id, type='income').scalar() or 0
        total_expense = db.session.query(db.func.sum(Transaction.amount)).filter_by(
            user_id=current_user.id, type='expense').scalar() or 0
        net_balance = total_income - total_expense
        
        # Get member since date
        member_since = current_user.created_at.strftime('%B %Y') if hasattr(current_user, 'created_at') and current_user.created_at else 'Recently'
        
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Profile - Expense Tracker</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        </head>
        <body>
            <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
                <div class="container">
                    <a class="navbar-brand" href="/dashboard">
                        <i class="fas fa-chart-line me-2"></i>Expense Tracker
                    </a>
                </div>
            </nav>
            
            <div class="container mt-4">
                <div class="row justify-content-center">
                    <div class="col-md-8">
                        <!-- Profile Header -->
                        <div class="card mb-4">
                            <div class="card-header bg-primary text-white text-center">
                                <div class="d-flex align-items-center justify-content-center">
                                    <i class="fas fa-user-circle fa-3x me-3"></i>
                                    <div>
                                        <h2 class="mb-1">{current_user.first_name} {current_user.last_name}</h2>
                                        <p class="mb-0 opacity-75">@{current_user.username}</p>
                                    </div>
                                </div>
                            </div>
                            <div class="card-body">
                                <div class="row text-center">
                                    <div class="col-md-6">
                                        <p class="mb-1"><i class="fas fa-envelope text-primary me-2"></i><strong>Email:</strong></p>
                                        <p class="text-muted">{current_user.email}</p>
                                    </div>
                                    <div class="col-md-6">
                                        <p class="mb-1"><i class="fas fa-calendar-alt text-success me-2"></i><strong>Member Since:</strong></p>
                                        <p class="text-muted">{member_since}</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Statistics Cards -->
                        <div class="row mb-4">
                            <div class="col-md-6 col-lg-3 mb-3">
                                <div class="card text-center h-100">
                                    <div class="card-body">
                                        <i class="fas fa-list-alt fa-2x text-info mb-2"></i>
                                        <h4 class="text-info">{total_transactions}</h4>
                                        <p class="mb-0">Total Transactions</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-6 col-lg-3 mb-3">
                                <div class="card text-center h-100">
                                    <div class="card-body">
                                        <i class="fas fa-arrow-up fa-2x text-success mb-2"></i>
                                        <h4 class="text-success">💰 Rs.{total_income:.2f}</h4>
                                        <p class="mb-0">Total Income</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-6 col-lg-3 mb-3">
                                <div class="card text-center h-100">
                                    <div class="card-body">
                                        <i class="fas fa-arrow-down fa-2x text-danger mb-2"></i>
                                        <h4 class="text-danger">💸 Rs.{total_expense:.2f}</h4>
                                        <p class="mb-0">Total Expenses</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-6 col-lg-3 mb-3">
                                <div class="card text-center h-100">
                                    <div class="card-body">
                                        <i class="fas {'fa-chart-line text-success' if net_balance >= 0 else 'fa-chart-line-down text-warning'} fa-2x mb-2"></i>
                                        <h4 class="{'text-success' if net_balance >= 0 else 'text-warning'}">{'📈' if net_balance >= 0 else '📉'} Rs.{net_balance:.2f}</h4>
                                        <p class="mb-0">Net Balance</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Account Actions -->
                        <div class="card">
                            <div class="card-header bg-light">
                                <h5 class="mb-0"><i class="fas fa-cog me-2"></i>Account Settings</h5>
                            </div>
                            <div class="card-body">
                                <div class="d-grid gap-2">
                                    <a href="/logout" class="btn btn-outline-danger btn-lg" 
                                       onclick="return confirm('Are you sure you want to logout?')">
                                        <i class="fas fa-sign-out-alt me-2"></i>Logout
                                    </a>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <script>
            console.log('Profile page loaded with styling - User: {current_user.username}');
            </script>
        </body>
        </html>
        """
            
    except Exception as e:
        return f"<h1>System Error</h1><p>{str(e)}</p><a href='/dashboard'>Back to Dashboard</a>"

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