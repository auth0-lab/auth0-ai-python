import os
from llama_index.core import VectorStoreIndex, Document
from llama_index_auth0_ai import FGARetriever
from openfga_sdk.client.models import ClientBatchCheckItem


def create_store():
    current_dir = os.path.dirname(__file__)

    public_doc_path = os.path.join(current_dir, "../assets/docs/public-doc.md")

    private_doc_path = os.path.join(current_dir, "../assets/docs/private-doc.md")

    with open(public_doc_path, "r", encoding="utf-8") as file:
        public_doc_content = file.read()

    with open(private_doc_path, "r", encoding="utf-8") as file:
        private_doc_content = file.read()

    documents = [
        Document(text=public_doc_content, doc_id="public-doc"),
        Document(text=private_doc_content, doc_id="private-doc"),
    ]

    vectorStoreIndex = VectorStoreIndex.from_documents(documents)
    return vectorStoreIndex


def create_retriever(user: str):
    base_retriever = create_store().as_retriever()
    return FGARetriever(
        base_retriever,
        build_query=lambda node: ClientBatchCheckItem(
            user=f"user:{user}",
            object=f"doc:{node.node.ref_doc_id}",
            relation="viewer",
        ),
    )


__all__ = ["create_retriever", "create_retriever"]
