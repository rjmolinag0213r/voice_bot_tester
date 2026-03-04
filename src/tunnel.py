"""ngrok tunnel manager for exposing the local webhook server to Twilio."""
import time
from typing import Optional

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class TunnelManager:
    """Manages an ngrok tunnel to expose the local webhook server."""

    def __init__(self, port: int = 5000):
        """Initialize the tunnel manager.

        Args:
            port: Local port the Flask server is running on
        """
        self.port = port
        self.public_url: Optional[str] = None
        self._tunnel = None

    def start(self) -> str:
        """Start the ngrok tunnel and return the public URL.

        Returns:
            Public HTTPS URL

        Raises:
            RuntimeError: If tunnel cannot be started
        """
        try:
            from pyngrok import ngrok, conf

            # Kill any existing tunnels to avoid conflicts
            ngrok.kill()
            time.sleep(1)

            logger.info(f"Starting ngrok tunnel on port {self.port}...")
            self._tunnel = ngrok.connect(self.port, "http")
            self.public_url = self._tunnel.public_url

            # Prefer HTTPS
            if self.public_url.startswith("http://"):
                self.public_url = self.public_url.replace("http://", "https://", 1)

            logger.info(f"Tunnel active: {self.public_url}")
            return self.public_url

        except ImportError:
            raise RuntimeError(
                "pyngrok is not installed. Run: pip install pyngrok"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to start ngrok tunnel: {e}")

    def stop(self) -> None:
        """Stop the ngrok tunnel."""
        try:
            from pyngrok import ngrok
            ngrok.kill()
            logger.info("ngrok tunnel stopped")
        except Exception as e:
            logger.warning(f"Error stopping tunnel: {e}")
        finally:
            self.public_url = None
            self._tunnel = None
