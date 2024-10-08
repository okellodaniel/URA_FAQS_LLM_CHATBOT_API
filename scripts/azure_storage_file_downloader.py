import os
from azure.storage.blob import BlobServiceClient, BlobClient

connection_string = os.getenv("AZURE_STORAGE_CONN_STRING")
container_name = os.getenv("AZURE_STORAGE_CONTAINER")

download_folder = "data"

# Initialize the BlobServiceClient
blob_service_client = BlobServiceClient.from_connection_string(connection_string)

# Create the container client
container_client = blob_service_client.get_container_client(container_name)

if not os.path.exists(download_folder):
    os.makedirs(download_folder)

def download_blob(blob_name):
    blob_client = container_client.get_blob_client(blob_name)
    
    download_file_path = os.path.join(download_folder, blob_name)

    with open(download_file_path, "wb") as download_file:

        download_file.write(blob_client.download_blob().readall())
    
    print(f"Downloaded {blob_name} to {download_file_path}")

# List and download all blobs in the container
try:
    blobs = container_client.list_blobs()
    for blob in blobs:
        download_blob(blob.name)
except Exception as e:
    print(f"Error occurred: {str(e)}")
