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
from dotenv import dotenv_values
import os

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


class ActionAskForEntity(Action):

    def name(self) -> Text:
        return "action_ask_for_entity"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(text="I need a few more details before I can proceed. Could you please provide a description of what topic you want assistance on?")

        return []

class ActionProvideReccomendations(Action):

    def __init__(self):
        # Initializing document database
        print("----------------INIT----------------")
        config = dotenv_values(".env")
        monclient = pymongo.MongoClient(config["MONGODB_URI"])
        professor_database = monclient["professor_database"]
        prof_collection = professor_database["prof_collection"]
        self.data = [i for i in prof_collection.find({})]
        
        # TODO: Fix areas of expertise
        # TODO: Add about
        # TODO: Fix scraper
        # self.areas_of_expertise = []
        # self.about = []
        # for i in self.data:
        #     if "about" in i.keys():
        #         self.about.append(i["about"])
            
        #     if "areas_of_expertise" in i.keys():
        #         self.areas_of_expertise.append(" ".join(i["areas_of_expertise"]))

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
        result = self._generate_recommendations(keyword_lst)
        dispatcher.utter_message(text="I have found some resources for you. {}".format(result))

        return []

    def _generate_recommendations(self, keyword_list: list) -> List[Integer]:
        # Find the top 3 professors with the highest similarity to the query
        # print([i["areas_of_expertise_text"] for i in self.data])
        simprobs = self.docsim.similarity_query(" ".join(keyword_list), [i["areas_of_expertise_text"] for i in self.data])
        
        retdata = self.data.copy()

        #sort by similarity
        for i in range(len(retdata)):
            retdata[i]["similarity"] = simprobs[i]
        
        retdata = sorted(retdata, key=lambda x: x["similarity"], reverse=True)
        return retdata[:3]