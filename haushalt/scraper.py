import mechanize
import pymongo
import datetime
import soupselect
import re
from BeautifulSoup import BeautifulSoup

import local # set username and password in there!

class HaushaltsScraper(object):
    """scrape the aachen haushalt participation site"""

    def __init__(self, login_url, main_url, username, password):
        self.login_url = login_url
        self.main_url = main_url
        self.username = username
        self.password = password
        self.browser = mechanize.Browser()
        self.conn = pymongo.Connection()
        self.conn.drop_database("haushalt")
        self.db = self.conn.haushalt.proposals
        self.proposal_links = []

    def login(self):
        """login the user"""
        self.browser.open(self.login_url)
        self.browser.form = self.browser.forms().next()
        self.browser.form['name'] = self.username
        self.browser.form['pass'] = self.password
        self.browser.submit()

    def get_proposals(self):
        """retrieve a list of links to all proposals"""
        url = self.main_url
        while True:
            response = self.browser.open(url)
            soup = BeautifulSoup(response)
            for div in soup.findAll("div"):
                if "discussion" in str(div.get("class")).split(" "):
                    for url in ["http://www.aachen-rechnet-mit-ihnen.de"+str(div.find("a").get("href"))]:
                        self.proposal_links.append(url)

            # try to retrieve the next link
            elem = soup.find("li", {'class' : 'pager-next'})
            if elem is None: 
                break
            url = elem.find("a").get("href")
            #print ".", 
            #break

    def store_proposal(self, url):
        """fetch and store a proposal in the mongo db database"""
        doc = self.get_proposal(url)
        self.db.save(doc)
        return doc

    def get_proposal(self, url):
        """retrieve a proposal and return a dictionary with the information of it"""
        response = self.browser.open(url)

        soup = BeautifulSoup(response)
        main_wrapper = soup.find("div",{'class': "proposal-detail-box "})
        content = main_wrapper.find("div", "content")

        # get title
        title = content.find("h1").text

        # get description
        body_copy = content.findAll("p")
        submit_wrapper = soup.find("div",{'class': "proposal-submitted"})
        parts = submit_wrapper.text.split("|")
        date = datetime.datetime.strptime(parts[0].strip(),"%d.%m.%Y - %H:%M")
        username, usertype = re.match(".*von\ (.+) \((.+)\)", parts[1].strip()).groups()

        html = "".join([str(item) for item in body_copy[1:]])

        # get number
        spans = submit_wrapper.findAll("span")
        prefix =  spans[0].text
        nr = spans[1].text

        # get spar/ausgabe
        updown =  soupselect.select(soup, ".category-bar-content")[0].text.lower()
        category =  soupselect.select(soup, ".titlebar_inner")[0].text.lower()

        # get voting
        avg_rating = float(soup.find("span", {'class' : 'average-rating'}).find("span").text)
        total_votes = int(soup.find("span", {'class' : 'total-votes'}).find("span").text)
        comment_count = int(soup.find("div", {'class' : 'comment_count'}).text)

        doc = {
            'url' : url,
            'title' : title,
            'html' : html,
            'username' : username,
            'usertype' : usertype,
            'date' : date,
            'updown' : updown, 
            'category' : category, 
            'votes' : total_votes,
            'rating' : avg_rating,
            'comment_count' : comment_count,
            'type' : prefix,
            '_id' : nr
        }
        print updown, comment_count
        return doc

if __name__=="__main__":
    s = HaushaltsScraper("http://www.aachen-rechnet-mit-ihnen.de/user?destination=node/5593", 
                         "http://www.aachen-rechnet-mit-ihnen.de/diskussion",
                         local.username, local.password)
    s.login()
    s.get_proposals()
    for url in s.proposal_links:
        print s.store_proposal(url)

