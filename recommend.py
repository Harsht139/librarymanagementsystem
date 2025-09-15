import pandas as pd
from sqlalchemy import create_engine, text
import matplotlib.pyplot as plt
import seaborn as sns
import schedule
import time

# -------------------------------
# 1️⃣ Database connection
# -------------------------------
DATABASE_URL = "mysql+pymysql://root:Harsh5764@localhost:3306/lms"
engine = create_engine(DATABASE_URL)

# -------------------------------
# 2️⃣ Load book predictions
# -------------------------------
def load_book_predictions(csv_file='book_predictions.csv'):
    try:
        df = pd.read_csv(csv_file)
        return df
    except FileNotFoundError:
        print(f"❌ CSV file '{csv_file}' not found. Using DB data instead.")
        query = """
            SELECT 
                c.copy_id,
                c.book_id,
                c.predicted_borrow_prob,
                c.predicted_damage_prob,
                b.title AS book_title
            FROM book_copies c
            JOIN books b ON c.book_id = b.book_id
        """
        df = pd.read_sql(text(query), engine)
        return df

# -------------------------------
# 3️⃣ Update predictions in DB
# -------------------------------
def update_predictions(csv_file='book_predictions.csv'):
    df = load_book_predictions(csv_file)

    if df.empty:
        print("❌ No data to update.")
        return

    # Clip probabilities to 0-1
    df['predicted_borrow_prob'] = df['predicted_borrow_prob'].clip(0, 1)
    df['predicted_damage_prob'] = df['predicted_damage_prob'].clip(0, 1)

    # Update DB
    records = df.to_dict(orient='records')
    with engine.begin() as conn:
        for record in records:
            conn.execute(
                """
                UPDATE book_copies
                SET predicted_borrow_prob = :predicted_borrow_prob,
                    predicted_damage_prob = :predicted_damage_prob
                WHERE copy_id = :copy_id
                """,
                **record
            )
    print("✅ Database updated with new predictions.")

# -------------------------------
# 4️⃣ Visualize predictions
# -------------------------------
def visualize_predictions():
    df = pd.read_sql(text("SELECT * FROM book_copies"), engine)

    plt.figure(figsize=(12, 5))
    
    plt.subplot(1, 2, 1)
    sns.histplot(df['predicted_borrow_prob']*100, bins=30, kde=True, color='skyblue')
    plt.title('Predicted Borrow Probability (%)')

    plt.subplot(1, 2, 2)
    sns.histplot(df['predicted_damage_prob']*100, bins=30, kde=True, color='salmon')
    plt.title('Predicted Damage Probability (%)')

    plt.tight_layout()
    plt.savefig('predictions_distribution.png')
    plt.show()
    print("📊 Visualization saved as predictions_distribution.png")

# -------------------------------
# 5️⃣ Show predictions for a book
# -------------------------------
def show_book_prediction(book_name):
    df = load_book_predictions()
    df['predicted_borrow_prob'] = df['predicted_borrow_prob'].clip(0, 1)
    df['predicted_damage_prob'] = df['predicted_damage_prob'].clip(0, 1)

    # Book-level aggregation
    book_summary = df.groupby('book_title').agg(
        avg_borrow_prob=('predicted_borrow_prob', 'mean'),
        avg_damage_prob=('predicted_damage_prob', 'mean')
    ).reset_index()

    book_summary['avg_borrow_prob_pct'] = (book_summary['avg_borrow_prob']*100).round(2)
    book_summary['avg_damage_prob_pct'] = (book_summary['avg_damage_prob']*100).round(2)

    # Filter by name
    filtered_summary = book_summary[book_summary['book_title'].str.lower().str.contains(book_name.lower())]

    if filtered_summary.empty:
        print(f"❌ No predictions found for '{book_name}'")
        return

    for _, row in filtered_summary.iterrows():
        print(f"📖 Book: {row['book_title']}")
        print(f"  - Predicted Borrow Probability: {row['avg_borrow_prob_pct']}%")
        print(f"  - Predicted Damage Probability: {row['avg_damage_prob_pct']}%")
        print("-"*40)

    # Also show copy-level details
    filtered_copies = df[df['book_title'].str.lower().str.contains(book_name.lower())]
    for _, row in filtered_copies.iterrows():
        print(f"  Copy ID: {row['copy_id']}")
        print(f"    - Borrow Probability: {(row['predicted_borrow_prob']*100):.2f}%")
        print(f"    - Damage Probability: {(row['predicted_damage_prob']*100):.2f}%")
    print("-"*40)

# -------------------------------
# 6️⃣ CLI loop
# -------------------------------
def cli_loop():
    print("=== Library Book Predictions ===")
    while True:
        book_name = input("Enter book name to see predictions (or 'exit' to quit): ").strip()
        if book_name.lower() == 'exit':
            print("Goodbye!")
            break
        show_book_prediction(book_name)

# -------------------------------
# 7️⃣ Scheduler for automated updates
# -------------------------------
def job():
    update_predictions()
    visualize_predictions()

# -------------------------------
# 8️⃣ Main
# -------------------------------
if __name__ == "__main__":
    # Uncomment next line to run scheduled daily updates
    # schedule.every().day.at("02:00").do(job)

    cli_loop()
    # Uncomment to run scheduler continuously
    # while True:
    #     schedule.run_pending()
    #     time.sleep(60)
