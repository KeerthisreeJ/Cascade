from azure.storage.blob import BlobServiceClient
import os
import uuid


def upload_resume(file_bytes: bytes, filename: str) -> str:

    conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    container_name = "resumes"

    blob_service = BlobServiceClient.from_connection_string(conn_str)

    extension = filename.split(".")[-1]
    blob_name = f"{uuid.uuid4()}.{extension}"

    blob_client = blob_service.get_blob_client(
        container=container_name,
        blob=blob_name
    )

    blob_client.upload_blob(file_bytes, overwrite=True)

    return blob_client.url