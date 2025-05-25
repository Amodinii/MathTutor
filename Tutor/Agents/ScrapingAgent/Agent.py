import sys
from typing import TypedDict, Dict, Optional, List, Any
from langgraph.graph import StateGraph, END
from Tutor.MCPClients.WebScrape import WebScrapeClient
from Tutor.Services.ScrapeLLM import ScrapeLLM
from Tutor.Logging.Logger import logger
from Tutor.Exception.Exception import TutorException

# Define state for the scraping agent
class ScraperState(TypedDict):
    input_data: Dict[str, Any]
    url_dict: Optional[Dict[str, str]]
    scraper_client: Optional[Any]
    llm: Optional[Any]
    raw_pages: Optional[Dict[str, str]]
    extracted: Optional[List[Dict[str, Any]]]

#1. Extract URLs from input_data
async def extract_urls_from_data(state: ScraperState) -> ScraperState:
    try:
        input_data = state.get("input_data", {})
        if not input_data:
            raise TutorException("No input data provided for URL extraction", sys)
        urls = []
        url_dict = {}        
        results = input_data.get("results", [])
        if results:
            page_name = input_data.get("page_name", "page")
            for i, result in enumerate(results):
                url = result.get("url")
                if url:
                    urls.append(url)
                    name = f"{page_name} #{i+1}"
                    url_dict[name] = url

        if not urls:
            raise TutorException("No valid URLs found in input data", sys)

        logger.info(f"[Scraping Agent] Extracted {len(urls)} URLs from input data.")
        logger.info(f"[Scraping Agent] URL dictionary: {url_dict}")
        state["url_dict"] = url_dict
        return state

    except Exception as e:
        logger.error(f"[Scraping Agent] Error extracting URLs from data: {e}")
        raise TutorException(e, sys)

#2. Scrape the URLs using the WebScrape MCP client
async def scrape_urls(state: ScraperState) -> ScraperState:
    try:
        urls = state.get("url_dict", {})
        if not urls:
            raise TutorException("No URLs provided to scraping agent", sys)

        scraper = state.get("scraper_client")
        if not scraper:
            raise TutorException("No scraper client provided", sys)

        logger.info(f"[Scraping Agent] Scraping {len(urls)} URLs.")
        results = {}
        for name, url in urls.items():
            try:
                html = await scraper.scrape(url)
                results[name] = html
            except Exception as e:
                logger.warning(f"[Scraping Agent] Failed to scrape {url} ({name}): {e}")
                continue
        state["raw_pages"] = results
        logger.info("[Scraping Agent] Scraping completed.")
        return state

    except Exception as e:
        logger.error(f"[Scraping Agent] Error scraping URLs: {e}")
        raise TutorException(e, sys)

#3. Extract structured questions using the LLM
async def extract_questions(state: ScraperState) -> ScraperState:
    try:
        raw_pages = state.get("raw_pages", {})
        model = state.get("llm")
        if not model:
            raise TutorException("No LLM model provided for extraction", sys)

        logger.info(f"[Scraping Agent] Extracting questions from {len(raw_pages)} pages.")
        results = []
        for name, html in raw_pages.items():
            try:
                extracted = await model.extract(document=html)
                results.append(extracted)
            except Exception as e:
                logger.warning(f"[Scraping Agent] Skipping document '{name}' due to error: {e}")
                continue
        state["extracted"] = results
        return state

    except Exception as e:
        logger.error(f"[Scraping Agent] Error extracting from HTML: {e}")
        raise TutorException(e, sys)

#4. Agent definition using LangGraph
class ScrapingAgent:
    def __init__(self, model_name="llama3-8b-8192"):
        self.llm = ScrapeLLM(model_name=model_name)
        self.model_name = model_name

        workflow = StateGraph(ScraperState)
        workflow.add_node("extract_urls", extract_urls_from_data)
        workflow.add_node("scrape", scrape_urls)
        workflow.add_node("extract", extract_questions)

        workflow.set_entry_point("extract_urls")
        workflow.add_edge("extract_urls", "scrape")
        workflow.add_edge("scrape", "extract")
        workflow.add_edge("extract", END)

        self.app = workflow.compile()
        logger.info("[Scraping Agent] Initialized.")

    async def run(self, input_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        if not input_data:
            raise TutorException("Input data is empty.", sys)

        scraper_client = WebScrapeClient()
        await scraper_client.connect()

        try:
            state = ScraperState(
                input_data=input_data,
                url_dict=None,
                scraper_client=scraper_client,
                llm=self.llm,
                raw_pages=None,
                extracted=None,
            )
            logger.info(f"[Scraping Agent] Running on input with {len(input_data)} entries.")
            result = await self.app.ainvoke(state)
            return result.get("extracted", [])
        except Exception as e:
            logger.error(f"[Scraping Agent] Error running agent: {e}")
            raise TutorException(e, sys)
        finally:
            logger.info("[Scraping Agent] Closing scraper client.")
            await scraper_client.close()

#5. Builder for external use 
async def build_scraping_agent(model_name="llama3-8b-8192"):
    try:
        agent = ScrapingAgent(model_name)

        async def run_scraper(input_data: Dict[str, Any]):
            return await agent.run(input_data)

        return run_scraper
    except Exception as e:
        raise TutorException(e, sys)