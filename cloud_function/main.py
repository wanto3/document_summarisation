import os
import json
import re
from openai import OpenAI
# from flask import escape

# Function to load JSON data from file
def load_json_data(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

# Function to summarize a text using OpenAI's GPT-4 and provide a one-sentence summary
def abstract_summary_extraction(text, api_key, summary_type="document"):
    try:
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key not found in environment variables")
        client = OpenAI(api_key=api_key)
        prompt = ""

        if summary_type == "document":
            # Asking for both a detailed summary and a one-sentence description
            prompt = ("You are a highly skilled AI trained in legal document analysis. "
                      "Please provide a detailed summary of the following legal document, "
                      "focusing on key legal points, arguments, and conclusions relevant to a legal matter. "
                      "Additionally, provide a one-sentence description of its content.")
        elif summary_type == "overall":
            # Legal expert summary for the overall matter
            prompt = ("You are a highly skilled AI trained in legal analysis. "
                      "Synthesize the following legal document summaries into a comprehensive legal overview. "
                      "Highlight key legal themes, draw connections between documents, and emphasize critical legal insights.")

        response = client.chat.completions.create(
            model="gpt-4",
            temperature=0.7,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": text}
            ]
        )

        if response.choices and len(response.choices) > 0:
            full_summary = response.choices[0].message.content
            if summary_type == "document":
                # Splitting the full summary to extract the one-sentence description
                split_summary = full_summary.split('\n\n')
                detailed_summary = split_summary[0].strip()
                one_sentence_description = split_summary[1].strip() if len(split_summary) > 1 else ""
                return detailed_summary, one_sentence_description
            else:
                # For overall summary, just return the full summary
                return full_summary, ""
        else:
            return "Summary not available", ""
    except Exception as e:
        print(f"Error during summarization: {e}")
        return "Summary not available", ""


# Function to extract metadata
def extract_metadata(cleaned_text, original_json, one_sentence_summary):
    # Extract metadata from the full text and the original JSON structure
    return {
        "Document ID": extract_document_id(original_json),
        "Number of Pages": extract_number_of_pages(original_json),
        "Document Type": extract_document_type(original_json), # Changed to original_json
        "Event Description": extract_event_description(cleaned_text),
        "Date": extract_date(cleaned_text),
        "Author": extract_author(cleaned_text),
        "Brief Description": one_sentence_summary
    }

# Function to extract document ID
def extract_document_id(document):
    return document.get("doc_id", "Unknown")

# Function to extract number of pages
def extract_number_of_pages(document):
    content = document.get("content", [])
    return len(content) if content else 0


def extract_document_type(document):
    # Assuming 'type' key exists in the document dictionary
    document_type = document.get("type", "").lower()
    if "report" in document_type:
        return "Report"
    elif "submission" in document_type:
        return "Submission"
    return "Unknown"


def extract_event_description(document_text):
    # Assuming event description is part of the document text
    match = re.search(r"flood event in (\w+)", document_text)
    return match.group(1) if match else "Not specified"


def extract_date(document):
    # Example: Extracting date
    match = re.search(r"\d{1,2}-\w{3}-\d{4}", document)
    return match.group(0) if match else "Date not available"

def extract_author(document):
    # Example: Extracting author name
    match = re.search(r"author: ([\w\s]+)", document, re.IGNORECASE)
    return match.group(1) if match else "Author not available"

# Function to load JSON data from file
def load_json_data(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

# Function to concatenate texts
def concatenate_texts(data):
    concatenated_texts = ""
    for document in data:
        for page in document['content']:
            page_text = ' '.join([word['content'] for word in page['words']])
            concatenated_texts += page_text + ' '
    return concatenated_texts.strip()


# Function to clean and preprocess text
def clean_and_preprocess_text(text):
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s.,;:\'\"()\-\/]', '', text)
    text = text.lower()
    return text

# Main function to process and summarize texts
def process_and_summarize_texts(data, api_key):
    individual_summaries, individual_metadata = summarize_each_document(data, api_key)
    overall_summary = summarize_overall_matter(individual_summaries, api_key)
    return overall_summary, individual_metadata


# Function to summarize each document individually and collect their summaries and metadata
def summarize_each_document(data, api_key):
    individual_summaries = []
    individual_metadata = []

    for i, document in enumerate(data, start=1):
        document_text = concatenate_texts([document])
        cleaned_text = clean_and_preprocess_text(document_text)
        full_summary, one_sentence_summary = abstract_summary_extraction(cleaned_text, api_key)

        # Extract metadata using the cleaned text
        metadata = {
            "Document ID": extract_document_id(document),
            "Number of Pages": extract_number_of_pages(document),
            "Document Type": extract_document_type(document),
            "Event Description": extract_event_description(cleaned_text),
            "Date": extract_date(cleaned_text),
            "Author": extract_author(cleaned_text),
            "Brief Description": one_sentence_summary
        }

        # # Print the results for each document
        # print(f"\nDocument {i} Summary:\n{full_summary}")
        # print(f"One-Sentence Summary:\n{one_sentence_summary}")
        # print(f"Metadata:\n{metadata}\n")

        individual_summaries.append(full_summary)
        individual_metadata.append(metadata)

    return individual_summaries, individual_metadata


# Function to summarize all individual summaries into one overall matter summary
def summarize_overall_matter(individual_summaries, api_key):
    concatenated_summaries = " ".join(individual_summaries)
    return abstract_summary_extraction(concatenated_summaries, api_key)

# Function to combine individual metadata into overall metadata
def combine_metadata(individual_metadata):
    combined_metadata = {
        "Total Documents": len(individual_metadata),
        "Total Pages": sum(md.get("Number of Pages", 0) for md in individual_metadata),
        "Types of Documents": list(set(md.get("Document Type", "Unknown") for md in individual_metadata)),
        "Date Range": f"{min(md.get('Date', '') for md in individual_metadata)} to {max(md.get('Date', '') for md in individual_metadata)}"
    }
    return combined_metadata

# Google Cloud Function Entry Point
def summarize_documents(request):
    # Retrieve API key from environment variables
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        return 'API key not provided in environment variables', 401

    request_json = request.get_json(silent=True)
    if not request_json:
        return 'No valid JSON data found', 400

    try:
        individual_summaries = []
        individual_metadata = []

        # Process and summarize each document
        for i, document in enumerate(request_json, start=1):
            document_text = concatenate_texts([document])
            cleaned_text = clean_and_preprocess_text(document_text)
            detailed_summary, one_sentence_description = abstract_summary_extraction(cleaned_text, api_key)

            # Extract metadata using cleaned text and original document dictionary
            metadata = extract_metadata(cleaned_text, document, one_sentence_description)

            individual_summaries.append(detailed_summary)
            individual_metadata.append(metadata)

        # Summarize the overall matter
        overall_summary, _ = abstract_summary_extraction(" ".join(individual_summaries), api_key, summary_type="overall")
        overall_metadata = combine_metadata(individual_metadata)

        response_data = {
            "Overall Matter Summary": overall_summary,
            "Overall Matter Metadata": overall_metadata,
            "Metadata for Each Document": individual_metadata
        }

        return json.dumps(response_data), 200, {'Content-Type': 'application/json'}

    except Exception as e:
        return f"Error processing request: {str(e)}", 500
    

# Function to test summarization of each document and the overall matter
def test_summarization(data, api_key):
    individual_summaries = []
    individual_metadata = []

    # Summarizing each document
    for i, document in enumerate(data, start=1):
        document_text = concatenate_texts([document])
        cleaned_text = clean_and_preprocess_text(document_text)
        detailed_summary, one_sentence_description = abstract_summary_extraction(cleaned_text, api_key)

        # Extract metadata using cleaned text and original document dictionary
        metadata = extract_metadata(cleaned_text, document, one_sentence_description)

        print(f"\nDocument {i} Summary:\n{detailed_summary}")
        print(f"One-Sentence Description:\n{one_sentence_description}")
        print(f"Metadata:\n{metadata}\n")

        individual_summaries.append(detailed_summary)
        individual_metadata.append(metadata)

    # Summarizing the overall matter
    overall_summary, _ = abstract_summary_extraction(" ".join(individual_summaries), api_key, summary_type="overall")
    overall_metadata = combine_metadata(individual_metadata)

    print("\nOverall Matter Summary:\n", overall_summary)
    print("\nOverall Matter Metadata:")
    for key, value in overall_metadata.items():
        print(f"{key}: {value}\n")


# # FOR TESTING PURPOSES
# # Load JSON data
# json_file_path = 'matter_documents_data.json'
# sample_data = load_json_data(json_file_path)

# # API key
# api_key = "openai-api-key"  # Replace with your actual API key

# # Test the summarization
# test_summarization(sample_data, api_key)