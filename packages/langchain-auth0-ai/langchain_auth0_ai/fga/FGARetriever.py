from typing import Callable, Optional
from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document
from pydantic import PrivateAttr
from openfga_sdk import ClientConfiguration
from openfga_sdk.client.models import ClientBatchCheckItem
from auth0_ai.authorizers.fga.fga_filter import FGAFilter


class FGARetriever(BaseRetriever):
    """
    FGARetriever integrates with OpenFGA to filter documents based on fine-grained authorization (FGA).
    """

    _retriever: BaseRetriever = PrivateAttr()
    _fga_filter: FGAFilter

    def __init__(
        self,
        retriever: BaseRetriever,
        build_query: Callable[[Document], ClientBatchCheckItem],
        fga_configuration: Optional[ClientConfiguration] = None,
    ):
        """
        Initialize the FGARetriever with the specified retriever, query builder, and configuration.

        docs = self._filter_FGA(docs)
        return docs
        Args:
            retriever (BaseRetriever): The retriever used to fetch documents.
            build_query (Callable[[Document], ClientBatchCheckItem]): Function to convert documents into FGA queries.
            fga_configuration (Optional[ClientConfiguration]): Configuration for the OpenFGA client. If not provided, defaults to environment variables.
        """
        super().__init__()
        self._retriever = retriever
        self._fga_filter = FGAFilter[Document](build_query, fga_configuration)

    async def _aget_relevant_documents(self, query, *, run_manager) -> list[Document]:
        """
        Asynchronously retrieve relevant documents from the base retrieve and filter them using FGA.

        Args:
            query (str): The query for retrieving documents.
            run_manager (Optional[object]): Optional manager for tracking runs.

        Returns:
            List[Document]: Filtered and relevant documents.
        """
        docs = await self._retriever._aget_relevant_documents(
            query, run_manager=run_manager
        )
        return await self._fga_filter.filter(docs, lambda doc: doc.id)

    def _get_relevant_documents(self, query, *, run_manager) -> list[Document]:
        """
        Retrieve relevant documents and filter them using FGA.

        Args:
            query (str): The query for retrieving documents.
            run_manager (Optional[object]): Optional manager for tracking runs.

        Returns:
            List[Document]: Filtered and relevant documents.
        """
        docs = self._retriever._get_relevant_documents(query, run_manager=run_manager)
        return self._fga_filter.filter_sync(docs, lambda doc: doc.id)
