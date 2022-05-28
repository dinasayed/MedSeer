from itertools import islice

from bs4 import BeautifulSoup
from dateutil import parser
from django.core.validators import FileExtensionValidator
from django.db import IntegrityError, models


def take(n, iterable):
    "Return first n items of the iterable as a list"
    return list(islice(iterable, n))


class Journal(models.Model):
    name = models.CharField(max_length=1000, unique=True)
    rank = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Organization(models.Model):
    name = models.CharField(max_length=1000, unique=True)
    rank = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Author(models.Model):
    forename = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)
    email = models.EmailField(null=True, blank=True, unique=True)
    organization = models.ForeignKey(
        Organization, on_delete=models.PROTECT, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.forename} {self.surname}'

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('forename', 'surname'), name='unique_author_name'),
        ]


class Paper(models.Model):
    pdf = models.FileField(upload_to='pdfs/%Y/%m/%d/', blank=True,
                           help_text="Upload *.pdf file and Save to generate .tie.xml using Grobid",
                           validators=[FileExtensionValidator(['pdf'])])
    tei = models.FileField(upload_to='xmls/%Y/%m/%d/', blank=False,
                           help_text="Upload *.tie.xml file and Save to autofill paper data",
                           validators=[FileExtensionValidator(['xml'])])
    title = models.CharField(max_length=500, null=True,
                             blank=True, unique=True)
    abstract = models.TextField(blank=True)
    doi = models.CharField(max_length=100, null=True, blank=True, unique=True)
    url = models.URLField(max_length=1000, null=True, blank=True, unique=True)
    authors = models.ManyToManyField(Author, blank=True)
    journal = models.ForeignKey(
        Journal, on_delete=models.PROTECT, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    published_at = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.title or "Link To Paper"
    
    def parse_tei(self):
        soup = BeautifulSoup(self.tei, 'xml')
        title_tag = soup.title
        if title_tag:
            try:
                while not title_tag.getText():
                    title_tag = title_tag.find_next('title')
                self.title = title_tag.getText()
            except:
                pass
#            print("debug line 1: after dealing with title")
            
        self.abstract = soup.abstract.getText()
 #       print("debug line 2: after dealing with abstract")
        # self.doi = soup.find('idno', type='DOI').getText()
        date_published_tag = soup.find('date', type='published')
        if date_published_tag:
            if date_published_tag.get('when'):
                try:
                    self.published_at = parser.parse(date_published_tag.get('when'))
                except:
                    pass
        authors = []
  #      print("debug line 3: after dealing with date_publish")

        for author_tag in take(4, soup.find_all('author')):
            try:
                if author_tag.affiliation:
   #                 print (len("; ".join(org.getText() for org in author_tag.affiliation.find_all('orgName'))))
                    organization, created = Organization.objects.get_or_create(
                            name="; ".join(org.getText() for org in author_tag.affiliation.find_all('orgName')))
                else:
                    organization=None
    #                print("debug line 4: after dealing with organization none")
                author, created = Author.objects.update_or_create(
                        forename=author_tag.forename.getText() if author_tag.forename else None,
                        surname=author_tag.surname.getText() if author_tag.surname else None,
                        defaults={
                            'email': author_tag.email.getText() if author_tag.email else None,
                            'organization': organization
                            }
                        )
     #           print("debug line 5: before authors append")
                authors.append(author)
      #          print("debug line 6: after authors append")
            except IntegrityError:
                pass
       # print("before set authors ")
        self.authors.set(authors)
        #print("after set authors ")
        return self
