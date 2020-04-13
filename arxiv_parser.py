import re
from datetime import datetime
import time
from bs4 import BeautifulSoup
from urllib.request import urlopen

class ArxivParser:
    
    def __init__(self, search_categories = ["cs.CV", "cs.LG"], search_date = "2020-04-09"):
        self.search_categories = search_categories
        self.search_date = datetime.strptime(search_date, "%Y-%m-%d")
        self.max_results = 100
        self.base_url = "http://export.arxiv.org/api/query?search_query="
        
    def parse_from_arxiv(self):
        parse_url = self.base_url
        parse_url += "+OR+".join(["cat:" + x for x in self.search_categories])
        parse_url += "&start=0&max_results=%d"%(self.max_results)
        parse_url += "&sortBy=lastUpdatedDate&sortOrder=descending"
        
        content = urlopen(parse_url)
        text = content.read().decode(content.headers.get_content_charset())
        soup = BeautifulSoup(text, "html.parser")
        info = soup.find_all('entry')
        
        attachments = [self.convert_value(val) for val in info]
        attachments = [val for val in attachments if val != {}]
        
        result_dict = {
            "text": "Search Results: %d new papers"%(len(attachments)),
            "attachments": attachments
        }
        
        return result_dict

    def convert_value(self, val):
        result = dict()
        
        paper_updated = datetime.strptime(val.updated.text, "%Y-%m-%dT%H:%M:%SZ")
        if paper_updated >= datetime(2020, 4, 9) and paper_updated < datetime(2020, 4, 10):
            paper_updated = int(time.mktime(paper_updated.timetuple()))
            paper_updated = "<!date^%d^Published {date_num} {time_secs}|Date unknown>"%(paper_updated)
            
            paper_authors = [x.find('name').text for x in val.find_all('author')]
            paper_comment = val.find_all('arxiv:comment')
            paper_comment = "" if len(paper_comment) == 0 else paper_comment[0].text
            paper_published = datetime.strptime(val.published.text, "%Y-%m-%dT%H:%M:%SZ")
            paper_published = int(time.mktime(paper_published.timetuple()))
            paper_published = "<!date^%d^Published {date_num} {time_secs}|Date unknown>"%(paper_published)
            
            paper_categories = val.find_all('category')
            paper_categories = ", ".join([x['term'] for x in paper_categories])
            
            paper_summary = val.summary.text
            paper_summary = ". ".join(paper_summary.split('. ')[:3]).replace("\n", " ")
            
            is_accepted = len(re.findall("[A-Z][A-Z]", paper_comment)) > 0 or \
                len(re.findall("Accepted", paper_comment)) > 0
            
            if is_accepted:
                result['mrkdwn_in'] = ['text']
                result['color'] = '#36a64f'
                result['author_name'] = ", ".join(paper_authors)    
                result['title'] = val.title.text
                result['title_link'] = val.id.text
                result['text'] = paper_comment
            
                fields_list = [
                    {"title": "Dates", "value": paper_updated + "\n" + paper_published, "short": True}, 
                    {"title": "Category", "value": paper_categories, "short": True},
                    {"title": "Summary", "value": paper_summary, "short": False}
                ]
                result['fields'] = fields_list
                result['footer'] = "arxiv-bot"
    
        return result   
        
