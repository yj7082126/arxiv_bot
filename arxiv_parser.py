import re
from datetime import datetime
import time
import pandas as pd
from bs4 import BeautifulSoup
from urllib.request import urlopen

class ArxivParser:
    
    def __init__(self, channel, search_categories = ["cs.CV", "cs.LG"], search_date = "2020-04-09"):
        self.channel = channel
        self.username = "arxiv_bot"
        self.timestamp = ""
        self.search_categories = search_categories
        self.search_date = datetime.strptime(search_date, "%Y-%m-%d")
        self.max_results = 20
        self.base_url = "http://export.arxiv.org/api/query?search_query="
        
    def parse_from_arxiv(self):
        parse_url = self.base_url
        parse_url += "+OR+".join(["cat:" + x for x in self.search_categories])
        parse_url += "&start=0&max_results=%d"%(self.max_results)
        parse_url += "&sortBy=lastUpdatedDate&sortOrder=descending"
        
        content = urlopen(parse_url)
        text = content.read().decode(content.headers.get_content_charset())
        soup = BeautifulSoup(text, "html.parser")
        self.info = soup.find_all('entry')
        
    def create_json(self):
        result_dict = {
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": "We found *%d papers* in arxiv from *%s to %s*" %(
                    len(self.info), 
                    datetime.strftime(datetime(2020, 4, 9), "%Y-%m-%d"),
                    datetime.strftime(datetime(2020, 4, 10), "%Y-%m-%d")
                )
			}
		}
        divider_block = {"type":"divider"}
        blocks = [result_dict, divider_block]
        
        for i, val in enumerate(self.info):
            if i < 10:
                row, row2 = self.convert_value(val)
                if row != {}:
                    blocks.extend([row, row2, divider_block])

        return {
            "ts": self.timestamp,
            "channel": self.channel,
            "username": self.username,
            "blocks": blocks,
        }
    
    def parse_from_arxiv_df(self):
        parse_url = self.base_url
        parse_url += "+OR+".join(["cat:" + x for x in self.search_categories])
        parse_url += "&start=0&max_results=%d"%(self.max_results)
        parse_url += "&sortBy=lastUpdatedDate&sortOrder=descending"
        
        content = urlopen(parse_url)
        text = content.read().decode(content.headers.get_content_charset())
        soup = BeautifulSoup(text, "html.parser")
        info = soup.find_all('entry')

        df = pd.DataFrame(columns = ["Id", "Title", "Updated", "Published", 
                                     "Authors", "Categories", "Comment", "Summary"])        
        for i, val in enumerate(info):
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
        
        is_accepted = len(re.findall("[A-Z][A-Z]", paper_comment)) > 0 or \
            len(re.findall("Accepted", paper_comment)) > 0
        
        if is_accepted:
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
ap = ArxivParser(3300)
ap.parse_from_arxiv()
result = ap.create_json()

#%%