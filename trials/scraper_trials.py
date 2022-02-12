from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
import re

req = Request("https://www.swansea.ac.uk/staff/engineering/#associate-professors=is-expanded&lecturers-and-tutors=is-expanded&professors=is-expanded&readers=is-expanded&senior-lecturers=is-expanded")
html_page = urlopen(req)

soup = BeautifulSoup(html_page, "lxml")

links = []
names = []
for elem in soup.findAll('div'):
    if elem['class'] == ["article-item", "expander-list"]:
        for element in elem.findAll('a'):
            # links.append(element['href'])
            # names.append(element.text)
            print(element.text)

# print(links)
# print(names)