import re
from datetime import datetime
import time
import pandas as pd
from bs4 import BeautifulSoup
from urllib.request import urlopen

class ArxivParser:

    def __init__(self, channel, is_compact):
        self.channel = channel
        self.username = "arxiv_bot"
        self.timestamp = ""
        self.is_compact = is_compact
        self.base_url = "http://export.arxiv.org/api/query?search_query="

    def create_help_message(self):
        print("Creating help message")
        blocks =  [
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": "아카이브 (arxiv) 문서 검색용 앱. 카테고리, 컨퍼런스, 키워드 검색 및 일일 신규 논문 정리."
			}
		},
		{
			"type": "divider"
		},
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": "*사용 예시*"
			},
			"fields": [
				{
					"type": "mrkdwn",
					"text": "help \n compact_search tacotron 3 \n search facial cs.CV 5 \n compact_search cs.CV cs.CL CVPR"
				}
			]
		},
		{
			"type": "divider"
		},
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": """
*설명* \n\n\n해당 봇은 help, search, compact_search의 키워드로 시작되는 메세지에 반응하여,
arxiv api를 사용하여 논문 검색 결과를 채널에 포스팅합니다.
해당 봇은 매일 9:30AM에 사전에 입력된 키워드에 따라 검색된 결과를 보여줍니다.
해당 봇을 사용하실 때, *첫번째 단어를 제외한 문자 배열은 의미가 없습니다.*
\t(예시: compact_search tacotron 3 = compact_search 3 tacotron)
				"""
			}
		},
		{
			"type": "divider"
		},
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": """
*명령어*\n\n\n메세지의 첫번째 단어가 명령어가 되며, 다음의 3 단어만 인식됩니다.
*help*: 도움!
*search*: 각 논문의 모든 parameter들을 보여줍니다.
*compact_search*: 논문의 제목과 카테고리만 보여줍니다.
				"""
			}
		},
		{
			"type": "divider"
		},
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": """
*파라미터*\n\n\n메세지의 두번째 단어들부터 명령어가 됩니다.
*키워드*: 모든 영문 lowercase 단어들은 키워드로 인식되며, paper abstract 에 해당 키워드가 있는지 검색합니다.
\t이때 복수의 키워드가 있으면 AND 검색.
*컨퍼런스*: 모든 영문 uppercase 단어들은 컨퍼런스로 인식되며, paper comment에 해당 컨퍼런스가 있는지 검색합니다.
\t이때 복수의 컨퍼런스가 있으면 AND 검색.
*카테고리*: 모든 단어들 중 사이에 온점이 있으며, 그 전에 글자가 lowercase이고 이후 글자가 uppercase이면 arxiv category로 인식됩니다.
\t이때 복수의 카테고리가 있으면 OR 검색.
*숫자*: 모든 단어들 중 숫자는 검색 결과의 최대 기록수가 됩니다. 맨 첫 숫자만 사용됩니다.
				"""
			}
		},
		{
			"type": "divider"
		},
        {
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": "*향후 추가 예정*\n\n\n관심 논문 즐겨찾기 기능\nOCR"
			}
		}
	]

        return {
            "ts": self.timestamp,
            "channel": self.channel,
            "username": self.username,
            "blocks": blocks,
        }

    def parse_from_arxiv(self, search_categories, search_keywords, search_conferences):
        self.parse_url = self.base_url
        self.parse_url += ("%28" + "+OR+".join(["cat:" + x for x in search_categories]) + "%29")
        if len(search_keywords) > 0:
            self.parse_url += "+AND+"
            self.parse_url += ("%28" + "+OR+".join(["abs:" + x for x in search_keywords]) + "%29")
        if len(search_conferences) > 0:
            self.parse_url += "+AND+"
            self.parse_url += ("%28" + "+OR+".join(["co:" + x for x in search_conferences]) + "%29")
        self.parse_url += "&start=0&max_results=50"
        self.parse_url += "&sortBy=submittedDate&sortOrder=descending"

        print(self.parse_url)
        content = urlopen(self.parse_url)
        text = content.read().decode(content.headers.get_content_charset())
        soup = BeautifulSoup(text, "html.parser")
        self.info = soup.find_all('entry')

    def create_json(self, max_results = 5):
        divider_block = {"type":"divider"}
        blocks = [divider_block]

        for i, val in enumerate(self.info):
            if i < max_results:
                row, row2 = self.convert_value(val)
                if row != {}:
                    if self.is_compact:
                        blocks.extend([row, divider_block])
                    else:
                        blocks.extend([row, row2, divider_block])

        return {
            "ts": self.timestamp,
            "channel": self.channel,
            "username": self.username,
            "blocks": blocks,
        }

    def parse_from_arxiv_df(self):
        df = pd.DataFrame(columns = ["Id", "Title", "Updated", "Published",
                                     "Authors", "Categories", "Comment", "Summary"])
        for i, val in enumerate(self.info):
            df.loc[i] = self.convert_value_df(val)

        return df

    def convert_value(self, val):
        result = dict()
        result2 = dict()

        paper_title = "*<" + val.id.text + "|" + val.title.text.replace("\n", " ") + ">*\n"
        paper_comment = val.find_all('arxiv:comment')
        paper_comment = "" if len(paper_comment) == 0 else paper_comment[0].text.replace("\n", "")
        paper_title += paper_comment

        paper_published = datetime.strptime(val.published.text, "%Y-%m-%dT%H:%M:%SZ")
        paper_published = int(time.mktime(paper_published.timetuple()))
        paper_published = "<!date^%d^Published {date_num} {time_secs}|Date unknown>"%(paper_published)
        paper_updated = datetime.strptime(val.updated.text, "%Y-%m-%dT%H:%M:%SZ")
        paper_updated = int(time.mktime(paper_updated.timetuple()))
        paper_updated = "<!date^%d^Updated {date_num} {time_secs}|Date unknown>"%(paper_updated)
        paper_date = paper_published + "\n" + paper_updated

        paper_authors = ", ".join([x.find('name').text for x in val.find_all('author')])

        paper_categories = val.find_all('category')
        paper_categories = ", ".join([x['term'] for x in paper_categories])

        paper_summary = val.summary.text
        paper_summary = ". ".join(paper_summary.split('. ')[:3]).replace("\n", " ").strip()

        #is_accepted = len(re.findall("[A-Z][A-Z]", paper_comment)) > 0 or len(re.findall("Accepted|Submitted", paper_comment)) > 0

        if self.is_compact:
            result['type'] = "section"
            result['text'] = {"type": "mrkdwn", "text": paper_title}
            result['fields'] = [
                {"type": "mrkdwn", "text": "*Category*"},
                {"type": "mrkdwn", "text": " "},
                {"type": "mrkdwn", "text": paper_categories}
            ]
        else:
            result['type'] = "section"
            result['text'] = {"type": "mrkdwn", "text": paper_title}
            result['fields'] = [
                {"type": "mrkdwn", "text": "*Date*"},
                {"type": "mrkdwn", "text": "*Authors*"},
                {"type": "mrkdwn", "text": paper_date},
                {"type": "mrkdwn", "text": paper_authors},
                {"type": "mrkdwn", "text": "*Category*"},
                {"type": "mrkdwn", "text": " "},
                {"type": "mrkdwn", "text": paper_categories}
            ]

        result2["type"] = "section"
        result2['text'] = {"type": "mrkdwn", "text": paper_summary}

        return result, result2

    def convert_value_df(self, val):
        paper_id = val.id.text
        paper_title = val.title.text

        paper_updated = datetime.strptime(val.updated.text, "%Y-%m-%dT%H:%M:%SZ")
        paper_published = datetime.strptime(val.published.text, "%Y-%m-%dT%H:%M:%SZ")

        paper_authors = [x.find('name').text for x in val.find_all('author')]
        paper_categories = val.find_all('category')
        paper_categories = ", ".join([x['term'] for x in paper_categories])
        paper_comment = val.find_all('arxiv:comment')
        paper_comment = "" if len(paper_comment) == 0 else paper_comment[0].text

        paper_summary = val.summary.text
        paper_summary = ". ".join(paper_summary.split('. ')[:3]).replace("\n", " ")

        row = [paper_id, paper_title, paper_updated, paper_published, paper_authors,
               paper_categories, paper_comment, paper_summary]
        return row

#%%