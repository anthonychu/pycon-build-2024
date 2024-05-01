import os
import qdrant_client
from langchain_community.vectorstores.qdrant import Qdrant
from embeddings import embeddings
from sentence_transformers import SentenceTransformer
from qdrant_client.http.models import VectorParams, Distance


COLLECTION_NAME = "documents"

host = os.getenv("QDRANT_HOST", "localhost")
port = os.getenv("QDRANT_PORT", "6333")

doc_store = Qdrant(
    client=qdrant_client.QdrantClient(host=host, port=port, prefer_grpc=False,), 
    collection_name=COLLECTION_NAME, 
    embeddings=embeddings,
)


print("Attempting to create collection...")
try:
    transformer: SentenceTransformer = embeddings.client
    doc_store.client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=transformer.get_sentence_embedding_dimension(),  # Vector size is defined by used model
            distance=Distance.COSINE,
        ),
    )
except:
    print("Collection already exists (probably)")

