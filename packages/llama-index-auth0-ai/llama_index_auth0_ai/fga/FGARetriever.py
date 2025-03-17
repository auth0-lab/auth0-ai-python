import os
from typing import Callable, Optional, List
from llama_index.core.retrievers import BaseRetriever
from pydantic import PrivateAttr
from openfga_sdk import ClientConfiguration, OpenFgaClient
from openfga_sdk.client.client import ClientBatchCheckRequest
from openfga_sdk.client.models import ClientBatchCheckItem
from openfga_sdk.sync import OpenFgaClient as OpenFgaClientSync
from openfga_sdk.credentials import CredentialConfiguration, Credentials
from auth0_ai.authorizers.fga.fga_filter import FGAFilter

from llama_index.core.schema import (
    BaseNode,
    NodeWithScore,
    QueryBundle,
)


class FGARetriever(BaseRetriever):
    """
    FGARetriever integrates with OpenFGA to filter nodes based on fine-grained authorization (FGA).
    """

    _retriever: BaseRetriever = PrivateAttr()
    _fga_filter: FGAFilter

    def __init__(
        self,
        retriever: BaseRetriever,
        build_query: Callable[[BaseNode], ClientBatchCheckItem],
        fga_configuration: Optional[ClientConfiguration] = None,
    ):
        """
        Initialize the FGARetriever with the specified retriever, query builder, and configuration.

        Args:
            retriever (BaseRetriever): The retriever used to fetch nodes.
            build_query (Callable[[BaseNode], ClientBatchCheckItem]): Function to convert nodes into FGA queries.
            fga_configuration (Optional[ClientConfiguration]): Configuration for the OpenFGA client. If not provided, defaults to environment variables.
        """
        super().__init__()
        self._retriever = retriever
        self._fga_filter = FGAFilter[BaseNode](build_query, fga_configuration)

    def _retrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        """Retrieve nodes given query and filtered by FGA access."""
        nodes = self._retriever._retrieve(query_bundle)
        nodes = self._fga_filter.filter_sync(nodes)
        return nodes

    async def _aretrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        """Retrieve nodes given query and filtered by FGA access."""
        nodes = await self._retriever._aretrieve(query_bundle)
        nodes = await self._fga_filter.filter(nodes)
        return nodes
