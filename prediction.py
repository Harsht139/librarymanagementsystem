# prediction.py
import pandas as pd
from sqlalchemy import create_engine
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from joblib import dump

# ---- 1. Database connection ----
db_user = 'root'
db_pass = 'Harsh5764'
db_host = 'localhost'
db_name = 'lms'

# SQLAlchemy engine
engine = create_engine(f"mysql+pymysql://{db_user}:{db_pass}@{db_host}/{db_name}")

try:
    # Test connection
    with engine.connect() as conn:
        print("Connected successfully to LMS database!")
except Exception as e:
    print("Error connecting to database:", e)
    exit(1)

# ---- 2. Load data ----
try:
    book_copies_df = pd.read_sql("SELECT * FROM book_copies", engine)
    borrow_stats_df = pd.read_sql("SELECT * FROM book_borrow_stats", engine)
except Exception as e:
    print("Error reading tables/views:", e)
    exit(1)

print("Data loaded successfully!")
print("Book copies preview:\n", book_copies_df.head())
print("Borrow stats preview:\n", borrow_stats_df.head())

# ---- 3. Prepare dataset for prediction ----
# Predicting 'total_borrows' using available features
if 'total_borrows' not in borrow_stats_df.columns:
    print("Column 'total_borrows' not found in borrow_stats")
    exit(1)

# Features: book_id, unique_borrowers, avg_late_days (fill NaN with 0)
X = borrow_stats_df[['book_id', 'unique_borrowers', 'avg_late_days']].fillna(0)  
y = borrow_stats_df['total_borrows']  # Target

# Split into training and testing
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# ---- 4. Train model ----
model = LinearRegression()
model.fit(X_train, y_train)

# Evaluate
score = model.score(X_test, y_test)
print(f"Model R^2 score: {score:.2f}")

# ---- 5. Make predictions ----
borrow_stats_df['predicted_borrows'] = model.predict(X)

# ---- 6. Save predictions ----
borrow_stats_df.to_csv("borrow_predictions.csv", index=False)
dump(model, "borrow_model.joblib")  # Save the trained model
print("Predictions saved to borrow_predictions.csv and model saved as borrow_model.joblib")
