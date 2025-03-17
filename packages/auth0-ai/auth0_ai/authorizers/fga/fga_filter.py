from typing import Callable, Optional
from auth0_ai.authorizers.fga.fga_client import (
    build_openfga_client,
    build_openfga_client_sync,
)
from pydantic import PrivateAttr
from openfga_sdk import ClientConfiguration
from openfga_sdk.client.models import ClientBatchCheckItem
from openfga_sdk.client.client import ClientBatchCheckRequest


class FGAFilter[T]:
    _query_builder: Callable[[T], ClientBatchCheckItem] = PrivateAttr()
    _fga_configuration: ClientConfiguration

    def __init__(
        self,
        query_builder: Callable[[T], ClientBatchCheckItem],
        fga_configuration: Optional[ClientConfiguration],
    ):
        """
        Initialize the FGAFilter with the specified query builder, and FGA parameters.

        Args:
            query_builder (Callable[[Document], ClientBatchCheckItem]): Function to convert documents into FGA queries.
            fga_configuration (Optional[ClientConfiguration]): Configuration for the OpenFGA client. If not provided, defaults to environment variables.
        """
        self._fga_configuration = fga_configuration
        self._query_builder = query_builder

    async def filter(self, documents: list[T]) -> list[T]:
        """
        Asynchronously filter documents using OpenFGA.

        Args:
            documents (List[T]): List of documents to filter.

        Returns:
            List[T]: Filtered list of documents authorized by FGA.
        """
        async with build_openfga_client(self._fga_configuration) as fga_client:
            all_checks = [self._query_builder(doc) for doc in documents]
            unique_checks = list(
                {
                    (check.relation, check.object, check.user): check
                    for check in all_checks
                }.values()
            )

            doc_to_obj = {
                doc: check.object for check, doc in zip(all_checks, documents)
            }

            fga_response = await fga_client.batch_check(
                ClientBatchCheckRequest(checks=unique_checks)
            )
            await fga_client.close()

            permissions_map = {
                result.request.object: result.allowed for result in fga_response.result
            }

            return [
                doc
                for doc in documents
                if doc_to_obj[doc] in permissions_map
                and permissions_map[doc_to_obj[doc]]
            ]

    def filter_sync(self, documents: list[T]) -> list[T]:
        """
        Synchronously filter documents using OpenFGA.

        Args:
            documents (List[T]): List of documents to filter.

        Returns:
            List[T]: Filtered list of documents authorized by FGA.
        """
        with build_openfga_client_sync(self._fga_configuration) as fga_client:
            all_checks = [self._query_builder(doc) for doc in documents]
            unique_checks = list(
                {
                    (check.relation, check.object, check.user): check
                    for check in all_checks
                }.values()
            )

            doc_to_obj = {
                doc: check.object for check, doc in zip(all_checks, documents)
            }

            fga_response = fga_client.batch_check(
                ClientBatchCheckRequest(checks=unique_checks)
            )

            permissions_map = {
                result.request.object: result.allowed for result in fga_response.result
            }

            return [
                doc
                for doc in documents
                if doc_to_obj[doc] in permissions_map
                and permissions_map[doc_to_obj[doc]]
            ]
