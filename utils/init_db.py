from .database import Base, engine

def init_database():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_database() 