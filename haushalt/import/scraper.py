import mechanize
import pymongo
import datetime
import soupselect
import re
from BeautifulSoup import BeautifulSoup

import local # set username and password in there!

class HaushaltsScraper(object):
    """scrape the aachen haushalt participation site"""

    def __init__(self, login_url, username, password):
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

    def get_proposals(self, url):
        """retrieve a list of links to all proposals"""
        url = self.main_url
        links = []
        while True:
            response = self.browser.open(url)
            soup = BeautifulSoup(response)
            for div in soup.findAll("div"):
                if "discussion" in str(div.get("class")).split(" "):
                    for url in ["http://www.aachen-rechnet-mit-ihnen.de"+str(div.find("a").get("href"))]:
                        links.append(url)

            # try to retrieve the next link
            elem = soup.find("li", {'class' : 'pager-next'})
            if elem is None: 
                break
            url = elem.find("a").get("href")
        return links

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
        rightside = soupselect.select(soup, ".rightside")[0]
        avg_rating = float(rightside.find("span", {'class' : 'average-rating'}).find("span").text)
        total_votes = int(rightside.find("span", {'class' : 'total-votes'}).find("span").text)
        comment_count = int(rightside.find("div", {'class' : 'comment_count'}).text)

        # comments
        comments =  soupselect.select(soup, ".node-type-comment")
        clist = []
        node_id = None
        for comment in comments:
            comment_id = int(comment.get("id").split("-")[1])
            comment_username = comment.find("span", {'class' : 'submitted'}).find("a").text
            comment_date = comment.find("span", {'class' : 'submitted'}).text.split("am")[1].strip()
            comment_title = comment.find("h1").text.strip()
            comment_body = "".join([str(p) for p in comment.findAll("p")])
            is_in_reply = "comment-reply" in comment.get("class")
            comment = {
                '_id' : comment_id,
                'username' : comment_username,
                'date' : comment_date,
                'title' : comment_title,
                'content' : comment_body,
                'type' : '',
                'in_reply_to' : node_id if is_in_reply else None,
            }
            if is_in_reply is False:
                node_id = comment_id
            clist.append(comment)


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
            '_id' : nr,
            'comments' : clist, 
        }
        return doc

if __name__=="__main__":
    s = HaushaltsScraper("http://www.aachen-rechnet-mit-ihnen.de/user?destination=node/5593", 
                         local.username, local.password)
    s.login()
    proposals1 = self.get_proposals("http://www.aachen-rechnet-mit-ihnen.de/diskussion")
    proposals2 = self.get_proposals("http://www.aachen-rechnet-mit-ihnen.de/diskussion-stadt")
    for url in proposals1 + proposals2:
        print s.store_proposal(url)

