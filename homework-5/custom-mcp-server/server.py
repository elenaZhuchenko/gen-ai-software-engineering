"""Custom MCP server built with FastMCP.

Exposes lorem ipsum text from lorem-ipsum.md as both a Resource (read via URI)
and a Tool (callable by the AI agent).

Resources vs Tools
------------------
- **Resources** are URI-addressable data sources that the AI client can *read*
  (similar to GET endpoints). They are identified by a URI scheme and are best
  suited for providing context, files, or structured data.
- **Tools** are functions the AI agent can *call* to perform an action and receive
  a result. They accept arguments and return a response, making them suitable for
  dynamic, parameterized operations like reading a configurable number of words.
"""

from pathlib import Path

from fastmcp import FastMCP

mcp = FastMCP("lorem-ipsum-server")

_LOREM_PATH = Path(__file__).parent / "lorem-ipsum.md"


def _load_words(word_count: int) -> str:
    """Return the first *word_count* words from lorem-ipsum.md.

    Clamps out-of-range values instead of relying on raw slice semantics,
    since a negative word_count would otherwise return "all but the last
    N words" rather than an empty/short result.
    """
    text = _LOREM_PATH.read_text(encoding="utf-8")
    words = text.split()
    count = max(0, min(word_count, len(words)))
    return " ".join(words[:count])


@mcp.resource("lorem://text")
def lorem_default() -> str:
    """Return the first 30 words of lorem ipsum text."""
    return _load_words(30)


@mcp.resource("lorem://text/{word_count}")
def lorem_by_count(word_count: str) -> str:
    """Return exactly word_count words of lorem ipsum text.

    Args:
        word_count: Number of words to return (passed as URI path segment).
    """
    try:
        count = int(word_count)
    except ValueError:
        count = 30
    return _load_words(count)


@mcp.tool()
def read(word_count: int = 30) -> str:
    """Read lorem ipsum content from lorem-ipsum.md.

    Args:
        word_count: Number of words to return. Defaults to 30.

    Returns:
        A string containing exactly *word_count* words from the lorem ipsum source.
    """
    return _load_words(word_count)


if __name__ == "__main__":
    mcp.run()
