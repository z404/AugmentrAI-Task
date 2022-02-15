'''
Script to scrape swansea for information on given professors
'''
from unicodedata import name
from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
from multiprocessing.pool import ThreadPool
import json
import pymongo
from dotenv import dotenv_values


class ScraperScript:

    def __init__(self, testing: bool = False):
        req = Request("https://www.swansea.ac.uk/staff/engineering/#associate-professors=is-expanded&lecturers-and-tutors=is-expanded&professors=is-expanded&readers=is-expanded&senior-lecturers=is-expanded")
        html_page = urlopen(req)
        self.soup = BeautifulSoup(html_page, "lxml")
        config = dotenv_values(".env")
        self.monclient = pymongo.MongoClient(config["MONGODB_URI"])
        self.testing = testing

    def create_collection(self) -> None:
        self.collection_promises = []
        # Go through each div with class article-item and expander-list
        for elem in self.soup.findAll('div'):

            # Find dropdown with professor names
            if elem['class'] == ["article-item", "expander-list"]:

                # Go through each link in the dropdown
                for professor in elem.findAll('a'):

                    # If it contains a #, it is a category of teachers
                    if professor['href'][0] == '#':
                        mode = professor.text[:-1].replace('Lecturers', 'Lecturer')
                        continue
                    if professor['href'][0] == '/':
                        link = "https://www.swansea.ac.uk" + professor['href']
                    else:
                        link = professor['href']
                    name = professor.text
                    # Create a dictionary that will hold teacher information
                    self.collection_promises.append([link, name, mode])

    def _caesar_cipher(self, text:str, shift:int) -> str:
        newtext = ""
        for char in text:
            if char.isalpha():
                newtext += chr((ord(char) - ord('a') + shift) % 26 + ord('a'))
            else:
                newtext += char
        return newtext


    def _professor_scraper(self, _list: list) -> dict:
        link, name, mode = _list
        req = Request(link)
        try:
            html_page = urlopen(req)
        except:
            return {}
        soup = BeautifulSoup(html_page, "lxml")
        temp_dict = {}
        for elem in soup.findAll('h1'):
            try:
                if elem['class'] == ["staff-profile-overview-honorific-prefix-and-full-name"]:
                    temp_dict['name'] = elem.text
            except KeyError:
                pass
        flag = True
        for elem in soup.findAll('div'):
            try:
                #about
                if elem['class'] == ["title-and-body-text","title-and-body-text-12"]:
                    for element_temp in elem.findAll('p'):
                        temp_dict["about"] = element_temp.text
                        break

                # profile picture
                elif elem['class'] == ["staff-profile-overview-profile-picture"]:
                    for element in elem.findAll('img'):
                        temp_dict["profile_picture"] = element['src']
                        break

                # characteristics
                elif elem['class'] == ["mb-3"]:
                    temp_dict["characteristics"] = [i.strip() for i in elem.text.replace('\n', '').replace('\t', '').replace('\r', '').split(',')]

                # areas of expertise
                elif elem['class'] == ["staff-profile-areas-of-expertise"]:
                    for element in elem.findAll('li'):
                        try:
                            temp_dict["areas_of_expertise"].append(element.text)
                        except:
                            temp_dict["areas_of_expertise"] = [element.text]
                
                # contact details
                elif elem['class'] == ["col-12","col-lg-6"]:
                    if flag:
                        temp_dict['contact_details'] = {}
                        flag = False
                        contact_details = elem.findAll('div', class_="row mb-2")
                        for element in contact_details:
                            if element.find('a'):
                                if element.find('a').get('href') == None:
                                    obfuscated_email = element.find('a').get('data-obfuscated-email')
                                    for i in range(1,27):
                                        if self._caesar_cipher(obfuscated_email, i).strip().endswith('@swansea.ac.uk'):
                                            temp_dict['contact_details']['email'] = self._caesar_cipher(obfuscated_email, i).strip()
                                            break
                                else:
                                    temp_dict['contact_details']['email'] = element.find('a').get('href').replace('mailto:', '')
                            else:
                                temp_dict['contact_details']['phone'] = element.find('div', class_="col").text.strip()
            except KeyError:
                pass
        

        if temp_dict == {}:
            return {}
        # print(temp_dict)
        temp_dict["mode"] = mode
        temp_dict["name"] = name
        temp_dict["link"] = link
        return temp_dict
    
    def write_to_mongo(self, jsonlist: list) -> None:
        self.professor_database = self.monclient["professor_database"]
        self.prof_collection = self.professor_database["prof_collection"]
        for json_object in jsonlist:
            if json_object != {}:
                self.prof_collection.insert_one(json_object)

    def begin_scrape(self) -> None:
        self.create_collection()
        jsonlist = []
        # Creating a thread pool of 15 threads
        with ThreadPool(15) as pool:
            for result in pool.map(self._professor_scraper, self.collection_promises):
                jsonlist.append(result)
        
        # Writing to MongoDB
        if self.testing:
            with open('test.json', 'w') as f:
                json.dump(jsonlist, f, indent=4)
        else:
            self.clear_mongo()
            self.write_to_mongo(jsonlist)
        
    def get_database_as_json(self) -> dict:
        self.professor_database = self.monclient["professor_database"]
        self.prof_collection = self.professor_database["prof_collection"]
        return [i for i in self.prof_collection.find({})]
    
    def clear_mongo(self) -> None:
        self.professor_database = self.monclient["professor_database"]
        self.prof_collection = self.professor_database["prof_collection"]
        self.prof_collection.delete_many({})


if __name__ == "__main__":
    scraper = ScraperScript()
    scraper.begin_scrape()