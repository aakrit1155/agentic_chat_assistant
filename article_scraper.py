import re  # Import the re module for regular expressions
import time
import urllib.robotparser
from typing import Tuple
from urllib.parse import urljoin, urlparse

import requests
import tiktoken
from bs4 import BeautifulSoup
from langchain.tools import tool

TOOL_MSG_PREFIX = "TOOL OUTPUT: "
# Define a user agent string
USER_AGENT = "MyArticleScraperSummaryGenerator/1.0"

TOKEN_LIMIT = 600


def tokenize_and_truncate_text(article_text: str) -> str:
    #  Tokenize and Truncate ---
    try:
        # Using cl100k_base encoding (common for many OpenAI models)
        encoding = tiktoken.get_encoding("cl100k_base")
        tokens = encoding.encode(article_text)

        if len(tokens) > TOKEN_LIMIT:
            truncated_tokens = tokens[:TOKEN_LIMIT]
            truncated_text = encoding.decode(truncated_tokens)
            # Ensure truncation doesn't cut mid-word awkwardly at the very end
            # This is a simple heuristic, might still cut mid-sentence.
            if len(truncated_text) < len(
                article_text
            ):  # Only add ellipsis if truncated
                # Try to end on a word boundary if possible (simple method)
                if truncated_text[-1].isalnum():
                    truncated_text = truncated_text.rsplit(" ", 1)[0] + "..."
                else:
                    truncated_text += "..."

            return truncated_text
        else:
            # Return the full text if it's 600 tokens or less
            return article_text

    except Exception as e:
        return f"Error: Failed to tokenize text. Details: {e}"


def parse_url(url: str) -> Tuple[str, str]:
    if not url.startswith("http"):
        raise ValueError("Error: Invalid URL format. Must start with http or https.")

    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    robots_url = urljoin(base_url, "/robots.txt")
    return parsed_url, robots_url


def check_robots_txt(robots_url: str, user_agent: str, scrape_url: str) -> bool:
    """
    Check if the given user agent is allowed to scrape the URL based on robots.txt.
    """
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(robots_url)
    rp.read()
    return rp.can_fetch(user_agent, scrape_url)


def fetch_page_content(url: str) -> bytes:
    headers = {"User-Agent": USER_AGENT}
    # Add a timeout to the main request
    response = requests.get(
        url, headers=headers, timeout=15
    )  # Increased timeout slightly
    response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
    return response.content


def parse_and_extract(content: bytes) -> str:
    soup = BeautifulSoup(content, "html.parser")

    # --- Improved Text Extraction Strategy ---

    # Define common class name patterns for main content areas
    # Add or remove patterns based on common observations
    potential_content_patterns = [
        "article",
        "post",
        "content",
        "body",
        "text",
        "story",
        "review",
        "main",
    ]
    # Create a regex pattern to match any class containing these patterns (case-insensitive)
    class_regex = re.compile(
        r".*(?:" + "|".join(potential_content_patterns) + ").*", re.IGNORECASE
    )

    # Look for common container tags (div, article, main, section) that have a class matching the pattern
    relevant_containers = soup.find_all(
        ["div", "article", "main", "section"], class_=class_regex
    )

    article_text = ""

    # If we found potential containers with relevant classes
    if relevant_containers:
        # Iterate through potential containers and try to extract text, prioritizing paragraphs
        for container in relevant_containers:
            # Try to find paragraphs within this container first
            text_elements = container.find_all("p")
            if text_elements:
                # Join text from paragraphs
                current_text = " ".join([p.get_text(strip=True) for p in text_elements])
                if current_text:
                    article_text = (
                        article_text + " " + current_text
                    )  # Use the text found in paragraphs
                    break  # Stop searching containers if we found paragraph text

            # If no paragraphs within this container, get all text from the container
            if (
                not article_text
            ):  # Only do this if paragraph extraction failed for *any* container so far
                container_text = container.get_text(separator=" ", strip=True)
                # Keep the longest text found among containers if paragraph extraction failed
                if len(container_text) > len(article_text):
                    article_text = article_text + " CONTAINER_TEXT: " + container_text

    # Fallback 1: If no relevant containers found or they didn't yield text, try finding all paragraphs in the body
    if not article_text:
        body = soup.find("body")
        if body:
            text_elements = body.find_all("p")
            if text_elements:
                article_text = " ".join([p.get_text(strip=True) for p in text_elements])

    # Fallback 2: Get all text from the body if still no text found
    if not article_text:
        body = soup.find("body")
        if body:
            article_text = body.get_text(separator=" ", strip=True)

    # If still no text, return an error
    if not article_text:
        raise ValueError(
            "Error: Could not extract any meaningful text from using common patterns."
        )

    # Clean up excessive whitespace
    article_text = " ".join(article_text.split())
    return article_text


@tool
def scrape_article(url: str) -> str:
    """
    Fetches content from a given URL, checks robots.txt, parses the page
    to extract main text based on common class/tag patterns, and returns
    the first 600 tokens.

    Args:
        url: The URL of the article page to scrape.

    Returns:
        A string containing the first 600 tokens of the extracted article text,
        or an informative error message if fetching, parsing, or robots.txt check fails.
    """

    # parse the URL and get the parsed url
    try:
        parsed_url, robots_url = parse_url(url)
    except Exception as e:
        return TOOL_MSG_PREFIX + str(e)

    # check the robots.txt whether scraping is allowed
    try:
        scraping_allowed = check_robots_txt(
            robots_url=robots_url, user_agent=USER_AGENT, scrape_url=parsed_url.path
        )
        if not scraping_allowed:
            return (
                TOOL_MSG_PREFIX
                + f"Error: Scraping is disallowed by robots.txt for {url} for user agent {USER_AGENT}."
            )
    except Exception as e:
        return TOOL_MSG_PREFIX + f"Error: Failed to check robots.txt. Details: {e}"

    # Fetch the Page Content ---
    try:
        content = fetch_page_content(url)
    except requests.exceptions.RequestException as e:
        return TOOL_MSG_PREFIX + f"Error: Failed to fetch page {url}. Details: {e}"

    # --- 3. Parse HTML and Extract Text ---
    try:
        text = parse_and_extract(content=content)
    except Exception as e:
        return (
            TOOL_MSG_PREFIX
            + f"Error: Failed to parse HTML or extract text from {url}. Details: {e}"
        )

    # Tokenize and truncate the text to 600 tokens
    try:
        truncated_text = tokenize_and_truncate_text(text)
    except Exception as e:
        return (
            TOOL_MSG_PREFIX
            + f"Error: Failed to tokenize or truncate text. Details: {e}"
        )

    return TOOL_MSG_PREFIX + f"SCRAPED TEXT:: {truncated_text}"


# Example Usage (for testing the tool independently)
if __name__ == "__main__":
    # Example URL (replace with a real URL for testing)
    # Make sure to test with a site that allows scraping and one that doesn't if possible
    test_url_allowed = "https://edition.cnn.com/2025/05/14/business/de-minimis-tariff-china-trump"  # Example allowed
    test_url_disallowed = (
        "https://www.amazon.com/gp/bestsellers/"  # Example often disallowed
    )
    test_url_invalid = "https://invalid-url.com"

    print(f"--- Testing Valid URL: {test_url_allowed} ---")
    result_allowed = scrape_article(test_url_allowed)
    print("Result (first 600 tokens):\n")
    print(result_allowed)
    print("-" * 30)

    time.sleep(2)
    print(f"\n--- Testing Disallowed URL: {test_url_disallowed} ---")
    result_disallowed = scrape_article(test_url_disallowed)
    print("Result:\n")
    print(result_disallowed)
    print("-" * 30)

    time.sleep(2)
    print(f"\n--- Testing Invalid URL: {test_url_invalid} ---")
    result_invalid = scrape_article(test_url_invalid)
    print("Result:\n")
    print(result_invalid)
    print("-" * 30)
