from langchain_community.embeddings.huggingface import HuggingFaceBgeEmbeddings


model_name = "BAAI/bge-small-en-v1.5"
model_kwargs = {"device": "cpu"}
encode_kwargs = {"normalize_embeddings": True}
embeddings = HuggingFaceBgeEmbeddings(
    model_name=model_name, model_kwargs=model_kwargs, encode_kwargs=encode_kwargs
)