# coms_4156 ![travisci](https://travis-ci.com/s4chin/coms_4156.svg?token=3tkeMeV6pyEjAXfzc7xZ&branch=master)

Course project for COMS 4156 - Advanced Software Engineering

## Instructions
To run, first clone this repository

To install requirements:
```sh
pip3 install -r requirements.txt
```
To setup Google Drive Sync 
1) Turn on Google Drive API [here] (if you have any troubles, check [Python Quickstart guide]).
2) Get your .json client secret config file in [Google API Projects page] and put it in working directory (don't forget to save it as *client-secret.json*)

To run:
```sh
python3 notes.py
```
To test and generate coverage report:
```sh
pytest --pylint --pylint-rcfile=.pylintrc --cov-report html:cov_report --cov=. test_notes.py test_crypto.py
```

## Operating Instructions
This is a simple command line note-taking app. After running this app, on, you just choose ane of the options given on the screen to proceed.

### Options
- Create, Read, Update, Delete notes
- Add tags to notes
- Search notes by tags
- Save note with a password
- Set and reset a password for a session so the app doesn't ask for password repeatedly
- Sync notes with Google Drive(more setup required*)

[here]: https://console.developers.google.com/flows/enableapi?apiid=drive
[Python Quickstart guide]: https://developers.google.com/drive/v3/web/quickstart/python
[Google API Projects page]: https://console.developers.google.com/iam-admin/projects
