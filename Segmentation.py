import os
import pandas as pd
import json
from openpyxl import load_workbook
from azure.core.credentials import AzureKeyCredential
from azure.ai.textanalytics import TextAnalyticsClient
             
def extract_rows_to_text_files(file_path):
    try:
        # Create a new folder called "documents"
        os.makedirs("documents", exist_ok=True)

        # Read the file
        if file_path.endswith('.csv'):  # Check if the file has a CSV extension
            df = pd.read_csv(file_path)
        elif file_path.endswith('.xlsx'):  # Check if the file has an XLSX extension
            df = pd.read_excel(file_path)
        else:
            raise ValueError("Unsupported file format. Only CSV and Excel (XLSX) files are supported.")

        # Iterate over each row and create a text file for each row
        for index, row in df.iterrows():
            # Create a new text file
            file_name = f"documents/row_{index}.txt"
            with open(file_name, "w") as file:
                # Write the column names and row data to the text file
                for column, value in row.items():
                    file.write(f"{column}: {value}\n")
            print(f"Created {file_name}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        

# Provide the path to your Excel file
csv_file_path = "labelled_training_data.csv"

# Call the function to extract rows to text files
#extract_rows_to_text_files(csv_file_path)

# Function to perform custom text classification
def custom_text_classification(project_name, deployment_name):
    try:
        # Azure Cognitive Services endpoint and key
        endpoint = 'https://exoduslanguage.cognitiveservices.azure.com/'
        key = os.environ.get("AZURE_LANGUAGE_KEY")
        
        # Read data from an Excel file
        data = pd.read_excel('Segmentation.xlsx')
        document = data["Text"].tolist()
        
        # Initialize Text Analytics client
        text_analytics_client = TextAnalyticsClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(key),
        )
        
        # Perform single-label classification
        poller = text_analytics_client.begin_single_label_classify(document, project_name=project_name, deployment_name=deployment_name)
        
        # Get classification results for each document
        document_results = poller.result()
        categories = []
        
        for doc, classification_result in zip(document, document_results):
            if classification_result.kind == "CustomDocumentClassification":
                classification = classification_result.classifications[0]
                print("The document text '{}' was classified as '{}' with confidence score {}.".format(
                    doc, classification.category, classification.confidence_score)
                )
                categories.append(classification.category)
            elif classification_result.is_error is True:
                print("Document text '{}' has an error with code '{}' and message '{}'".format(
                    doc, classification_result.error.code, classification_result.error.message
                ))
            
            # Print the classification result
            print(classification_result.classifications)
            print()  # Print an empty line for readability
        
        # Add the categories to the data
        data["Categories"] = categories
        
        # Save the analyzed data to a new Excel file
        with pd.ExcelWriter('Segmentation_classification_Analyzed.xlsx', engine='openpyxl') as writer:
            data.to_excel(writer, index=False)
    
    except Exception as e:
        print(f"An error occurred: {str(e)}")
            
#custom_text_classification('exodusSingle', 'exodus')

def convert_labelled_data_to_json(file_path, language_code, cointainer_name, project_name, class_column_name):
    try:
        # Read CSV file or Excel file and convert it to a Pandas DataFrame
        if file_path.endswith('.csv'):  # Check if the file has a CSV extension
                df = pd.read_csv(file_path)
        elif file_path.endswith('.xlsx'):  # Check if the file has an XLSX extension
                df = pd.read_excel(file_path)
        else:
            raise ValueError("Unsupported file format. Only CSV and Excel (XLSX) files are supported.")

        # Create the JSON structure
        json_data = {
            "projectFileVersion": "2022-05-01",
            "stringIndexType": "Utf16CodeUnit",
            "metadata": {
                "projectKind": "CustomSingleLabelClassification",
                "storageInputContainerName": cointainer_name,
                "settings": {},
                "projectName": project_name,
                "multilingual": True,
                "description": "Project-description",
                "language": language_code
            },
            "assets": {
                "projectKind": "CustomSingleLabelClassification",
                "classes": [],
                "documents": []
            }
        }

        # Add classes from the data
        classes = set(df[class_column_name])
        json_data['assets']['classes'] = [{'category': c} for c in classes]

        # Add documents from the data
        for index, row in df.iterrows():
            document = {
                "location": f"row_{index}.txt",
                "language": language_code,
                "dataset": "Train",
                "class": {"category": row[class_column_name]}
            }
            json_data['assets']['documents'].append(document)

        # Convert the JSON data to a string
        json_string = json.dumps(json_data, indent=4)

        # Save the JSON data to a file
        with open('text_classification.json', 'w') as file:
            file.write(json_string)
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        
convert_labelled_data_to_json("labelled_training_data.csv", "en-us", "exodus", "exodusSingle_json_label", "Categories")