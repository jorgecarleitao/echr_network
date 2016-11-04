from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import crawler, models


engine = create_engine('postgresql://echr:echr@localhost/echr', echo=False)
Session = sessionmaker(bind=engine)

# uncomment to drop all stuff and try again
#models.Base.metadata.drop_all(engine)

models.Base.metadata.create_all(engine)

session = Session()

crawler.retrieve_and_save(session)
