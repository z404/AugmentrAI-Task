# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

from typing import Any, Text, Dict, List

from numpy import disp
from sqlalchemy import Integer

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
import pymongo
import os
from dotenv import dotenv_values

from re import sub
import threading

import gensim.downloader as api
from gensim.utils import simple_preprocess
from gensim.corpora import Dictionary
from gensim.models import TfidfModel
from gensim.similarities import WordEmbeddingSimilarityIndex
from gensim.similarities import SparseTermSimilarityMatrix
from gensim.similarities import SoftCosineSimilarity
from gensim.models.keyedvectors import Word2VecKeyedVectors

# Import and download the most up-to-date stopwords from NLTK
# from nltk import download
# from nltk.corpus import stopwords
# download('stopwords')  # Download stopwords list.
# nltk_stop_words = set(stopwords.words("english"))

# Or use a hard-coded list of English stopwords
nltk_stop_words = {'a','about','above','after','again','against','ain','all','am','an','and','any','are','aren',"aren't",'as','at','be','because','been','before','being','below','between','both','but','by','can','couldn',"couldn't",'d','did','didn',"didn't",'do','does','doesn',"doesn't",'doing','don',"don't",'down','during','each','few','for','from','further','had','hadn',"hadn't",'has','hasn',"hasn't",'have','haven',"haven't",'having','he','her','here','hers','herself','him','himself','his','how','i','if','in','into','is','isn',"isn't",'it',"it's",'its','itself','just','ll','m','ma','me','mightn',"mightn't",'more','most','mustn',"mustn't",'my','myself','needn',"needn't",'no','nor','not','now','o','of','off','on','once','only','or','other','our','ours','ourselves','out','over','own','re','s','same','shan',"shan't",'she',"she's",'should',"should've",'shouldn',"shouldn't",'so','some','such','t','than','that',"that'll",'the','their','theirs','them','themselves','then','there','these','they','this','those','through','to','too','under','until','up','ve','very','was','wasn',"wasn't",'we','were','weren',"weren't",'what','when','where','which','while','who','whom','why','will','with','won',"won't",'wouldn',"wouldn't",'y','you',"you'd","you'll","you're","you've",'your','yours','yourself','yourselves'}


class NotReadyError(Exception):
    pass


class DocSim:
    """
    Find documents that are similar to a query string.
    Calculated using word similarity (Soft Cosine Similarity) of word embedding vectors
    Example usage:
    # Use default model (glove-wiki-gigaword-50)
    docsim = DocSim()
    docsim.similarity_query(query_string, documents)
    # Or, specify a preferred, pre-existing Gensim model with custom stopwords and verbose mode    
    docsim = DocSim(model='glove-twitter-25', stopwords=['the', 'and', 'are'], verbose=True)
    docsim.similarity_query(query_string, documents)
    # Or, supply a custom pre-initialised model in gensim.models.keyedvectors.Word2VecKeyedVectors format
    docsim = DocSim(model=myModel)
    docsim.similarity_query(query_string, documents)    
    """

    default_model = "glove-wiki-gigaword-50"
    model_ready = False  # Only really relevant to threaded sub-class
    
    def __init__(self, model=None, stopwords=None, verbose=False):
        # Constructor

        self.verbose = verbose

        self._load_model(model)

        if stopwords is None:
            self.stopwords = nltk_stop_words
        else:
            self.stopwords = stopwords

    def _load_model(self, model):
        # Pass through to _setup_model (overridden in threaded)
        self._setup_model(model)

    def _setup_model(self, model):
        # Determine which model to use, download/load it, and create the similarity_index
        
        if isinstance(model, Word2VecKeyedVectors):
            # Use supplied model
            self.model = model
        elif isinstance(model, str):
            # Try to download named model
            if self.verbose: 
                print(f'Loading word vector model: {model}')
            self.model = api.load(model)
            if self.verbose: 
                print('Model loaded')
        elif model is None:
            # Download/use default GloVe model
            if self.verbose: 
                print(f'Loading default GloVe word vector model: {self.default_model}')
            self.model = api.load(self.default_model)
            if self.verbose: 
                print('Model loaded')
        else:
            raise ValueError('Unable to load word vector model')

        self.similarity_index = WordEmbeddingSimilarityIndex(self.model)
        
        self.model_ready = True

    def preprocess(self, doc: str):
        # Clean up input document string, remove stopwords, and tokenize
        doc = sub(r'<img[^<>]+(>|$)', " image_token ", doc)
        doc = sub(r'<[^<>]+(>|$)', " ", doc)
        doc = sub(r'\[img_assist[^]]*?\]', " ", doc)
        doc = sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', " url_token ", doc)
        
        return [token for token in simple_preprocess(doc, min_len=0, max_len=float("inf")) if token not in self.stopwords]

    def _softcossim(self, query: str, documents: list):
        # Compute Soft Cosine Measure between the query and each of the documents.
        query = self.tfidf[self.dictionary.doc2bow(query)]
        index = SoftCosineSimilarity(
            self.tfidf[[self.dictionary.doc2bow(document) for document in documents]],
            self.similarity_matrix)
        similarities = index[query]

        return similarities

    def similarity_query(self, query_string: str, documents: list):
        """
        Run a new similarity ranking, for query_string against each of the documents
        Arguments:
            query_string: (string)
            documents: (list) of string documents to compare query_string against
            explain: (bbol) if True, highest scoring words are also returned
        Returns:
            list: similarity scores for each of the documents
            or
            NotReadyError: if model is not ready/available
        """

        if self.model_ready:
        
            corpus = [self.preprocess(document) for document in documents]
            query = self.preprocess(query_string)

            if set(query) == set([word for document in corpus for word in document]):
                raise ValueError('query_string full overlaps content of document corpus')
            
            if self.verbose:
                print(f'{len(corpus)} documents loaded into corpus')
            
            self.dictionary = Dictionary(corpus+[query])
            self.tfidf = TfidfModel(dictionary=self.dictionary)
            self.similarity_matrix = SparseTermSimilarityMatrix(self.similarity_index, 
                                                self.dictionary, self.tfidf)
                        
            scores = self._softcossim(query, corpus)

            return scores.tolist()

        else:
            raise NotReadyError('Word embedding model is not ready.')


class DocSim_threaded(DocSim):
    """
    Threaded verion to load model (long running process) in background. Everything else same as standard version.
    Find documents that are similar to a query string.
    Calculated using word similarity (Soft Cosine Similarity) of word embedding vectors
    Example usage:
    docsim = DocSim_threaded()
    docsim.similarity_query(query_string, documents)
    """

    def _load_model(self, model):
        """
        # Setup the model in a separate thread
        """

        self.thread = threading.Thread(target=self._setup_model, args=[model])
        self.thread.setDaemon(True)
        self.thread.start()


class UtteSadGoodbye(Action):

    def name(self) -> Text:
        return "utte_sad_goodbye"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(text="I'm sorry to hear that. I hope I can be of better help next time.")

        return []

class ActionAskForEntity(Action):

    def name(self) -> Text:
        return "action_ask_for_entity"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(text="I need a few more details before I can proceed. Could you please provide a description of what topic you want assistance on?")

        return []

class ActionProvideReccomendations(Action):

    data = []

    about_recommendations = {}

    def __init__(self):
        # Initializing document database
        print("----------------INIT----------------")
        config = dotenv_values(".env")
        monclient = pymongo.MongoClient(config["MONGODB_URI"])
        professor_database = monclient["professor_database"]
        prof_collection = professor_database["prof_collection"]
        self.data = [i for i in prof_collection.find({})]
        ActionProvideReccomendations.data = self.data
        self.docsim = DocSim()

        for i in range(len(self.data)):
            if "about" in self.data[i].keys():
                self.data[i]["about_text"] = self.data[i]["about"].replace("\n", " ")
            else: self.data[i]["about_text"] = "None"

            if "areas_of_expertise" in self.data[i].keys():
                self.data[i]["areas_of_expertise_text"] = " ".join(self.data[i]["areas_of_expertise"])
            else:
                self.data[i]["areas_of_expertise_text"] = "None"

        # simprobs = docsim.similarity_query("fluidmechanics", areas_of_expertise)
        # strings = [areas_of_expertise[i] for i in range(len(simprobs)) if simprobs[i] > 0.5]
        # print(strings)

    def name(self) -> Text:
        return "action_provide_recommendations"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        keyword_lst = [x for i in tracker.latest_message['entities'] if i["entity"] == "subject" and i["confidence_entity"] > 0.2 for x in i["value"].split()]
        result = self._generate_recommendations(keyword_lst, tracker.sender_id)

        output_string = "I think " + result[0]["name"] + " can help you out! You can check out their profile at "+ result[0]["link"] + " or contact them directly at "\
             + result[0]['contact_details']["email"] + " (email) or " + result[0]['contact_details']["phone"] + " (phone). "
        
        output_string += "Alternatively, you can check out the following professors: " + ", ".join([i["name"]+" ("+i["link"]+")" for i in result[1:]]) + "."

        dispatcher.utter_message(text="I have found some resources for you. {}".format(output_string))

        return []

    def _generate_recommendations(self, keyword_list: list, username) -> List[Integer]:
        # Find the top 3 professors with the highest similarity to the query
        # print([i["areas_of_expertise_text"] for i in self.data])
        simprobs = self.docsim.similarity_query(" ".join(keyword_list), [i["areas_of_expertise_text"] for i in self.data])
        
        retdata = self.data.copy()

        #sort by similarity
        for i in range(len(retdata)):
            retdata[i]["similarity"] = simprobs[i]
        
        retdata = sorted(retdata, key=lambda x: x["similarity"], reverse=True)
        

        ActionProvideReccomendations.about_recommendations = {username: (retdata[:3], keyword_list)}
        return retdata[:3]

class ActionProvideReccomendationsAbout(Action):

    def __init__(self):
        # Initializing document database
        print("----------------INIT----------------")
        self.data = ActionProvideReccomendations.data
        self.docsim = DocSim()

        for i in range(len(self.data)):
            if "about" in self.data[i].keys():
                self.data[i]["about_text"] = self.data[i]["about"].replace("\n", " ")
            else: self.data[i]["about_text"] = "None"

            if "areas_of_expertise" in self.data[i].keys():
                self.data[i]["areas_of_expertise_text"] = " ".join(self.data[i]["areas_of_expertise"])
            else:
                self.data[i]["areas_of_expertise_text"] = "None"

        # simprobs = docsim.similarity_query("fluidmechanics", areas_of_expertise)
        # strings = [areas_of_expertise[i] for i in range(len(simprobs)) if simprobs[i] > 0.5]
        # print(strings)

    def name(self) -> Text:
        return "action_provide_recommendations_about"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # keyword_lst = [x for i in tracker.latest_message['entities'] if i["entity"] == "subject" and i["confidence_entity"] > 0.2 for x in i["value"].split()]
        # result = self._generate_recommendations(keyword_lst)
        userdetails = ActionProvideReccomendations.about_recommendations[tracker.sender_id]
        result = self._generate_recommendations(userdetails[1], userdetails[0])

        outputtext = "Sorry that I couldn't be of more help. I thought of more recommendations for you, judging by thier about section. "
        outputtext += "Here are 3 more professors that might be of interest to you: " + ", ".join([i["name"]+" ("+i["link"]+")" for i in result]) + ". "
        outputtext += "Hopefully, these suggestions are more useful. Thank you for your patience, I'll see you next time!."

        dispatcher.utter_message(text="These are extra resources i found for you. {}".format(outputtext))

        return []

    def _generate_recommendations(self, keyword_list: list, prev_recommendations) -> List[Integer]:
        # Find the top 3 professors with the highest similarity to the query
        # print([i["areas_of_expertise_text"] for i in self.data])

        simprobs = self.docsim.similarity_query(" ".join(keyword_list), [i["about_text"] for i in self.data])
        
        retdata = self.data.copy()

        #sort by similarity
        for i in range(len(retdata)):
            retdata[i]["similarity"] = simprobs[i]
        
        retdata = [i for i in retdata if i["_id"] not in [x["_id"] for x in prev_recommendations]]
        retdata = sorted(retdata, key=lambda x: x["similarity"], reverse=True)
        return retdata[:3]

class ActionGiveProfContact(Action):

    def __init__(self):
        self.data = ActionProvideReccomendations.data
        self.names = [i["name"].replace("Professor ", "").replace("Dr ", "") for i in self.data]

    def name(self) -> Text:
        return "action_give_prof_contact"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # get name from entities
        name2 = [x for i in tracker.latest_message['entities'] if i["entity"] == "professor" and i["confidence_entity"] > 0.2 for x in i["value"].split()]
        name = list(set(name2))
        if len(name) == 0:
            dispatcher.utter_message(text="Sorry, I didn't quite catch the name. Can you try framing your sentence in a different way?")
            return []
        elif len(name) > 1:
            namex = " ".join([i for i in reversed(name)])
            name[0] = " ".join([i for i in name])
        name = name[0].lower().replace("professor ", "").replace("dr ", "")
        print(name)
        # check most similar name using docsim
        
        #search for professor in names
        prof = [i for i in self.data if name in i["name"].lower().replace("professor ", "").replace("dr ", "") or \
            i["name"].lower().replace("professor ", "").replace("dr ", "") in name]
        print([i["name"].lower() for i in self.data])
        if len(prof) == 0:
            prof = [i for i in self.data if namex in i["name"].lower().replace("professor ", "").replace("dr ", "") or \
                i["name"].lower().replace("professor ", "").replace("dr ", "") in namex]
            if len(prof) == 0:
                dispatcher.utter_message(text="Sorry, I couldn't find any professors with that name. Can you try framing your sentence in a different way?")
                return []
            
        prof = prof[0]
        contact_string = []
        if "contact_details" in prof.keys():
            for i, j in prof["contact_details"].items():
                contact_string.append(j + " (" + i + ")")
            contact_string = ", ".join(contact_string)
            expertise = ""
            if "areas_of_expertise" in prof.keys():
                expertise = "Their areas of expertise are in: " + ", ".join(prof["areas_of_expertise"])
            if expertise == "":
                dispatcher.utter_message(text="A little bit about " + prof["name"] + ": " + prof["about_text"] + "\nYou can contact them at " + contact_string \
                    + ". Here is their website: " + prof["link"] + ".")
            else:
                dispatcher.utter_message(text="A little bit about " + prof["name"] + ": " + prof["about_text"] + "\n" + expertise + "\nYou can contact them at " + contact_string \
                    + ". Here is their website: " + prof["link"] + "." )
        else:
            expertise = ""
            if "areas_of_expertise" in prof.keys():
                expertise = "Their areas of expertise are in: " + ", ".join(prof["areas_of_expertise"])
            if expertise == "":
                dispatcher.utter_message(text="A little bit about " + prof["name"] + ": " + prof["about_text"] + "\nHere is their website: " + prof["link"] + ".")
            else:
                dispatcher.utter_message(text="A little bit about " + prof["name"] + ": " + prof["about_text"] + "\n" + expertise + \
                    + ". Here is their website: " + prof["link"] + "." )
        return []