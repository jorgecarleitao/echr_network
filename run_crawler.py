from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import crawler


engine = create_engine('postgresql://echr:echr@localhost/echr', echo=False)
Session = sessionmaker(bind=engine)


session = Session()

crawler.retrieve_and_save(session)
