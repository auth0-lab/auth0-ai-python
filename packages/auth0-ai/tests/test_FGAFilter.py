import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from openfga_sdk.client.models import (
    ClientBatchCheckItem,
)
from auth0_ai.authorizers.fga.fga_filter import FGAFilter


# Test document class
class Document:
    def __init__(self, id, content):
        self.id = id
        self.content = content

    def __eq__(self, other):
        if not isinstance(other, Document):
            return False
        return self.id == other.id and self.content == other.content

    def __hash__(self):
        return hash((self.id, self.content))


# Sample query builder function
def query_builder(doc):
    return ClientBatchCheckItem(
        user="user:alice", relation="can_read", object=f"document:{doc.id}"
    )


# Non-hashable document class for testing custom hash function
class NonHashableDocument:
    def __init__(self, id, content):
        self.id = id
        self.content = content

    def __eq__(self, other):
        if not isinstance(other, NonHashableDocument):
            return False
        return self.id == other.id and self.content == other.content

    # Explicitly make this non-hashable
    __hash__ = None


def doc_hasher(doc):
    return doc.id


# Test fixtures
@pytest.fixture
def fga_config():
    return MagicMock()


@pytest.fixture
def documents():
    return [
        Document(id="1", content="Test 1"),
        Document(id="2", content="Test 2"),
        Document(id="3", content="Test 3"),
    ]


@pytest.fixture
def non_hashable_documents():
    return [
        NonHashableDocument(id="1", content="Test 1"),
        NonHashableDocument(id="2", content="Test 2"),
        NonHashableDocument(id="3", content="Test 3"),
    ]


@pytest.fixture
def fga_response():
    return MagicMock(
        result=[
            MagicMock(
                request=ClientBatchCheckItem(
                    user="user:alice", relation="can_read", object="document:1"
                ),
                allowed=True,
            ),
            MagicMock(
                request=ClientBatchCheckItem(
                    user="user:alice", relation="can_read", object="document:2"
                ),
                allowed=False,
            ),
            MagicMock(
                request=ClientBatchCheckItem(
                    user="user:alice", relation="can_read", object="document:3"
                ),
                allowed=True,
            ),
        ]
    )


# Tests
class TestFGAFilter:
    def test_init(self, fga_config):
        """Test that FGAFilter initializes properly"""
        filter = FGAFilter(query_builder, fga_config)
        assert filter._query_builder == query_builder
        assert filter._fga_configuration == fga_config

    @pytest.mark.asyncio
    @patch("auth0_ai.authorizers.fga.fga_filter.build_openfga_client")
    async def test_filter_async(self, mock_build_client, documents, fga_response):
        """Test the async filter method with hashable documents"""
        # Mock the FGA client
        mock_client = AsyncMock()
        mock_client.batch_check.return_value = fga_response
        mock_context_manager = MagicMock()
        mock_context_manager.__aenter__.return_value = mock_client
        mock_build_client.return_value = mock_context_manager

        # Create the filter
        fga_filter = FGAFilter(query_builder, None)

        # Call the filter method
        result = await fga_filter.filter(documents)

        # Check that only documents 1 and 3 were allowed
        assert len(result) == 2
        assert result[0].id == "1"
        assert result[1].id == "3"

        # Verify the batch check was called with the expected arguments
        mock_client.batch_check.assert_called_once()
        request = mock_client.batch_check.call_args[0][0]
        assert len(request.checks) == 3

    @pytest.mark.asyncio
    @patch("auth0_ai.authorizers.fga.fga_filter.build_openfga_client")
    async def test_filter_async_with_custom_hasher(
        self, mock_build_client, non_hashable_documents, fga_response
    ):
        """Test the async filter method with non-hashable documents and a custom hasher"""
        # Mock the FGA client
        mock_client = AsyncMock()
        mock_client.batch_check.return_value = fga_response
        mock_context_manager = MagicMock()
        mock_context_manager.__aenter__.return_value = mock_client
        mock_build_client.return_value = mock_context_manager

        # Create the filter
        fga_filter = FGAFilter(query_builder, None)

        # Call the filter method with custom hasher
        result = await fga_filter.filter(
            non_hashable_documents, hash_document=doc_hasher
        )

        # Check that only documents 1 and 3 were allowed
        assert len(result) == 2
        assert result[0].id == "1"
        assert result[1].id == "3"

    @patch("auth0_ai.authorizers.fga.fga_filter.build_openfga_client_sync")
    def test_filter_sync(self, mock_build_client, documents, fga_response):
        """Test the sync filter method"""
        # Mock the FGA client
        mock_client = MagicMock()
        mock_client.batch_check.return_value = fga_response
        mock_context_manager = MagicMock()
        mock_context_manager.__enter__.return_value = mock_client
        mock_build_client.return_value = mock_context_manager

        # Create the filter
        fga_filter = FGAFilter(query_builder, None)

        # Call the filter_sync method
        result = fga_filter.filter_sync(documents)

        # Check that only documents 1 and 3 were allowed
        assert len(result) == 2
        assert result[0].id == "1"
        assert result[1].id == "3"

        # Verify the batch check was called with the expected arguments
        mock_client.batch_check.assert_called_once()
        request = mock_client.batch_check.call_args[0][0]
        assert len(request.checks) == 3

    @patch("auth0_ai.authorizers.fga.fga_filter.build_openfga_client_sync")
    def test_filter_sync_with_custom_hasher(
        self, mock_build_client, non_hashable_documents, fga_response
    ):
        """Test the sync filter method with non-hashable documents and a custom hasher"""
        # Mock the FGA client
        mock_client = MagicMock()
        mock_client.batch_check.return_value = fga_response
        mock_context_manager = MagicMock()
        mock_context_manager.__enter__.return_value = mock_client
        mock_build_client.return_value = mock_context_manager

        # Create the filter
        fga_filter = FGAFilter(query_builder, None)

        # Call the filter_sync method with custom hasher
        result = fga_filter.filter_sync(
            non_hashable_documents, hash_document=doc_hasher
        )

        # Check that only documents 1 and 3 were allowed
        assert len(result) == 2
        assert result[0].id == "1"
        assert result[1].id == "3"

    @pytest.mark.asyncio
    @patch("auth0_ai.authorizers.fga.fga_filter.build_openfga_client")
    async def test_filter_empty_documents(self, mock_build_client):
        """Test filtering an empty document list"""
        # Mock the FGA client
        mock_client = AsyncMock()
        mock_context_manager = MagicMock()
        mock_context_manager.__aenter__.return_value = mock_client
        mock_build_client.return_value = mock_context_manager

        # Create the filter
        fga_filter = FGAFilter(query_builder, None)

        # Call the filter method with empty list
        result = await fga_filter.filter([])

        # Check that the result is an empty list
        assert result == []

        # Verify batch_check was not called
        mock_client.batch_check.assert_not_called()

    @pytest.mark.asyncio
    @patch("auth0_ai.authorizers.fga.fga_filter.build_openfga_client")
    async def test_deduplicate_checks(self, mock_build_client, fga_response):
        """Test that duplicate check requests are deduplicated"""
        # Create documents with duplicate permissions
        duplicate_docs = [
            Document(id="1", content="Test 1"),
            Document(id="1", content="Duplicate of 1"),  # Same ID results in same check
            Document(id="3", content="Test 3"),
        ]

        # Mock the FGA client
        mock_client = AsyncMock()
        mock_client.batch_check.return_value = fga_response
        mock_context_manager = MagicMock()
        mock_context_manager.__aenter__.return_value = mock_client
        mock_build_client.return_value = mock_context_manager

        # Create the filter
        fga_filter = FGAFilter(query_builder, None)

        # Call the filter method
        result = await fga_filter.filter(duplicate_docs)

        # Check that both document 1 instances are included in the result
        assert len(result) == 3
        assert all(doc.id in ["1", "3"] for doc in result)

        # Verify the batch check was called with deduplicated checks (only 2 unique checks)
        mock_client.batch_check.assert_called_once()
        request = mock_client.batch_check.call_args[0][0]
        assert len(request.checks) == 2

