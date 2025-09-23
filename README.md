# Personal Expense & Income Tracker

A Flask web application for tracking personal expenses and income with user authentication, profiles, and analytics visualization features. Ready for deployment on Vercel.

## Features

- **User Authentication**: Secure registration and login system
- **User Profiles**: Individual user accounts with personal statistics
- **Dashboard**: Overview of total income, expenses, and balance for each user
- **Add Transactions**: Easy form to add income or expense transactions
- **Transaction Management**: View all transactions with pagination and delete functionality
- **Analytics**: Visual charts showing:
  - Income breakdown by category
  - Expense breakdown by category
  - Monthly trends over time
- **Categories**: Predefined categories for both income and expenses
- **Responsive Design**: Mobile-friendly interface using Bootstrap
- **Multi-user Support**: Each user has their own separate financial data
- **Cloud Ready**: Optimized for serverless deployment on Vercel

## Quick Deploy to Vercel

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/yourusername/expense-tracker)

## Local Development

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd expense-tracker
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv .venv
   ```

3. **Activate the virtual environment**:
   - Windows: `.venv\Scripts\activate`
   - macOS/Linux: `source .venv/bin/activate`

4. **Install required packages**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the application locally**:
   ```bash
   python app.py
   ```

6. **Open your browser** and navigate to:
   ```
   http://localhost:5000
   ```

## Vercel Deployment

### Method 1: Vercel CLI (Recommended)

1. **Install Vercel CLI**:
   ```bash
   npm i -g vercel
   ```

2. **Login to Vercel**:
   ```bash
   vercel login
   ```

3. **Deploy**:
   ```bash
   vercel
   ```

### Method 2: GitHub Integration

1. **Push your code to GitHub**
2. **Visit [Vercel Dashboard](https://vercel.com/dashboard)**
3. **Click "New Project"**
4. **Import your GitHub repository**
5. **Deploy automatically**

### Method 3: Vercel Web Interface

1. **Visit [Vercel](https://vercel.com)**
2. **Sign up/Login with GitHub**
3. **Create new project from your repository**
4. **Vercel will auto-detect Flask and deploy**

## Project Structure

```
expense-tracker/
├── app.py                    # Main Flask application
├── vercel.json              # Vercel deployment configuration
├── requirements.txt         # Python dependencies
├── .gitignore              # Git ignore file
├── README.md               # This file
├── templates/              # HTML templates
│   ├── base.html           # Base template with navigation
│   ├── index.html          # Dashboard/home page
│   ├── login.html          # User login page
│   ├── register.html       # User registration page
│   ├── profile.html        # User profile page
│   ├── add_transaction.html # Add transaction form
│   ├── transactions.html   # View all transactions
│   └── analytics.html      # Analytics and charts
└── expense_tracker.db      # SQLite database (created automatically)
```

## Income Categories

- Salary
- Freelance
- Investment
- Business
- Gift
- Other Income

## Expense Categories

- Food & Dining
- Transportation
- Shopping
- Entertainment
- Bills & Utilities
- Healthcare
- Education
- Travel
- Housing
- Other Expense

## Technologies Used

## Technologies Used

- **Backend**: Flask, SQLAlchemy, Flask-Login, Flask-Bcrypt
- **Frontend**: HTML5, Bootstrap 5, JavaScript
- **Charts**: Chart.js
- **Database**: SQLite (local), PostgreSQL (production recommended)
- **Forms**: Flask-WTF, WTForms
- **Authentication**: Flask-Login with password hashing
- **Deployment**: Vercel (serverless)

## Features in Detail

### Dashboard
- Quick overview of financial status
- Recent transactions list
- Summary cards showing totals and balance

### Transaction Management
- Add income or expense transactions
- Dynamic category selection based on transaction type
- Date selection with current date as default
- Optional description field
- View all transactions with pagination
- Delete transactions with confirmation

### Analytics
- Pie charts for income and expense categories
- Line chart showing monthly trends
- Tabular breakdown of amounts by category

## Database Schema

The application uses SQLite database with the following tables:

### User Table
- `id`: Primary key
- `username`: Unique username (4-20 characters)
- `email`: Unique email address
- `password_hash`: Encrypted password
- `first_name`: User's first name
- `last_name`: User's last name
- `created_at`: Account creation timestamp

### Transaction Table
- `id`: Primary key
- `type`: 'income' or 'expense'
- `amount`: Transaction amount (float)
- `category`: Selected category
- `description`: Optional description
- `date`: Transaction date
- `created_at`: Timestamp when record was created
- `user_id`: Foreign key linking to User table

## Environment Variables (Optional)

For production deployment, you can set these environment variables:

```bash
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
DATABASE_URL=your-database-url-here
```

## Production Considerations

### Database
- **Local Development**: Uses SQLite (included)
- **Production**: Consider upgrading to PostgreSQL for better performance
- **Vercel**: Database persists between deployments in serverless functions

### Security
- Change the `SECRET_KEY` in production
- Use environment variables for sensitive configuration
- Enable HTTPS in production (Vercel provides this automatically)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is open source and available under the MIT License.
