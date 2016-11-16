from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Table, ForeignKey, Text, Date, Integer, PrimaryKeyConstraint


Base = declarative_base()


document_articles = Table('document_articles', Base.metadata,
    Column('document_id', String, ForeignKey('document.id')),
    Column('article_id', Integer, ForeignKey('article.id'))
)


document_references = Table('document_references', Base.metadata,
    Column('from_id', String, ForeignKey('document.id'), nullable=False),
    Column('to_id', String, ForeignKey('document.id'), nullable=False),
    #PrimaryKeyConstraint('from_id', 'to_id'),
)


class Document(Base):
    """
    A document is
    - uniquely identified by an `id` of the form XXX-XXXXX (e.g. 001-61414)
    - contains text (in `html`)
    - associated to a particular `case`
    - related to specific `articles` from the treaty
    - contains references to other cases (`scl`)
    """
    __tablename__ = 'document'

    id = Column(String, primary_key=True)
    scl = Column(Text)

    articles = relationship("Article", secondary=document_articles)

    references = relationship(
        'Document',
        secondary=document_references,
        primaryjoin=document_references.c.from_id==id,
        secondaryjoin=document_references.c.to_id==id,
        backref="referrers")

    case = Column(String)

    case_name = Column(String)

    # models.Document.tags.contains('JUDGMENTS') for decisions and
    # models.Document.tags.contains('COMMUNICATEDCASES') for communications
    tags = Column(String)

    date = Column(Date, index=True)

    html = Column(Text)


class Article(Base):
    """
    An article is a number from the European Convention on Human Rights.
    """
    __tablename__ = 'article'

    id = Column(Integer, primary_key=True)

    documents = relationship("Document", secondary=document_articles)
