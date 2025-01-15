import json
from asyncio import run as run_async
from typing import Optional, Type
from urllib.parse import quote_plus

from bs4 import BeautifulSoup, ResultSet, Tag
from langchain_core.callbacks.manager import AsyncCallbackManagerForToolRun
from langchain_core.tools import BaseTool
from playwright.async_api import Browser, Page, async_playwright
from pydantic import BaseModel, Field

from common.constants import NDTL_GOOGLE_SEARCH


class GoogleSearchInput(BaseModel):
    query: str = Field(description="Search query")
    number_of_pages_to_fetch: int = Field(description="Number of search result pages to fetch")

class GoogleSearchTool(BaseTool):
    name: str = NDTL_GOOGLE_SEARCH
    description: str = "Searches the web using Google"
    args_schema: Type[BaseModel] = GoogleSearchInput
    return_direct: bool = False

    def _run(
        self,
        query: str,
        number_of_pages_to_fetch: int = 1,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> list[dict]:
        return run_async(self._arun(query, number_of_pages_to_fetch, run_manager))

    async def _arun(
        self,
        query: str,
        number_of_pages_to_fetch: int = 1,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> list[dict]:
        # 1. Google 検索を行い、ページの HTML を保存
        pages: list[str] = []
        async with async_playwright() as p:
            browser: Browser = await p.chromium.launch(headless=True)
            page: Page = await browser.new_page()
            search_term_encoded: str = quote_plus(query)
            print(f"[GSTOOL] Opening Google search page for '{query}'...")
            await page.goto(f"https://www.google.co.jp/search?q={search_term_encoded}")
            while len(pages) < number_of_pages_to_fetch:
                print(f"[GSTOOL] Processing page {len(pages) + 1} of {number_of_pages_to_fetch}...", end="")
                await page.wait_for_load_state("load")
                page_html: str = await page.content()
                pages.append(page_html)
                print("done.")
                if len(pages) < number_of_pages_to_fetch:
                    soup: BeautifulSoup = BeautifulSoup(page_html, "html.parser")
                    next_page_button: Tag | None = soup.find("a", id="pnnext")
                    if next_page_button:
                        print("[GSTOOL] Going to next page...")
                        await page.click("a#pnnext")
                    else:
                        print("[GSTOOL] No next page available, breaking.")
                        break
            await browser.close()

        # 2. HTML を処理して、検索結果を抽出
        print("[GSTOOL] Extracting search results...", end="")
        search_results: list[dict] = []
        for search_result_page_html in pages:
            soup: BeautifulSoup = BeautifulSoup(search_result_page_html, "html.parser")
            search_result_tags: ResultSet[Tag] = soup.find_all("div", class_="g Ww4FFb vt6azd tF2Cxc asEBEc")
            for search_result in search_result_tags:
                result_text: str = search_result.get_text(separator="\n")
                result_a_tags: ResultSet[Tag] = search_result.find_all("a")
                result_a_tag: Tag | None = result_a_tags[0] if result_a_tags else None
                result_a_href: str | list[str] | None = result_a_tag["href"] if result_a_tag else None
                result_a_href_value: str | None = result_a_href[0] if isinstance(result_a_href, list) else result_a_href
                if result_text and result_a_href_value:
                    search_results.append({
                        "text": result_text,
                        "url": result_a_href_value
                    })
        print("done.")

        return search_results


if __name__ == "__main__":
    tool: GoogleSearchTool = GoogleSearchTool()
    search_results: list[dict] = tool.invoke({
        "query": "dinosaurs",
        "number_of_pages_to_fetch": 3
    })
    print(json.dumps(search_results, indent=2, ensure_ascii=False))
