import os
import time
from langchain_text_splitters import CharacterTextSplitter
from database import COLLECTION_NAME, doc_store
from langchain_community.document_loaders.pdf import PyMuPDFLoader
from qdrant_client.http.models import Filter, FieldCondition, MatchValue


dir = os.environ.get("PDF_DIR", os.path.join(os.path.dirname(__file__), "sample-data"))

text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=50)

for pdf_file_name in os.listdir(dir):
    pdf_file_path = os.path.join(dir, pdf_file_name)
    print(f"Loading and splitting {pdf_file_path}...")

    loader = PyMuPDFLoader(file_path=pdf_file_path)
    docs = loader.load_and_split(text_splitter=text_splitter)

    print(f"{pdf_file_path}: {len(docs)}")

    print("Deleting existing points for document...")
    filter = Filter(
        must=[FieldCondition(
            key="metadata.source",
            match=MatchValue(value=pdf_file_path),
        )]
    )
    result = doc_store.client.delete(collection_name=COLLECTION_NAME, points_selector=filter)

    print(result)

    print("Adding new points for document...")
    start_time = time.time()

    doc_store.add_documents(documents=docs)

    time_taken = time.time() - start_time
    print(f"Added {len(docs)} documents in {time_taken:.2f} seconds")

    print("Done!")