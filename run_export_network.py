import json
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
import models


engine = create_engine('postgresql://echr:echr@localhost/echr', echo=False)
Session = sessionmaker(bind=engine)

session = Session()

docs = session.query(models.Document) \
        .filter(~(models.Document.html == '')) \
        .filter(models.Document.tags.contains('ENG')) \
        .order_by(desc('date'))

json_object = {}
for doc in docs:
    references = list(set([ref.id for ref in doc.references]))

    json_object[doc.id] = {
        'year': doc.date.year,
        'month': doc.date.month,
        'references': references,
        'case_name': doc.case_name,
        'cases': doc.case.split(';')
    }

with open('network.json', 'w') as fp:
    json.dump(json_object, fp, indent=4, sort_keys=True)


# to export the database to sql, use:
# pg_dump -U echr -d echr > dump.sql
