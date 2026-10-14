"""Evidence retrieval from URLs and text sources."""
import httpx
from bs4 import BeautifulSoup
from typing import Optional
import re
import ipaddress
from urllib.parse import urlparse


class EvidenceRetriever:
    """Retrieves evidence from URLs and processes text sources."""

    def __init__(self, timeout: int = 30):
        """Initialize the retriever with HTTP client."""
        self.timeout = timeout
        self.client = httpx.Client(timeout=timeout)

    def fetch_url(self, url: str) -> Optional[str]:
        """
        Fetch and extract text content from a URL.

        Args:
            url: The URL to fetch

        Returns:
            Extracted text content, or None if fetch fails
        """
        try:
            # Validate URL format
            if not self._is_valid_url(url):
                return None

            response = self.client.get(url, follow_redirects=True)
            response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()

            # Extract text
            text = soup.get_text()

            # Clean up text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)

            # Limit length
            if len(text) > 10000:
                text = text[:10000]

            return text

        except httpx.TimeoutException:
            return None
        except httpx.HTTPError:
            return None
        except Exception:
            return None

    def _is_valid_url(self, url: str) -> bool:
        """
        Validate URL format and check for SSRF risks.

        Blocks:
        - localhost and local addresses
        - private IP ranges (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
        - link-local addresses (169.254.0.0/16)
        - loopback addresses (127.0.0.0/8)

        Args:
            url: The URL to validate

        Returns:
            True if URL is safe, False otherwise
        """
        # Basic format validation
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        if not url_pattern.match(url):
            return False

        # Block localhost
        if 'localhost' in url.lower():
            return False

        # Extract hostname from URL
        parsed = urlparse(url)
        hostname = parsed.hostname or parsed.netloc.split(':')[0]

        # Block private IP ranges
        try:
            ip = ipaddress.ip_address(hostname)
            if ip.is_private or ip.is_loopback or ip.is_link_local:
                return False
        except ValueError:
            # Not an IP address, continue with domain check
            pass

        # Block common internal hostnames
        blocked_hosts = ['localhost', '127.0.0.1', '0.0.0.0', '::1']
        if hostname.lower() in blocked_hosts:
            return False

        return True

    def close(self):
        """Close the HTTP client."""
        self.client.close()
