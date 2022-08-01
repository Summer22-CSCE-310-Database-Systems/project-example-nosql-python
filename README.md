# CSCE 310 - Sample App NoSQL Python

## Introduction ##

This project provides sample code for the project of CSCE 310 of Summer 2022 written following a NoSQL database design.
Implemented in Python 3, we use Firebase and Firestore as our server, Flask as our backend, and HTML as our frontend.

## Requirements ##

* Python 3.10
* Flask - 2.1.2
* Firebase-Admin 5.2


## Installation ##

First, link your Google account to [Firebase](https://firebase.google.com/), create a project, and deploy a [Firestore Database](https://firebase.google.com/docs/firestore).

Make sure you have Anaconda installed. If not, install it via your preferred conda installer. We recommend [Miniconda](https://docs.conda.io/en/latest/miniconda.html).

To install the remaining dependencies, simply enter the following in an anaconda-enabled terminal:
 
```
conda create -n csce310app python=3.10
conda activate csce310app
conda install -c anaconda flask
pip install --upgrade firebase-admin
```


## Connect to Database ##

Before running the application, you should create and download private credentials to allow our Python application to talk to our Firebase database.

To do that, you should enter your Firebase console. Then, you should go to Project settings -> Service Accounts, then click the button "Generate new private key". It will generate a json file that we recommend saving next to the main application file "app.py". Now, you can update the credentials path in "app.py" to reflect the path to your credentials file. By default, the application expects the credentials file to be named:

 `csce310-app-cred.json`

 And for it to be located next to the app.py script.

## Execute Application ##

To run our web application, simply run the command 

```
flask run
```

in your preferred terminal. The flask application should start automatically. It can be accessed on a browser via the link [http://localhost:5000](http://localhost:5000).


## Support

If you have any issues executing this application, do not hesitate to contact the responsible TA at [pedrofigueiredo@tamu.edu](pedrofigueiredo@tamu.edu), or attend his office hours.
