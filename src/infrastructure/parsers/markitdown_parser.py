import logging
from markitdown import MarkItDown

logger = logging.getLogger(__name__)

class MarkItDownParser:
    """Wrapper for Microsoft MarkItDown tool to convert URLs and files to Markdown."""
    
    def __init__(self):
        self._md = MarkItDown()
        
    async def convert_url(self, url: str) -> str:
        """Fetch a URL and convert its contents to Markdown.
        
        Note: Since markitdown uses synchronous requests/processing,
        we could run this in a thread if it blocks, but for now we'll 
        just run it directly or wrap it.
        """
        import asyncio
        try:
            logger.info(f"[MarkItDownParser] Converting URL to Markdown: {url}")
            # Run in a thread to prevent blocking the async event loop
            result = await asyncio.to_thread(self._md.convert, url)
            return result.text_content
        except Exception as e:
            logger.error(f"[MarkItDownParser] Failed to convert URL {url}: {e}")
            raise

    async def convert_file(self, file_path: str) -> str:
        """Convert a local file (PDF, DOCX, XLSX, HTML, etc) to Markdown."""
        import asyncio
        try:
            logger.info(f"[MarkItDownParser] Converting File to Markdown: {file_path}")
            result = await asyncio.to_thread(self._md.convert, file_path)
            return result.text_content
        except Exception as e:
            logger.error(f"[MarkItDownParser] Failed to convert file {file_path}: {e}")
            raise
