# Azure RPA repo

## Intro
In this repo, I tested how to use Azure Python SDK to conduct some RPA tasks.

The 2 examples I did so far:
1. The blob [tutorial](https://learn.microsoft.com/en-us/azure/applied-ai-services/form-recognizer/tutorial-azure-function?view=form-recog-3.0.0&source=docs) from Azure
2. The pdf with form-recognizer in the capstone project 2022 (where we receive medical request forms and use key words to categorize them into several different pre-determined classes, and save to different containers accordingly.)

## How to run
Pretty much similar to the step mentioned in the blob tutorial above, and here're the summarized steps:
1. install required library and plugins (Azure Account, Azure Functions, Azure Resources, Python, etc.) recommend installation via the tutorial material.
2. log in the azure account (via click the azure tab on the left tab bar of vs code.)
3. after log in the account via azure tab, make sure you have "BlobTrigger1" under "WORKSPACE -> Local Project -> Functions". (if not, check tutorial)
4. create a `.env` add your own credentials to it (END_POINT, API_KEY, STORAGE_ACCOUNT_NAME, and STORAGE_ACCOUNT_KEY).
5. go to `./BlobTrigger1/faxCategorize.py` and hit F5 to run (you can specify which python script to run in the `function.json` file)
6. now open the azure portal, go to "storage account", and upload a pdf file to the "input" container
7. after several minutes of running, a csv file with the same name shall appear in the output container

## Idea for categorization
Based on the investigation in `explore.ipynb`, it is clear that the `key_value_pairs` and the text content from `pages.lines` are the most promising information.

Idea for the 1st version:
- Use text content first for key words matching.
- Search for key words for all 4 types of requests that we are interested in. (lower() and remove punctuations.)
- If only one of them were True, then we are sure abt it.
- If multiple ones are true, we then check the key value pair for the "requested" key and use the associated content to make the decision.
- If neither method triggers, then put into undecided folder.

Probably shall add a logging as (bcz this this this condition, thus file <...> is saved to xxx folder.) The reason being the first method (key word) shall be very reliable, and not so much for the second method.