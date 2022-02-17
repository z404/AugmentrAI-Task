# AugmentrAI-Task

## Given Task

Problem Statement: University Expertise Recommender using Rasa Chatbot 

1. Scrape all data of professors only from [Swansea University Website](https://www.swansea.ac.uk/staff/engineering/#associate-professors=is-expanded&lecturers-and-tutors=is-expanded&professors=is-expanded&readers=is-expanded&senior-lecturers=is-expanded). Store the data in MongoDb.
2. Create a chatbot using Rasa.ai framework, and train it on the scraped data.

    1. The chatbot should be able to greet you.
    2. A user would ask about a topic he might want help with, and relevantprofessor with expertise should be recommended not more than 3 at any time.
    3. Recommendation can be based on expertise list in profile or from descriptions etc

## Navigation

1. [The Task](#given-task)
2. [Solution](#solution)
3. [Installation](#installation)
4. [Capabilities](#capabilities-of-the-bot)

## Solution

The solution is to create a rasa bot with a knowledge base of all the professors in the university. It should have proper followable stories and actions. It should be able to judge the user's input and recommend relevant professors according to requested topics.

The scraping of the given website is done by [scaper_script.py](./scraper_script.py). This script can also be imported into other python programs. Passing `testing=True` to the script will scrape the website and store the data in a text file instead of MongoDB.

The stories and actions are defined in [stories.md](./rasa_model_train/data/stories.yml) and [actions.py](./rasa_model_train/actions/actions.py). The rasa pipeline used is defined in [config.yml](./rasa_model_train/config.yml). More about the bot can be found in the [capabilities](#capabilities-of-the-bot) section.

To communicate with the bot, one can use `python3 rasainteraction.py <link to rasa api server>` in the root directory of the project. This script works with any rasa bot.

## Installation


The bot can be installed and deployed in 3 ways:
1. [Manual installation](#installation-manual)
2. [Docker installation](#installation-docker)
3. [Heroku deployment](#installation-heroku)


### Installation (Manual)

Step 1:

Create a mongodb cluster, and copy the base link of the cluster and set it as an environment variable.
```bash
export MONGODB_URI=<link>
```

Step 2:

As rasa only works on python 3.5 to python 3.8, we need to install the required python versions
```bash
sudo apt install build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libsqlite3-dev libreadline-dev libffi-dev curl libbz2-dev
curl -O https://www.python.org/ftp/python/3.8.2/Python-3.8.2.tar.xz
tar -xf Python-3.8.2.tar.xz
./configure --enable-optimizations
make -j 4
sudo make altinstall
```

Step 3:

Install, create, and activate a virtual environment for rasa and python3.8.
```bash
sudo apt install python3-venv
python3.8 -m venv rasa_env
source rasa_env/bin/activate
```

Step 4:

Install the required dependencies for rasa.
```bash
pip install -r requirements.txt
spacy download en_core_web_md
```

Step 5:

Clone this repository and train the rasa model
```bash
git clone https://github.com/z404/AugmentrAI-Task.git
cd AugmentrAI-Task/rasa_model_train
rasa train
```

Step 6:

Run the rasa servers for the API and the actions server
```bash
# The command runs the action server detached from the shell
# If this is something you do not want, run the command in a seperate terminal without the &
rasa run actions & 
rasa run --enable-api -p <PORT>
```

Step 7:

Rasa is now ready to be used. You can test it by running the following command in a seperate terminal.
```bash
python3 rasainteraction.py <link to rasa api server>
```

Step 8:

This bot can now be deployed by port forwarding the port of the rasa server.

### Installation (Docker)

Step 1:

Make sure you have docker installed. Clone this repository and run the dockerfile to create an image.
```bash
git clone https://github.com/z404/AugmentrAI-Task.git
cd AugmentrAI-Task
docker build docker build -t rasa_model .
```

Step 2:

Create a container by running the following command.
```bash
# The command runs the container detached from the shell
# If this is something you do not want, run the command in a seperate terminal without the &
docker run -p <PORT>:80 -it rasa_model -e MONGODB_URI=<link> &
```

Step 3:

Rasa is now ready to be used. You can test it by running the following command in a seperate terminal.
```bash
python3 rasainteraction.py <link to rasa api server>
```

Step 4:

This bot can now be deployed by port forwarding the port provided at the docker command.


### Installation (Heroku)

Step 1:

Fork this repository on github, and then clone your fork
```bash
git clone <fork_url>
cd AugmentrAI-Task
```

Step 2:

Make sure you have the heroku CLI installed and you have successfully logged in. Create a new heroku app. Change the Stack to container
```bash
heroku create <app name>
heroku stack:set container --app <app name>
```

Step 3:

On the heroku dashboard set the environment variable, select github as the source for the app. Then select the fork you created earlier. Choose main branch as the default branch from which to deploy. You can choose to set up automatic deployment.

Step 4:

Hit deploy. Heroku will automatically deploy the latest changes to the app. Memory might be an issue if you're deploying to free tier apps on heroku.

## Capabilities of the bot

The bot can greet a user, and ask how they are doing. The bot has relevant stories to handle sad and happy outcomes. The bot asks if the user needs any help, and if the used affirms without providing any information, it will ask for topics on which the bot can recommend relevant professors. 

The bot then recommends relevant professors based on the topics and on thier areas of expertise. If the user is unhappy with the recommendations, the bot recommends other relevant professors that are based on thier "about" section. The stories restart after each interaction. 

The bot also has the extra capability of searching for professors by name. Given a professor's name, it can search for the professor and display thier details, their contact details, and their website.

