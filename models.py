from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Table, ForeignKey, Text, Date, Integer


Base = declarative_base()


document_articles = Table('document_articles', Base.metadata,
    Column('document_id', String, ForeignKey('document.id')),
    Column('article_id', Integer, ForeignKey('article.id'))
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

    case = Column(String)

    case_name = Column(String)

    tags = Column(String)

    date = Column(Date)

    html = Column(Text)


class Article(Base):
    """
    An article is a number from the European Convention on Human Rights.
    """
    __tablename__ = 'article'

    id = Column(Integer, primary_key=True)

    documents = relationship("Document", secondary=document_articles)


class Case(Base):
    __tablename__ = 'case'

    id = Column(String, primary_key=True)
