import re
from asyncio import run as run_async
from typing import Optional, Type

from bs4 import BeautifulSoup
from langchain_core.callbacks.manager import AsyncCallbackManagerForToolRun
from langchain_core.tools import BaseTool
from playwright.async_api import BrowserContext, Page, async_playwright
from pydantic import BaseModel, Field

from common.constants import NDTL_WEB_BROWSER

user_agent: str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
element_tags_to_remove: list[str] = [
    "head", "header", "footer", "nav", "sidebar", "menu", "img", "object", "svg", "iframe"
]

# Update uBlock Origin Lite: https://github.com/uBlockOrigin/uBOL-home/releases

class WebBrowserInput(BaseModel):
    url: str = Field(description="URL of the website")

class WebBrowserTool(BaseTool):
    name: str = NDTL_WEB_BROWSER
    description: str = "Gets the contents of a website"
    args_schema: Type[BaseModel] = WebBrowserInput
    return_direct: bool = False

    def _run(
        self,
        url: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> str:
        return run_async(self._arun(url, run_manager))

    async def _arun(
        self,
        url: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> str:
        try:
            # 1. ページを開き、HTML を取得
            page_html: str | None = None
            async with async_playwright() as p:
                browser_context: BrowserContext = await p.chromium.launch_persistent_context(
                    user_data_dir="./.chromium/",
                    args=[
                        "--password-store=basic",
                        "--disable-extensions-except=./common/tools/chromium_extensions/ubolite",
                        "--load-extension=./common/tools/chromium_extensions/ubolite"
                    ],
                    headless=True,
                    user_agent=user_agent
                )
                page: Page = browser_context.pages[0]
                print(f"[WBTOOL] Opening '{url}'...")
                await page.goto(url)
                await page.wait_for_load_state("load")
                page_html = await page.content()
                await browser_context.close()

            # 2. HTML を処理して、検索結果を抽出
            if page_html:
                print("[WBTOOL] Extracting text from webpage...")
                soup: BeautifulSoup = BeautifulSoup(page_html, "html.parser")
                try:
                    for element_tag in element_tags_to_remove:
                        if element := soup.find(element_tag):
                            element.decompose()
                except Exception:
                    pass
                page_text = soup.get_text()
                print("[WBTOOL] Cleaning up text...")
                page_text = page_text.strip()
                page_text = re.sub(r"\n+", "\n", page_text)
                page_text = re.sub(r" {2,}", " ", page_text)
                return page_text
            else:
                raise RuntimeError("Failed to fetch page HTML.")
        except Exception:
            return ""


if __name__ == "__main__":
    tool: WebBrowserTool = WebBrowserTool()
    urls_to_test: list[str] = [
        "https://myip.wtf/",
        "https://whatsmyua.info/"
    ]
    for url in urls_to_test:
        page_contents: str = tool.invoke({
            "url": url
        })
        print(page_contents)
