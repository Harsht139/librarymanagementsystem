import pandas as pd
from sqlalchemy import create_engine, text
import matplotlib.pyplot as plt
import seaborn as sns
import schedule
import time
import os

# -------------------------------
# 1️⃣ Database connection
# -------------------------------
DATABASE_URL = "mysql+pymysql://root:Harsh5764@localhost:3306/lms"

try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))  # simple test query
    print("✅ Database connection successful.")
except Exception as e:
    print("⚠️ Database connection failed:", e)
    exit(1)

# -------------------------------
# 2️⃣ Load CSV predictions (optional)
# -------------------------------
def load_csv_predictions(csv_file='book_predictions.csv'):
    if not os.path.exists(csv_file):
        print(f"⚠️ CSV file '{csv_file}' not found. Skipping CSV load.")
        return pd.DataFrame()
    return pd.read_csv(csv_file)

# -------------------------------
# 3️⃣ Update predictions in DB
# -------------------------------
def update_predictions(csv_file='book_predictions.csv'):
    df = load_csv_predictions(csv_file)
    if df.empty:
        return

    update_df = df[['copy_id', 'predicted_damage_prob', 'predicted_borrow_prob']]
    records = update_df.to_dict(orient='records')

    with engine.begin() as conn:
        for record in records:
            conn.execute(
                text("""
                    UPDATE book_copies
                    SET predicted_damage_prob = :predicted_damage_prob,
                        predicted_borrow_prob = :predicted_borrow_prob
                    WHERE copy_id = :copy_id
                """),
                **record
            )
    print("✅ Database updated with new predictions.")

# -------------------------------
# 4️⃣ Visualize predictions
# -------------------------------
def visualize_predictions():
    df = pd.read_sql("SELECT * FROM book_copies", engine)
    if df.empty:
        print("⚠️ No data in book_copies table to visualize.")
        return

    plt.figure(figsize=(12, 5))
    plt.subplot(1, 2, 1)
    sns.histplot(df['predicted_borrow_prob'], bins=30, kde=True, color='skyblue')
    plt.title('Predicted Borrow Probability Distribution')

    plt.subplot(1, 2, 2)
    sns.histplot(df['predicted_damage_prob'], bins=30, kde=True, color='salmon')
    plt.title('Predicted Damage Probability Distribution')

    plt.tight_layout()
    plt.savefig('predictions_distribution.png')
    plt.show()
    print("📊 Visualization saved as predictions_distribution.png")

# -------------------------------
# 5️⃣ CLI for book predictions
# -------------------------------
def show_book_prediction(book_name):
    df = pd.read_sql("SELECT * FROM book_copies", engine)
    if df.empty:
        print("⚠️ No books found in the database.")
        return

    # Filter by book name (case-insensitive)
    book = df[df['book_name'].str.contains(book_name, case=False, na=False)]
    if book.empty:
        print(f"⚠️ No book found matching '{book_name}'")
        return

    print(f"\n=== Predictions for '{book_name}' ===")
    for _, row in book.iterrows():
        print(f"Copy ID: {row['copy_id']}")
        print(f"Damage Probability: {row.get('predicted_damage_prob', 0):.2f}")
        print(f"Borrow Probability: {row.get('predicted_borrow_prob', 0):.2f}")
        print("-" * 30)

# -------------------------------
# 6️⃣ CLI loop
# -------------------------------
def cli_loop():
    while True:
        print("\nOptions:\n1. Show book prediction\n2. Update predictions from CSV\n3. Visualize predictions\n4. Exit")
        choice = input("Enter choice (1-4): ").strip()
        if choice == '1':
            book_name = input("Enter book name: ").strip()
            show_book_prediction(book_name)
        elif choice == '2':
            update_predictions()
        elif choice == '3':
            visualize_predictions()
        elif choice == '4':
            print("👋 Exiting CLI.")
            break
        else:
            print("⚠️ Invalid choice. Try again.")

# -------------------------------
# 7️⃣ Optional: Scheduled job
# -------------------------------
def scheduled_job():
    update_predictions()
    visualize_predictions()

# -------------------------------
# 8️⃣ Run CLI
# -------------------------------
if __name__ == "__main__":
    print("=== Library Prediction CLI ===")
    cli_loop()
