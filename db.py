from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Replace with your credentials
DATABASE_URL = "mysql+pymysql://root:Harsh5764@localhost:3306/lms"

engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine)
