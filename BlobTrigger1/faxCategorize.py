import os
import logging
from azure.storage.blob import BlobServiceClient
from azure.ai.formrecognizer import DocumentAnalysisClient, AnalyzeResult
from azure.core.serialization import AzureJSONEncoder
from azure.core.credentials import AzureKeyCredential
import azure.functions as func
import json
import time
import requests
import os
from collections import OrderedDict
import numpy as np
import pandas as pd
from typing import List
from dotenv import load_dotenv

load_dotenv()

endpoint = os.environ["END_POINT"]
apim_key = os.environ["API_KEY"]
storage_account_name = os.environ["STORAGE_ACCOUNT_NAME"]
storage_account_key = os.environ["STORAGE_ACCOUNT_KEY"]

CT_FOLDER = "ct-requests"
MR_FOLDER = "mr-requests"
US_FOLDER = "us-requests"
BS_FOLDER = "bs-requests"
XR_FOLDER = "xr-requests"


def getKeyValuePairsFromJson(data, showPrint=False):
    contents = data.get("key_value_pairs", [])
    # contents = data.key_value_pairs

    keyList, valList = [], []
    for content in contents:
        try:
            keyList.append(content.get("key", {}).get("content", None))
            tmp = content.get("value", {})
            # tmp = content.value
            if tmp:
                valList.append(tmp.get("content", None))
                # valList.append(tmp.content)
            else:
                valList.append("NoValue")
        except:
            print("hmmm..strange why get() will return None for some tmp.")
            print(tmp)
            print(content)

    if showPrint:
        for key, value in zip(keyList, valList):
            print(key, "||", value)

    return keyList, valList


def getPageTextFromJson(data, showPrint=False):
    textList = []
    for page in data["pages"]:
        # for page in data.pages:
        for line in page["lines"]:
            # for line in page.lines:
            textList.append(line.get("content").lower().strip())
            # textList.append(line.content.lower().strip())

    if showPrint:
        print(len(textList), textList)

    return textList


def searchKeyWordFromTextList(keyWord: str, textList: List[str]) -> bool:
    for text in textList:
        if keyWord in text:
            return True
    return False


def main(myblob: func.InputStream):
    logging.info(
        f"Python blob trigger function processed blob \n"
        f"Name: {myblob.name}\n"
        f"Blob Size: {myblob.length} bytes"
    )

    # Azure Function App - radiologyrequests - Configuration - Application settings
    source = myblob.read()  # read file in bytes

    # sample document
    # https://azuresdkdocs.blob.core.windows.net/$web/python/azure-ai-formrecognizer/latest/index.html#using-the-general-document-model
    document_analysis_client = DocumentAnalysisClient(
        endpoint=endpoint, credential=AzureKeyCredential(apim_key)
    )

    poller = document_analysis_client.begin_analyze_document(
        "prebuilt-document", source
    )
    result = poller.result()

    # https://github.com/Azure/azure-sdk-for-python/blob/main/sdk/formrecognizer/azure-ai-formrecognizer/samples/v3.2/sample_convert_to_and_from_dict.py
    # convert the received model to a dictionary
    analyze_result_dict = result.to_dict()  # {key: {}}

    # categorizing
    outputFolderName = "undecided"
    allText = getPageTextFromJson(analyze_result_dict)
    hasCTKeyWord = searchKeyWordFromTextList("computed tomography", allText)
    hasUltrasoundKeyWord = searchKeyWordFromTextList("ultrasound (us)", allText) or searchKeyWordFromTextList(
        "ultrasound (us) requisition", allText) or searchKeyWordFromTextList("ultrasound consultation", allText)
    hasMRKeyWord = searchKeyWordFromTextList("magnetic resonance", allText)
    hasBSKeyWord = searchKeyWordFromTextList(
        "breast scan", allText) or searchKeyWordFromTextList("breast imaging", allText)
    hasXRayKeyWord = searchKeyWordFromTextList("x-ray requisition", allText)

    keyWordSum = hasCTKeyWord + hasUltrasoundKeyWord + \
        hasMRKeyWord + hasBSKeyWord + hasXRayKeyWord
    # case 1, only 1 keyword found
    if keyWordSum == 1:
        if hasCTKeyWord:
            outputFolderName = CT_FOLDER
        elif hasUltrasoundKeyWord:
            outputFolderName = US_FOLDER
        elif hasMRKeyWord:
            outputFolderName = MR_FOLDER
        elif hasBSKeyWord:
            outputFolderName = BS_FOLDER
        elif hasXRayKeyWord:
            outputFolderName = XR_FOLDER
        else:
            raise ("Categorize error! Keyword mismatch.")
    # case 2, if no keyword found or multiple key word found, use key-value pair info
    else:
        keyList, valueList = getKeyValuePairsFromJson(analyze_result_dict)
        for key, value in zip(keyList, valueList):

            if ("exam requested" in key.strip().lower() or
                "EXAM(s) REQUESTED".lower() in key.strip().lower() or
                    "EXAM (s) REQUESTED".lower() in key.strip().lower()):

                if "ct" in value.lower():
                    outputFolderName = CT_FOLDER
                elif "us" in value.lower():
                    outputFolderName = US_FOLDER
                elif "mr" in value.lower():
                    outputFolderName = MR_FOLDER
                elif "bs" in value.lower():
                    outputFolderName = BS_FOLDER
    logging.info("toby1")
    print("toby2")
    # print("----Key-value pairs found in document----")
    # for kv_pair in result.key_value_pairs:
    #     if kv_pair.key:
    #         print(
    #             "Key '{}' found within '{}' bounding regions".format(
    #                 kv_pair.key.content,
    #                 kv_pair.key.bounding_regions,
    #             )
    #         )
    #     if kv_pair.value:
    #         print(
    #             "Value '{}' found within '{}' bounding regions\n".format(
    #                 kv_pair.value.content,
    #                 kv_pair.value.bounding_regions,
    #             )
    #         )

    # print("----Tables found in document----")
    # for table_idx, table in enumerate(result.tables):
    #     print(
    #         "Table # {} has {} rows and {} columns".format(
    #             table_idx, table.row_count, table.column_count
    #         )
    #     )
    #     for region in table.bounding_regions:
    #         print(
    #             "Table # {} location on page: {} is {}".format(
    #                 table_idx,
    #                 region.page_number,
    #                 region.polygon,
    #             )
    #         )

    # print("----Styles found in document----")
    # for style in result.styles:
    #     if style.is_handwritten:
    #         print("Document contains handwritten content: ")
    #         print(
    #             ",".join(
    #                 [
    #                     result.content[span.offset : span.offset + span.length]
    #                     for span in style.spans
    #                 ]
    #             )
    #         )

    # for page in result.pages:
    #     print("----Analyzing document from page #{}----".format(page.page_number))
    #     print(
    #         "Page has width: {} and height: {}, measured with unit: {}".format(
    #             page.width, page.height, page.unit
    #         )
    #     )

    #     for line_idx, line in enumerate(page.lines):
    #         words = line.get_words()
    #         print(
    #             "...Line # {} has {} words and text '{}' within bounding polygon '{}'".format(
    #                 line_idx,
    #                 len(words),
    #                 line.content,
    #                 line.polygon,
    #             )
    #         )

    #         for word in words:
    #             print(
    #                 "......Word '{}' has a confidence of {}".format(
    #                     word.content, word.confidence
    #                 )
    #             )

    #     for selection_mark in page.selection_marks:
    #         print(
    #             "...Selection mark is '{}' within bounding polygon '{}' and has a confidence of {}".format(
    #                 selection_mark.state,
    #                 selection_mark.polygon,
    #                 selection_mark.confidence,
    #             )
    #         )

    # logging.info(f"filename: {os.path.basename(myblob.name)}\n")

    # print("----------------------------------------")

    # convert the dictionary back to the original model
    model = AnalyzeResult.from_dict(analyze_result_dict)

    # use the model as normal
    print("----Converted from dictionary AnalyzeResult----")
    print("Model ID: '{}'".format(model.model_id))
    print("Number of pages analyzed {}".format(len(model.pages)))
    print("API version used: {}".format(model.api_version))

    print("----------------------------------------")

    # https://learn.microsoft.com/en-us/python/api/overview/azure/storage-blob-readme?view=azure-python#creating-the-client-from-a-connection-string
    # This is the connection to the blob storage, with the Azure Python SDK

    blob_service_client = BlobServiceClient.from_connection_string(
        f"DefaultEndpointsProtocol=https;AccountName={storage_account_name};AccountKey={storage_account_key};EndpointSuffix=core.windows.net")

    # container_client = blob_service_client.get_container_client("output")
    container_client = blob_service_client.get_container_client(
        outputFolderName)
    filename = os.path.basename(myblob.name)

    # save the dictionary as JSON content in a JSON file, use the AzureJSONEncoder
    # to help make types, such as dates, JSON serializable
    # NOTE: AzureJSONEncoder is only available with azure.core>=1.18.0.
    container_client.upload_blob(
        name=(os.path.splitext(filename)[0]) + ".json",
        data=json.dumps(analyze_result_dict, cls=AzureJSONEncoder),
        overwrite=True,
    )
    container_client.upload_blob(
        name=(os.path.splitext(filename)[0]) + ".pdf",
        data=source,
        overwrite=True,
    )

    # also save a copy
    backup_container_client = blob_service_client.get_container_client(
        "output")
    backup_container_client.upload_blob(
        name=(os.path.splitext(filename)[0]) + ".pdf",
        data=source,
        overwrite=True,
    )
