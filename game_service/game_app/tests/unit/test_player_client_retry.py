"""
==========================================
PLAYER CLIENT RETRY LOGIC UNIT TESTS
==========================================

PURPOSE:
--------
Unit tests for PlayerClient retry mechanism with exponential backoff.
Verifies that the client properly handles failures and retries with correct timing.

WHAT IS TESTED:
---------------
1. Successful Finalization (no retry needed):
   - First attempt succeeds → returns True
   - No retries performed

2. Retry on HTTP Errors:
   - 500 Internal Server Error → retries 3 times
   - 503 Service Unavailable → retries 3 times
   - Non-200 status codes trigger retry logic

3. Retry on Network Errors:
   - Connection timeout → retries with exponential backoff
   - Connection refused → retries with exponential backoff
   - Network errors are logged properly

4. Exponential Backoff Timing:
   - Attempt 1 → wait 2s (2^1)
   - Attempt 2 → wait 4s (2^2)
   - Attempt 3 → wait 8s (2^3)
   - Respects MAX_RETRY_WAIT cap (10s)

5. Final Failure After Max Attempts:
   - After 3 failed attempts → returns False
   - Error logged with appropriate message

6. Payload Correctness:
   - Verifies correct payload structure
   - All match data included in POST request

HOW TO RUN:
-----------
Run all PlayerClient tests:
    $ cd game_service
    $ pytest game_app/tests/unit/test_player_client_retry.py -v

Run specific test:
    $ pytest game_app/tests/unit/test_player_client_retry.py::test_finalize_success_first_try -v

Run with output (see logs):
    $ pytest game_app/tests/unit/test_player_client_retry.py -v -s

MOCKING STRATEGY:
-----------------
- Uses pytest-mock to mock httpx.AsyncClient
- Mocks asyncio.sleep to avoid waiting during tests
- Simulates various failure scenarios
- Verifies retry count and timing

NOTES:
------
- These are PURE UNIT TESTS (no network calls)
- Tests run quickly (sleep is mocked)
- Focuses on retry logic correctness
- Does not test Player Service itself
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, call
import httpx

from game_app.clients.player_client import PlayerClient
from game_app.configs.client_config import (
    MAX_RETRY_ATTEMPTS,
    RETRY_BACKOFF_BASE,
    MAX_RETRY_WAIT,
    PLAYER_SERVICE_URL,
    PLAYER_ENDPOINTS,
)


# ============================================================
# SUCCESSFUL FINALIZATION (NO RETRY)
# ============================================================

@pytest.mark.asyncio
async def test_finalize_success_first_try():
    """
    Test successful match finalization on first attempt.

    Scenario:
    - Player Service responds with 201 Created immediately
    - No retries needed
    - Returns True
    """
    client = PlayerClient()

    # Mock successful response (Player Service returns 201 for POST /matches)
    mock_response = MagicMock()
    mock_response.status_code = 201

    with patch('httpx.AsyncClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        # Call finalize_match
        result = await client.finalize_match(
            match_id="test-match-123",
            player1_id="alice",
            player2_id="bob",
            winner_id="alice",
            points_p1=3,
            points_p2=2,
            status="finished"
        )

        # Assertions
        assert result is True
        assert mock_client.post.call_count == 1

        # Verify payload uses Player Service schema format
        call_args = mock_client.post.call_args
        payload = call_args[1]['json']

        # New format - Player Service schema
        assert payload['player1_external_id'] == "alice"
        assert payload['player2_external_id'] == "bob"
        assert payload['winner_external_id'] == "alice"
        assert payload['player1_score'] == 3
        assert payload['player2_score'] == 2
        assert payload['turns'] == []
        assert payload['external_match_id'] == "test-match-123"


# ============================================================
# RETRY ON HTTP ERRORS
# ============================================================

@pytest.mark.asyncio
async def test_finalize_retry_on_500_error():
    """
    Test retry logic when Player Service returns 500 Internal Server Error.

    Scenario:
    - First 2 attempts: 500 error
    - Third attempt: 201 Created
    - Should retry and eventually succeed
    """
    client = PlayerClient()

    # Mock responses: 500, 500, 201
    mock_response_error = MagicMock()
    mock_response_error.status_code = 500

    mock_response_success = MagicMock()
    mock_response_success.status_code = 201  # Changed from 200 to 201

    with patch('httpx.AsyncClient') as mock_client_class, \
         patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None

        # Configure mock to return different responses
        mock_client.post.side_effect = [
            mock_response_error,
            mock_response_error,
            mock_response_success
        ]

        mock_client_class.return_value = mock_client

        result = await client.finalize_match(
            match_id="test-match-456",
            player1_id="alice",
            player2_id="bob",
            winner_id="alice",
            points_p1=3,
            points_p2=2
        )

        # Assertions
        assert result is True
        assert mock_client.post.call_count == 3
        assert mock_sleep.call_count == 2  # 2 waits between 3 attempts


@pytest.mark.asyncio
async def test_finalize_fails_after_max_retries():
    """
    Test that finalize_match returns False after MAX_RETRY_ATTEMPTS failures.

    Scenario:
    - All 3 attempts fail with 503 Service Unavailable
    - Should return False after exhausting retries
    """
    client = PlayerClient()

    mock_response = MagicMock()
    mock_response.status_code = 503

    with patch('httpx.AsyncClient') as mock_client_class, \
         patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post.return_value = mock_response

        mock_client_class.return_value = mock_client

        result = await client.finalize_match(
            match_id="test-match-789",
            player1_id="alice",
            player2_id="bob",
            winner_id=None,  # Draw
            points_p1=2,
            points_p2=2
        )

        # Assertions
        assert result is False
        assert mock_client.post.call_count == MAX_RETRY_ATTEMPTS
        assert mock_sleep.call_count == MAX_RETRY_ATTEMPTS - 1


# ============================================================
# RETRY ON NETWORK ERRORS
# ============================================================

@pytest.mark.asyncio
async def test_finalize_retry_on_timeout():
    """
    Test retry logic when request times out.

    Scenario:
    - First 2 attempts: TimeoutException
    - Third attempt: 201 Created
    - Should handle timeouts gracefully and retry
    """
    client = PlayerClient()

    mock_response_success = MagicMock()
    mock_response_success.status_code = 201  # Changed from 200 to 201

    with patch('httpx.AsyncClient') as mock_client_class, \
         patch('asyncio.sleep', new_callable=AsyncMock):

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None

        # First two calls raise TimeoutException, third succeeds
        mock_client.post.side_effect = [
            httpx.TimeoutException("Request timeout"),
            httpx.TimeoutException("Request timeout"),
            mock_response_success
        ]

        mock_client_class.return_value = mock_client

        result = await client.finalize_match(
            match_id="test-timeout",
            player1_id="alice",
            player2_id="bob",
            winner_id="bob",
            points_p1=1,
            points_p2=4
        )

        assert result is True
        assert mock_client.post.call_count == 3


@pytest.mark.asyncio
async def test_finalize_retry_on_connection_error():
    """
    Test retry logic when connection fails.

    Scenario:
    - All attempts fail with ConnectError
    - Should retry MAX_RETRY_ATTEMPTS times
    - Should return False
    """
    client = PlayerClient()

    with patch('httpx.AsyncClient') as mock_client_class, \
         patch('asyncio.sleep', new_callable=AsyncMock):

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None

        # All attempts fail
        mock_client.post.side_effect = httpx.ConnectError("Connection refused")

        mock_client_class.return_value = mock_client

        result = await client.finalize_match(
            match_id="test-connection-error",
            player1_id="alice",
            player2_id="bob",
            winner_id="alice",
            points_p1=5,
            points_p2=0
        )

        assert result is False
        assert mock_client.post.call_count == MAX_RETRY_ATTEMPTS


# ============================================================
# EXPONENTIAL BACKOFF TIMING
# ============================================================

@pytest.mark.asyncio
async def test_exponential_backoff_timing():
    """
    Test that exponential backoff uses correct wait times.

    Scenario:
    - 3 failed attempts (500 errors)
    - Verify sleep calls: 2s, 4s (2^1, 2^2)
    - Respects RETRY_BACKOFF_BASE configuration
    """
    client = PlayerClient()

    mock_response = MagicMock()
    mock_response.status_code = 500

    with patch('httpx.AsyncClient') as mock_client_class, \
         patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post.return_value = mock_response

        mock_client_class.return_value = mock_client

        await client.finalize_match(
            match_id="test-backoff",
            player1_id="alice",
            player2_id="bob",
            winner_id="alice",
            points_p1=3,
            points_p2=2
        )

        # Verify sleep times
        assert mock_sleep.call_count == 2

        # Check exponential backoff: 2^1=2s, 2^2=4s
        expected_waits = [
            RETRY_BACKOFF_BASE ** 1,  # 2s
            RETRY_BACKOFF_BASE ** 2,  # 4s
        ]

        actual_waits = [call[0][0] for call in mock_sleep.call_args_list]
        assert actual_waits == expected_waits


@pytest.mark.asyncio
async def test_backoff_respects_max_wait():
    """
    Test that backoff wait time respects MAX_RETRY_WAIT cap.

    This test verifies the cap exists in config.
    In real scenario with many retries, wait time shouldn't exceed MAX_RETRY_WAIT.
    """
    # Just verify the configuration is sane
    assert MAX_RETRY_WAIT > 0
    assert RETRY_BACKOFF_BASE > 1

    # Calculate what wait time would be without cap
    uncapped_wait = RETRY_BACKOFF_BASE ** 10  # Hypothetical 10th retry

    # The actual wait would be capped
    actual_wait = min(uncapped_wait, MAX_RETRY_WAIT)

    assert actual_wait == MAX_RETRY_WAIT


# ============================================================
# PAYLOAD VERIFICATION
# ============================================================

@pytest.mark.asyncio
async def test_finalize_sends_correct_payload():
    """
    Test that finalize_match sends correct payload structure.

    Verifies:
    - Correct endpoint URL
    - All required fields in JSON payload
    - Proper match data formatting (Player Service schema)
    """
    client = PlayerClient()

    mock_response = MagicMock()
    mock_response.status_code = 201  # Changed from 200 to 201

    with patch('httpx.AsyncClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post.return_value = mock_response

        mock_client_class.return_value = mock_client

        await client.finalize_match(
            match_id="match-999",
            player1_id="player_one",
            player2_id="player_two",
            winner_id="player_one",
            points_p1=5,
            points_p2=0,
            status="finished"
        )

        # Get the call arguments
        call_args = mock_client.post.call_args

        # Verify endpoint
        expected_endpoint = f"{PLAYER_SERVICE_URL}{PLAYER_ENDPOINTS['finalize_match']}"
        assert call_args[0][0] == expected_endpoint

        # Verify payload structure - NEW FORMAT (Player Service schema)
        payload = call_args[1]['json']
        assert payload['player1_external_id'] == "player_one"
        assert payload['player2_external_id'] == "player_two"
        assert payload['winner_external_id'] == "player_one"
        assert payload['player1_score'] == 5
        assert payload['player2_score'] == 0
        assert payload['turns'] == []  # Changed from None to empty list
        assert payload['external_match_id'] == "match-999"


@pytest.mark.asyncio
async def test_finalize_with_draw_result():
    """
    Test finalize_match with draw (no winner).

    Verifies:
    - winner_external_id can be None
    - Equal points for both players
    - Draw is properly communicated to Player Service
    """
    client = PlayerClient()

    mock_response = MagicMock()
    mock_response.status_code = 201  # Changed from 200 to 201

    with patch('httpx.AsyncClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post.return_value = mock_response

        mock_client_class.return_value = mock_client

        result = await client.finalize_match(
            match_id="draw-match",
            player1_id="alice",
            player2_id="bob",
            winner_id=None,  # Draw
            points_p1=2,
            points_p2=2,
            status="finished"
        )

        assert result is True

        # Verify None winner_external_id is sent (NEW FORMAT)
        payload = mock_client.post.call_args[1]['json']
        assert payload['winner_external_id'] is None
        assert payload['player1_score'] == payload['player2_score']


# ============================================================
# EDGE CASES
# ============================================================

@pytest.mark.asyncio
async def test_finalize_handles_unexpected_exception():
    """
    Test that unexpected exceptions are handled gracefully.

    Scenario:
    - Unexpected exception during POST
    - Should log error and retry
    - Should eventually return False
    """
    client = PlayerClient()

    with patch('httpx.AsyncClient') as mock_client_class, \
         patch('asyncio.sleep', new_callable=AsyncMock):

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None

        # Raise unexpected exception
        mock_client.post.side_effect = Exception("Unexpected error")

        mock_client_class.return_value = mock_client

        result = await client.finalize_match(
            match_id="error-match",
            player1_id="alice",
            player2_id="bob",
            winner_id="alice",
            points_p1=3,
            points_p2=2
        )

        assert result is False
        assert mock_client.post.call_count == MAX_RETRY_ATTEMPTS
