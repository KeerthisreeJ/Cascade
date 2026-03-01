import os
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from services.grok_service import generate_resume_feedback


def get_client():
    endpoint = os.getenv("DOC_INT_ENDPOINT")
    key = os.getenv("DOC_INT_KEY")

    if not endpoint or not key:
        raise ValueError("Document Intelligence credentials not configured.")

    return DocumentAnalysisClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(key)
    )


def analyze_resume(file_bytes: bytes) -> dict:
    """
    Extracts text via Azure Document Intelligence,
    then calls Groq to generate real AI resume feedback.
    """
    client = get_client()

    poller = client.begin_analyze_document("prebuilt-layout", file_bytes)
    result = poller.result()

    extracted_text = ""
    for page in result.pages:
        for line in page.lines:
            extracted_text += line.content + "\n"

    # Real AI feedback from Groq
    ai_feedback = generate_resume_feedback(extracted_text)

    return {
        "extracted_text": extracted_text,
        "ai_feedback":    ai_feedback,
    }