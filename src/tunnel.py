"""Cloudflare tunnel manager for exposing the local webhook server to Twilio."""
import subprocess
import threading
import time
import re
from typing import Optional

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class TunnelManager:
    """Manages a Cloudflare (cloudflared) tunnel to expose the local webhook server."""

    def __init__(self, port: int = 5000):
        """Initialize the tunnel manager.

        Args:
            port: Local port the Flask server is running on
        """
        self.port = port
        self.public_url: Optional[str] = None
        self._process: Optional[subprocess.Popen] = None

    def start(self) -> str:
        """Start the cloudflared tunnel and return the public URL.

        Returns:
            Public HTTPS URL

        Raises:
            RuntimeError: If tunnel cannot be started or URL not found
        """
        try:
            from pycloudflared import try_cloudflare
        except ImportError:
            raise RuntimeError(
                "pycloudflared is not installed. Run: pip install pycloudflared"
            )

        logger.info(f"Starting Cloudflare tunnel on port {self.port}...")
        try:
            result = try_cloudflare(self.port, verbose=False)
            self.public_url = result.tunnel
            logger.info(f"Cloudflare tunnel active: {self.public_url}")
            return self.public_url
        except Exception as e:
            raise RuntimeError(f"Failed to start Cloudflare tunnel: {e}")

    def stop(self) -> None:
        """Stop the Cloudflare tunnel."""
        try:
            from pycloudflared import try_cloudflare
            try_cloudflare.terminate(self.port)
            logger.info("Cloudflare tunnel stopped")
        except Exception as e:
            logger.warning(f"Error stopping tunnel: {e}")
        finally:
            self.public_url = None
