"""
Player Client - HTTP client for Player Service communication.

Handles all communication with the player service including
match finalization and player statistics updates.
"""
import httpx
import logging
import asyncio
from typing import Optional, Dict, Any

from game_app.configs.client_config import (
    PLAYER_SERVICE_URL,
    PLAYER_TIMEOUT,
    PLAYER_ENDPOINTS,
    MAX_RETRY_ATTEMPTS,
    RETRY_BACKOFF_BASE,
    MAX_RETRY_WAIT,
)

logger = logging.getLogger(__name__)


class PlayerClient:
    """
    Client for Player Service communication.

    Provides methods to finalize matches and update player statistics.
    Implements retry logic with exponential backoff.
    """

    def __init__(self):
        self.base_url = PLAYER_SERVICE_URL
        self.timeout = PLAYER_TIMEOUT

    async def finalize_match(
        self,
        match_id: str,
        player1_id: str,
        player2_id: str,
        winner_id: Optional[str],
        points_p1: int,
        points_p2: int,
        status: str = "finished"
    ) -> bool:
        """
        Notify player service about finished match.

        Sends match result to player service so it can update player statistics.
        Implements exponential backoff retry pattern.

        Args:
            match_id: Match identifier
            player1_id: First player username
            player2_id: Second player username
            winner_id: Winner username (None for draw)
            points_p1: Points scored by player1
            points_p2: Points scored by player2
            status: Match status (default: "finished")

        Returns:
            bool: True if notification succeeded, False otherwise
        """
        endpoint = f"{self.base_url}{PLAYER_ENDPOINTS['finalize_match']}"

        payload = {
            "match_id": match_id,
            "player1_id": player1_id,
            "player2_id": player2_id,
            "winner_id": winner_id,
            "points_p1": points_p1,
            "points_p2": points_p2,
            "status": status,
        }

        logger.info(f"🎯 Finalizing match {match_id}: winner={winner_id}")

        for attempt in range(1, MAX_RETRY_ATTEMPTS + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        endpoint,
                        json=payload
                    )

                    if response.status_code == 200:
                        logger.info(f"✅ Match {match_id} finalized successfully")
                        return True
                    else:
                        logger.warning(
                            f"⚠️ Match {match_id} finalize failed with status {response.status_code} "
                            f"(attempt {attempt}/{MAX_RETRY_ATTEMPTS})"
                        )

            except httpx.TimeoutException:
                logger.warning(
                    f"⏱️ Match {match_id} finalize timeout "
                    f"(attempt {attempt}/{MAX_RETRY_ATTEMPTS})"
                )

            except httpx.ConnectError as e:
                logger.warning(
                    f"🔌 Match {match_id} finalize connection error "
                    f"(attempt {attempt}/{MAX_RETRY_ATTEMPTS}): {e}"
                )

            except Exception as e:
                logger.error(
                    f"❌ Match {match_id} finalize unexpected error "
                    f"(attempt {attempt}/{MAX_RETRY_ATTEMPTS}): {e}"
                )

            # Exponential backoff between retries
            if attempt < MAX_RETRY_ATTEMPTS:
                wait_time = min(RETRY_BACKOFF_BASE ** attempt, MAX_RETRY_WAIT)
                logger.info(f"⏳ Waiting {wait_time}s before retry...")
                await asyncio.sleep(wait_time)

        logger.error(
            f"❌ Failed to finalize match {match_id} after {MAX_RETRY_ATTEMPTS} attempts. "
            f"Match result may not be reflected in player stats!"
        )
        return False

    async def get_player(self, player_id: str) -> Optional[Dict[str, Any]]:
        """
        Get player information from player service.

        Args:
            player_id: Player username

        Returns:
            dict: Player information or None if not found
        """
        endpoint = f"{self.base_url}{PLAYER_ENDPOINTS['get_player']}".format(player_id=player_id)

        logger.debug(f"👤 Fetching player info for {player_id}")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(endpoint)

                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    logger.warning(f"⚠️ Player {player_id} not found")
                    return None
                else:
                    logger.error(f"❌ Failed to fetch player {player_id}: {response.status_code}")
                    return None

        except Exception as e:
            logger.error(f"❌ Error fetching player {player_id}: {e}")
            return None


# Global client instance
player_client = PlayerClient()

