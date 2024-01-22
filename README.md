# Document Summarization Service

This document provides information on how to interact with the Document Summarization Service, a cloud-based function deployed on Google Cloud Platform. The service uses OpenAI's GPT-4 to generate concise summaries of documents based on provided text data.

## Service Endpoint

- **URL**: `https://us-central1-document-summerization.cloudfunctions.net/summarize_documents`
- **Method**: `POST`

## Request Format

The request should be a POST request with a payload in JSON format. The JSON structure should consist of a list of documents, where each document contains its own structure of content and metadata.

![image](https://github.com/wanto3/document_summarisation/assets/59409764/19965e5a-c7c0-417c-b4c2-f64137d7c7f0)

## Sending a Request Using cURL

cURL is a command-line tool used for transferring data with URLs. You can use cURL to send a POST request to the Document Summarization Service with your JSON data.

## Prequisites

●	cURL installed on your system.

## Sample cURL Command

```bash:
curl -X POST https://us-central1-document-summerization.cloudfunctions.net/summarize_documents \
-H "Content-Type: application/json" \
-d @matter_documents_data.json
```

## Instructions
●	Open a terminal or command prompt.
●	Run the above cURL command.
●	The response will be printed in the terminal, containing the summaries of the matter.
