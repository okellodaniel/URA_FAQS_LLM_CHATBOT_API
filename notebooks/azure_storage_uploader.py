import os
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from dotenv import load_dotenv

load_dotenv()

# Azure Storage connection string
connection_string = os.getenv('AZURE_STORAGE_CONN_STRING')

# Name of the container where files will be uploaded
container_name = "urafaqs"

# Local directory where files are stored
local_folder = "data"  # This is your data folder

# Initialize the BlobServiceClient
blob_service_client = BlobServiceClient.from_connection_string(connection_string)

# Create the container if it doesn't already exist
container_client = blob_service_client.get_container_client(container_name)

try:
    container_client.create_container()
except Exception as e:
    print(f"Container already exists. Skipping creation. {str(e)}")

# Function to upload a single file
def upload_file_to_blob(file_name, file_path):
    try:
        # Create a BlobClient
        blob_client = container_client.get_blob_client(file_name)

        # Upload the file
        with open(file_path, "rb") as data:
            blob_client.upload_blob(data)
        print(f"Successfully uploaded {file_name} to Azure Blob Storage")
    except Exception as e:
        print(f"Failed to upload {file_name}. Error: {str(e)}")

# Iterate through the local data folder and upload each file
for root, dirs, files in os.walk(local_folder):
    for file_name in files:
        file_path = os.path.join(root, file_name)
        upload_file_to_blob(file_name, file_path)
