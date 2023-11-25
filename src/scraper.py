import itertools
import random
import time
from typing import Any, Callable, Iterable, List, Optional

from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.common.exceptions import (
    InvalidSessionIdException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.support.ui import WebDriverWait

from config import SELENOID_COMMAND_EXECUTOR

_USER_AGENTS: List[str] = [
    # Firefox/115.0
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7; rv:115.0) Gecko/20000101 Firefox/115.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13.5; rv:109.0) Gecko/20100101 Firefox/115.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_11_2; rv:115.0) Gecko/20100101 Firefox/115.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_11_6; rv:115.0) Gecko/20010101 Firefox/115.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_14; rv:115.0) Gecko/20010101 Firefox/115.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_5_2; rv:115.0) Gecko/20100101 Firefox/115.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2; rv:115.0) Gecko/20110101 Firefox/115.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7; rv:115.0) Gecko/20000101 Firefox/115.0",
]


class SelenoidWebScraper:
    def __init__(
        self,
        user_agents: List[str] = _USER_AGENTS,
        command_executor: str = SELENOID_COMMAND_EXECUTOR,
    ) -> None:
        """
        Start the browser driver and request session.
        Initializes the web driver instance for the scraper.
        """

        self.USER_AGENTS = user_agents
        self.command_executor = command_executor

    def _create_firefox_driver(self) -> webdriver.Remote:
        """
        Creates an instance of the Firefox web driver with the specified settings.

        :return: Returns an instance of the remote Firefox web driver.
        """

        firefox_options = webdriver.FirefoxOptions()

        # Basic options for headless browsing
        firefox_options.add_argument("--headless")
        firefox_options.add_argument("--no-sandbox")
        firefox_options.add_argument("--disable-dev-shm-usage")
        firefox_options.add_argument("--disable-gpu")
        firefox_options.add_argument("--disable-blink-features=AutomationControlled")

        # Ensure JavaScript is enabled
        firefox_options.set_preference("javascript.enabled", True)

        # Masking to imitate real user behavior
        firefox_options.set_preference("dom.webdriver.enabled", False)
        user_agent = self.get_random_user_agent()
        firefox_options.set_preference("general.useragent.override", user_agent)

        # Reduce delays during page loads
        firefox_options.set_preference("permissions.default.image", 2)
        firefox_options.set_preference(
            "dom.ipc.plugins.enabled.libflashplayer.so", False
        )

        # Disable web notifications
        firefox_options.set_preference("dom.webnotifications.enabled", False)

        # Disable media
        firefox_options.set_preference("media.volume_scale", "0.0")

        # Disable auto-updates
        firefox_options.set_preference("app.update.auto", False)
        firefox_options.set_preference("app.update.enabled", False)

        capabilities = {
            "browserName": "firefox",
        }
        firefox_options.to_capabilities().update(capabilities)

        return webdriver.Remote(
            command_executor=self.command_executor, options=firefox_options
        )

    @staticmethod
    def _imitate_user_behavior(driver: webdriver.Remote) -> None:
        """
        Imitate real user behavior to avoid bot detection.

        :param driver: Selenoid Web driver
        """

        # This is just a template. You can extend this method with more complex logic.
        actions = [
            lambda: driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);"
            ),
            lambda: driver.execute_script(
                "window.scrollTo(document.body.scrollHeight, 0);"
            ),
            # Add more actions here
        ]

        for action in random.sample(actions, len(actions)):
            action()
            time.sleep(random.uniform(0.5, 2.5))

    def _safe_get(self, driver, method: Callable[..., Any], *args, **kwargs) -> bool:
        """
        Safely execute a function or method, catching specific Selenium exceptions.

        :param driver: Current instance of the web driver.
        :param method: The function or method to execute.
        :param args: Positional arguments to pass to the action.
        :param kwargs: Keyword arguments to pass to the action.
        :return: The result of the executed action, or None if an exception occurs.
        """
        retries = 0
        last_exception = None

        while retries < 3:
            try:
                method(*args, **kwargs)
                return True

            except (
                TimeoutException,
                WebDriverException,
                InvalidSessionIdException,
            ) as ex:
                retries += 1
                last_exception = ex

                if retries < 3:
                    self.stop(driver)  # Close the current driver
                    driver = self.start()  # Start a new driver

        print(f"Max retries reached. Last error in _safe_get: {last_exception}")
        return False

    def start(self) -> webdriver.Remote:
        """
        Start the browser driver.
        Initializes the web driver instance for the scraper.
        """
        driver = self._create_firefox_driver()

        driver.set_page_load_timeout(20)

        driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        self._imitate_user_behavior(driver=driver)
        return driver

    @staticmethod
    def stop(driver: webdriver.Remote) -> None:
        """
        Stop the browser driver and session connection.
        Closes the web driver instance and cleans up.

        :param driver: Selenoid Web driver.
        """
        try:
            driver.quit()
        except (WebDriverException, InvalidSessionIdException):
            print("Browser session was not found. It might have been closed already.")

    def _fetch_url(self, url: str) -> Optional[str]:
        """
        Fetch the source content of the given URL using a Firefox web driver.

        :param url: The URL to be fetched.
        :return: The page source if fetched successfully, else None.
        """
        driver = self.start()

        try:
            if not self._safe_get(driver, driver.get, url):
                return "This site is not responding."

            WebDriverWait(driver, 10).until(
                lambda x: x.execute_script("return document.readyState") == "complete"
            )
            return driver.page_source

        except TimeoutException as e:
            print(
                f"TimeoutException in WebDriverWait, web site not loaded full: {url}: {e}"
            )
            return "This site is not responding."

        except WebDriverException as e:
            print(f"Error fetching page source from {url}: {e}")
            return None

        finally:
            self.stop(driver)

    def get_random_user_agent(self) -> str:
        """
        Return a randomly selected user agent.
        """
        return random.choice(self.USER_AGENTS)

    @staticmethod
    def _extract_text_from_paragraphs(paragraphs: Iterable[Tag]) -> str:
        """
        Extract and join the text from a list of paragraph elements.

        :param paragraphs: Iterable of paragraph elements.
        :return: Extracted text combined into a single string.
        """
        return "\n".join(p.get_text().strip() for p in paragraphs)

    @staticmethod
    def _remove_unwanted_elements(soup: BeautifulSoup) -> None:
        """
        Remove elements that are likely advertisements, cookie notifications, or specific tags.

        :param soup: BeautifulSoup object containing the HTML content.
        """
        unwanted_patterns = {
            "ads",
            "advertisement",
            "cookie",
            "cookies",
            "cookie-banner",
            "branda-cookie-notice",
            "banner",
            "widget",
            "notice",
            "cookie-notice",
            "footer",
            "subs",
            "header",
            "sidemenu",
            "sidebar",
            "bar",
            "menu",
            "navbar",
            "nav",
            "navigation",
            "tracker",
            "tracking",
            "promo",
            "promotion",
            "sponsor",
            "sponsored",
            "ad-slot",
            "ad-wrapper",
            "ad-container",
            "adbox",
            "popup",
            "pop-up",
            "social",
            "share",
            "sharing",
            "comments",
            "disqus",
            "fb",
            "twitter",
            "instagram",
            "widgetbox",
            "login",
            "signup",
            "subscribe",
            "related",
            "gallery",
            "breadcrumb",
            "bottom",
            "label",
            "modal-content",
        }

        direct_tags_to_remove = {
            "header",
            "footer",
            "nav",
            "script",
            "style",
            "form",
            "button",
            "iframe",
        }

        for tag in direct_tags_to_remove:
            for element in soup.find_all(tag):
                element.decompose()

        for pattern in unwanted_patterns:
            for attr in ["class", "id"]:
                for element in soup.find_all(True, {attr: pattern}):
                    element.decompose()

    def _extract_paragraphs(self, page_source: Optional[str]) -> Optional[str]:
        """
        Extract paragraphs from the provided page source.

        This function attempts to extract paragraphs from a given page source. It
        uses BeautifulSoup to parse the page source and then searches for paragraphs
        using `p` and `span` tags.

        :param page_source: The HTML content of a page.
        :return: Extracted paragraphs joined into a single string, or None if no paragraphs were extracted.
        """
        if not page_source:
            return None

        soup = BeautifulSoup(page_source, "lxml")
        body = soup.body

        if body:
            self._remove_unwanted_elements(body)

            all_elements = itertools.chain(body.select("p"), body.select("span"))
            text = self._extract_text_from_paragraphs(all_elements).strip()

            if len(text) < 1000:
                text = body.get_text().strip()

            return text

        return None

    def scrape(self, url: str) -> Optional[str]:
        """
         A worker function to scrape content from a given URL and save the result in the specified folder.

        The function performs the following steps:
         1. Fetch the content of the URL.
         2. Extract relevant paragraphs from the fetched content.

         :param url: The target URL to be scraped.
         :return: Extracted content from the given URL, or None if extraction was unsuccessful.
        """

        page_source = self._fetch_url(url)

        if page_source == "This site is not responding.":
            return page_source

        text_from_paragraphs = self._extract_paragraphs(page_source)

        if text_from_paragraphs:
            content_length = len(text_from_paragraphs)
            print(f"Content-Length: {content_length}")

            if content_length < 1000:
                print(f"Content-Length less than 1000 symbols.")
                return "This result doesn`t contain relevant information."

            print(f"Page source with text fetched SUCCESS: {url}")
            return text_from_paragraphs

        print(f"Body source text is None: {url}")
        return None
