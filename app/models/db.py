from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os

database_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'graduation_research.db')
engine = create_engine('sqlite:///' + database_file, echo=True, convert_unicode=True)
engine.execute('PRAGMA foreign_keys = true;')
db_session = scoped_session(sessionmaker(autocommit=False,autoflush=False,bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()

def init_db():
    os.remove(database_file)
    import app.models.models
    Base.metadata.create_all(bind=engine)