import re

from ._abstract import AbstractScraper
from ._utils import get_minutes


class HelloFresh(AbstractScraper):
    @classmethod
    def host(cls, domain="com"):
        return f"hellofresh.{domain}"

    def cook_time(self):
        script_tag = self.soup.find("script", {"id": "__NEXT_DATA__"})
        if script_tag:
            script_content = script_tag.string
            total_time_match = re.search(r'"totalTime":"(PT\d+[M|H])"', script_content)
            if total_time_match:
                total_time_str = total_time_match.group(1)
                return get_minutes(total_time_str)

    def prep_time(self):
        script_tag = self.soup.find("script", {"id": "__NEXT_DATA__"})
        if script_tag:
            script_content = script_tag.string
            total_time_match = re.search(r'"totalTime":"(PT\d+[M|H])"', script_content)
            if total_time_match:
                total_time_str = total_time_match.group(1)
                return get_minutes(total_time_str)

    def total_time(self):
        script_tag = self.soup.find("script", {"id": "__NEXT_DATA__"})
        if script_tag:
            script_content = script_tag.string
            prep_time_match = re.search(r'"prepTime":"(PT\d+[M|H])"', script_content)
            if prep_time_match:
                prep_time_str = prep_time_match.group(1)
                return get_minutes(prep_time_str)
