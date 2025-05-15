# Agentic Chat Assistant

## Project Overview

This project showcases an agentic workflow of Large Language Models (LLMs) to create an automated news article fetching system using an ethical web scraper. It leverages agent tools to gather and process information efficiently.

## Setup Instructions

1.  **Create a virtual environment:**

    ```bash
    python -m venv venv
    ```
2.  **Activate the virtual environment:**

    *   On Windows:

        ```bash
        .\venv\Scripts\activate
        ```
    *   On macOS and Linux:

        ```bash
        source venv/bin/activate
        ```
3.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

## Project Details

The Agentic Chat Assistant demonstrates how LLMs can be used to automate tasks through intelligent agents. The core component is an ethical web scraper that fetches news articles based on predefined criteria. This scraper is designed to respect website terms of service and avoid overloading servers.

The agentic workflow involves the following steps:

1.  **Task Definition:** The user defines the type of news articles to fetch.
2.  **Web Scraping:** The agent uses the ethical web scraper to find relevant articles.
3.  **Data Extraction:** The agent extracts key information from the articles, such as title, content, and publication date.
4.  **Data Processing:** The agent processes the extracted data and presents it in a structured format.

## Ethical Web Scraper

The ethical web scraper is designed with the following principles in mind:

*   **Respect `robots.txt`:** The scraper adheres to the rules defined in the `robots.txt` file of each website.
*   **Rate Limiting:** The scraper includes rate limiting to avoid overloading servers with requests.
*   **User-Agent:** The scraper uses a descriptive User-Agent string to identify itself.

## Key Frameworks Used

*   **Langchain:** Used for building the agentic workflow and managing interactions with LLMs.
*   **Beautiful Soup:** Used for parsing HTML content in the web scraper.
*   **Requests:** Used for making HTTP requests to fetch web pages.
*   **Python:** The primary programming language.
