from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import crawler, models


engine = create_engine('sqlite:///main.db', echo=False)
Session = sessionmaker(bind=engine)


models.Base.metadata.create_all(engine)

session = Session()

crawler.retrieve_and_save(session)
