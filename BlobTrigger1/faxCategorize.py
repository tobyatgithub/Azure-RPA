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
from dotenv import load_dotenv

load_dotenv()

def main(myblob: func.InputStream):
    logging.info(
        f"Python blob trigger function processed blob \n"
        f"Name: {myblob.name}\n"
        f"Blob Size: {myblob.length} bytes"
    )

    # Azure Function App - radiologyrequests - Configuration - Application settings
    endpoint = os.environ["END_POINT"]
    apim_key = os.environ["API_KEY"]

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

    # https://github.com/Azure/azure-sdk-for-python/blob/main/sdk/formrecognizer/azure-ai-formrecognizer/samples/v3.2/sample_convert_to_and_from_dict.py
    # convert the received model to a dictionary
    analyze_result_dict = result.to_dict()

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
    # blob_service_client = BlobServiceClient.from_connection_string(
    #     "DefaultEndpointsProtocol=https;AccountName=neufaxstorage;AccountKey=h+Kt/4Zwr2PkIPmRXZskj1mttcuj/Msxcg0K3IF2MVsqZf0PscH4vxeQflB5TbDtVdB6wGqAIHQF+AStjOEXlg==;EndpointSuffix=core.windows.net")
    storage_account_name = os.environ["STORAGE_ACCOUNT_NAME"]
    storage_account_key = os.environ["STORAGE_ACCOUNT_KEY"]
    blob_service_client = BlobServiceClient.from_connection_string(f"DefaultEndpointsProtocol=https;AccountName={storage_account_name};AccountKey={storage_account_key};EndpointSuffix=core.windows.net")
    
    # blob_service_client = BlobServiceClient(
    #     account_url="https://neufaxstorage.blob.core.windows.net",
    #     credential={
    #         "account_name": storage_account_name,
    #         "account_key": storage_account_key,
    #     },
    # )

    container_client = blob_service_client.get_container_client("output")
    text1 = os.path.basename(myblob.name)
    name1 = (os.path.splitext(text1)[0]) + ".json"

    # save the dictionary as JSON content in a JSON file, use the AzureJSONEncoder
    # to help make types, such as dates, JSON serializable
    # NOTE: AzureJSONEncoder is only available with azure.core>=1.18.0.
    container_client.upload_blob(
        name=name1,
        data=json.dumps(analyze_result_dict, cls=AzureJSONEncoder),
        overwrite=True,
    )
