from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SelectField, DateField, TextAreaField, SubmitField, PasswordField
from wtforms.validators import DataRequired, NumberRange, Email, Length, EqualTo
from datetime import datetime, date
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expense_tracker.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

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

# Forms
class RegistrationForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=2, max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=50)])
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', 
                                   validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')

class TransactionForm(FlaskForm):
    type = SelectField('Type', choices=[('income', 'Income'), ('expense', 'Expense')], validators=[DataRequired()])
    amount = FloatField('Amount', validators=[DataRequired(), NumberRange(min=0.01)])
    category = SelectField('Category', choices=[], validators=[DataRequired()])
    description = TextAreaField('Description')
    date = DateField('Date', validators=[DataRequired()], default=date.today)
    submit = SubmitField('Add Transaction')

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

# Routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Check if username or email already exists
        existing_user = User.query.filter((User.username == form.username.data) | 
                                        (User.email == form.email.data)).first()
        if existing_user:
            flash('Username or email already exists. Please choose different ones.', 'danger')
            return render_template('register.html', form=form)
        
        # Create new user
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=hashed_password,
            first_name=form.first_name.data,
            last_name=form.last_name.data
        )
        db.session.add(user)
        db.session.commit()
        
        flash(f'Account created for {form.username.data}! You can now log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.first_name}!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Login unsuccessful. Please check username and password.', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/profile')
@login_required
def profile():
    # Get user statistics
    total_transactions = Transaction.query.filter_by(user_id=current_user.id).count()
    total_income = db.session.query(db.func.sum(Transaction.amount)).filter_by(
        user_id=current_user.id, type='income').scalar() or 0
    total_expense = db.session.query(db.func.sum(Transaction.amount)).filter_by(
        user_id=current_user.id, type='expense').scalar() or 0
    
    return render_template('profile.html', 
                         user=current_user,
                         total_transactions=total_transactions,
                         total_income=total_income,
                         total_expense=total_expense)

@app.route('/')
@login_required
def index():
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

@app.route('/add_transaction', methods=['GET', 'POST'])
@login_required
def add_transaction():
    form = TransactionForm()
    
    # Set categories based on transaction type
    if request.method == 'POST' and form.type.data:
        if form.type.data == 'income':
            form.category.choices = INCOME_CATEGORIES
        else:
            form.category.choices = EXPENSE_CATEGORIES
    else:
        form.category.choices = EXPENSE_CATEGORIES  # Default to expense categories
    
    if form.validate_on_submit():
        transaction = Transaction(
            type=form.type.data,
            amount=form.amount.data,
            category=form.category.data,
            description=form.description.data,
            date=form.date.data,
            user_id=current_user.id
        )
        db.session.add(transaction)
        db.session.commit()
        flash(f'{form.type.data.title()} of ${form.amount.data:.2f} added successfully!', 'success')
        return redirect(url_for('index'))
    
    return render_template('add_transaction.html', form=form)

@app.route('/transactions')
@login_required
def transactions():
    page = request.args.get('page', 1, type=int)
    transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False)
    return render_template('transactions.html', transactions=transactions)

@app.route('/analytics')
@login_required
def analytics():
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
    
    return render_template('analytics.html',
                         income_by_category=income_by_category,
                         expense_by_category=expense_by_category,
                         monthly_data=monthly_data)

@app.route('/delete_transaction/<int:id>')
@login_required
def delete_transaction(id):
    transaction = Transaction.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    db.session.delete(transaction)
    db.session.commit()
    flash('Transaction deleted successfully!', 'success')
    return redirect(url_for('transactions'))

@app.route('/get_categories/<transaction_type>')
def get_categories(transaction_type):
    if transaction_type == 'income':
        return {'categories': INCOME_CATEGORIES}
    else:
        return {'categories': EXPENSE_CATEGORIES}

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run()

# For Vercel deployment
vercel_app = app