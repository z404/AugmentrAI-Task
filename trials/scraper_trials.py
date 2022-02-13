from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
import re

req = Request("https://www.swansea.ac.uk/staff/engineering/#associate-professors=is-expanded&lecturers-and-tutors=is-expanded&professors=is-expanded&readers=is-expanded&senior-lecturers=is-expanded")
html_page = urlopen(req)

soup = BeautifulSoup(html_page, "lxml")
collection = []

for elem in soup.findAll('div'):
    if elem['class'] == ["article-item", "expander-list"]:
        count = 0
        for element in elem.findAll('a'):
            # links.append(element['href'])
            # names.append(element.text)
            if element['href'][0] == '#':
                continue
            elif element['href'][0] == '/':
                link = "https://www.swansea.ac.uk" + element['href']
            else:
                link = element['href']
            try:
                reqtemp = Request(link)
                html_pagetemp = urlopen(reqtemp)
                soup_temp = BeautifulSoup(html_pagetemp, "lxml")
                temp_dict = {}
                for elem_temp in soup_temp.findAll('h1'):
                    try:
                        if elem_temp['class'] == ["staff-profile-overview-honorific-prefix-and-full-name"]:
                            temp_dict['name'] = elem_temp.text
                    except KeyError:
                        pass
                
                # phno = soup_temp.find('div', {"class": ["col-1"]}).text
                # temp_dict['phno'] = phno

                for elem_temp in soup_temp.findAll('div'):
                    flag = 0
                    try:
                        # profile picture
                        if elem_temp['class'] == ["staff-profile-overview-profile-picture"]:
                            for element_temp in elem_temp.findAll('img'):
                                temp_dict["profile_picture"] = element_temp['src']
                                break
                        # characteristics
                        elif elem_temp['class'] == ["mb-3"]:
                            temp_dict["characteristics"] = [i.strip() for i in elem_temp.text.replace('\n', '').replace('\t', '').replace('\r', '').split(',')]

                        
                        # areas of expertise
                        elif elem_temp['class'] == ["staff-profile-areas-of-expertise"]:
                            for element_temp in elem_temp.findAll('li'):
                                # temp_dict["areas_of_expertise"] = element_temp.text
                                # break
                                try:
                                    temp_dict["areas_of_expertise"].append(element_temp.text)
                                except:
                                    temp_dict["areas_of_expertise"] = [element_temp.text]
                        
                        # about
                        elif elem_temp['class'] == ["title-and-body-text","title-and-body-text-12"]:
                            for element_temp in elem_temp.findAll('p'):
                                temp_dict["about"] = element_temp.text
                                break

                        # #contact
                        # elif elem_temp['class'] == ["col-12","col-lg-6"]:
                        #     children = elem_temp.findChildren(recursive=False)
                        #     if "contact" not in temp_dict.keys():
                        #         temp_dict["contact"] = {}
                        #         for i in children[:-1]:
                        #             if i.name == "div":
                        #                 j = i.findChildren(recursive=False)
                        #                 print(j)
                        #                 for k in j:
                        #                     if k.name == "h3":
                        #                         key = k.text
                        #                     elif k.name == "div" and k['class'] == ["col"]:
                        #                         temp_dict["contact"].update({key:k.text.strip()})

                    except KeyError:
                        pass
            except Exception as e:
                print(e)
                print(link)
                continue
            collection.append(temp_dict)
            
            count+=1
            if count > 10: break

with open('data.txt', 'w') as outfile:
    for item in collection:
        outfile.write("%s\n" % item)
# print(links)
# print(names)