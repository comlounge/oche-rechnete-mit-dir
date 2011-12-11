# encoding=utf8
from starflyer import Handler, ashtml, asjson
import copy
import math

class Impressum(Handler):
    """display impressum"""

    template = "impressum.html"

    @ashtml()
    def get(self):
        return self.render()

class OpenData(Handler):
    """display opendata"""

    template = "opendata.html"

    @ashtml()
    def get(self):
        return self.render()

class Homepage(Handler):
    """display homepage"""

    template = "homepage.html"

    @ashtml()
    def get(self):
        return self.render()

class ProposalAdapter(object):
    
    def __init__(self, proposal, config):
        self.proposal = proposal
        self.config = config

    @property
    def rating_contra(self):
        ratings = self.proposal['rating']
        if ratings<2:
            return "0px"
        p = 60-60*(3-ratings)
        return "%spx" %p

    @property
    def rating_pro(self):
        ratings = self.proposal['rating']
        if ratings==2:
            return "1px"
        if ratings>2:
            return "0px"
        p = 60*(2-ratings)
        return "%spx" %p
        return "30px"


class Page(object):
    """one page"""

    def __init__(self, no, params, url_for, active=False, dots=False):
        params = copy.copy(params)
        params['page'] = str(no)
        self.url = url_for("proposals", append_unknown=True, **params)
        self.no = no
        self.active = active
        self.dots = dots # True = show some dots instead

class Amount(object):
    """an amount"""

    def __init__(self, amount, params, url_for, active=False):
        params = copy.copy(params)
        params['amount'] = str(amount)
        self.url = url_for("proposals", append_unknown=True, **params)
        self.amount = amount
        self.active = active

    def __str__(self):
        return unicode(self.amount)


class MongoPager(object):
    """a pager object"""

    def __init__(self, results, per_page = 20, radius = 3, page = 1, params = {}, url_for=None):
        """initialize a pager.

        :param results: A mongo Result Set
        :param per_page: the amount of items per page
        :param radius: the amount of pages around the recent page
        :param page: the active page 
        """

        self.results = results
        self.amount = results.count()
        self.per_page = per_page
        self.page = int(page)
        self.radius = radius
        self.params = params
        self.url_for = url_for

        self.pages = int(math.ceil((self.amount+0.0) / self.per_page)) # number of pages
        if self.page > self.pages:
            self.page = self.pages
        self.is_first = self.page == 1
        self.is_last = self.page == self.pages
        self.prev_page = Page(self.page-1 if self.page >0 else 1, params, url_for)
        self.next_page = Page(self.page+1 if self.page < self.pages else self.pages, params, url_for)

        # compute radius (= amount of pages next and prev to active page)
        # we want something like 1 ... 3 4 5 6 7 ... 12 in case active = 5
        lower = max(1, page - radius)
        higher = min(self.pages, page + radius)
        self.range = range(lower, higher+1)

        # compute which objects we are showing
        self.count_from = (self.page-1) * self.per_page + 1
        self.count_to = min((self.page) * self.per_page, self.amount)

    @property
    def objects(self):
        return self.results.limit(self.per_page).skip((self.page-1)*self.per_page)

    @property
    def page_range(self):
        """return a list of page objects

        also count in the radius we computed in front
        
        """

        pages = []
        for page_no in self.range:
            pages.append(Page(page_no, self.params, self.url_for, active=page_no==self.page))
        if 1 not in self.range:
            pages.insert(0, Page(1, self.params, self.url_for, active=False))
            if 2 not in self.range:
                pages.insert(1, Page(2, self.params, self.url_for, dots=True))
        if self.pages not in self.range:
            pages.append(Page(self.pages -1, self.params, self.url_for, dots=True))
        if self.pages not in self.range:
            pages.append(Page(self.pages, self.params, self.url_for))
        return pages
            

class Proposals(Handler):
    """display proposals"""

    template = "proposals.html"

    @ashtml()
    def get(self):

        sort = self.request.args.get("sort", "popular-down")
        page = int(self.request.args.get("page", "1"))
        amount = int(self.request.args.get("amount", "10"))
        vtype = self.request.args.get("vtype", "both")
        updown = self.request.args.get("updown", "all")

        q = {}
        if vtype=="citizen":
            q['type']="B"
        elif vtype=="gov":
            q['type']="V"
        if updown in ["sparvorschlag", 'ausgabevorschlag', 'k.a.']:
            q['updown'] = updown
        
        proposals = self.config.dbs.haushalt.proposals.find(q)

        if sort=="popular-down":
            proposals = proposals.sort("rating", 1)
        elif sort=="popular-up":
            proposals = proposaly.sort("rating", -1)
        elif sort=="comment-down":
            proposals = proposals.sort("comment_count", -1)
        elif sort=="comment-up":
            proposals = proposals.sort("comment_count", 1)

        params = {
            'page' : page, 
            'amount' : amount, 
            'sort' : sort, 
            'vtype' : vtype, 
            'updown' : updown, 
        }

        pager = MongoPager(proposals, amount, 2, page, params, self.url_for)
        proposals = [ProposalAdapter(p, self.config) for p in pager.objects]
        return self.render(
            proposals = proposals, 
            pager = pager,
            amounts = [Amount(a, params, self.url_for, active=amount==a) for a in [10, 20, 50]],
            **params)


class Proposal(Handler):

    template = "proposal.html"

    @ashtml()
    def get(self, vid):
        proposal = self.config.dbs.haushalt.proposals.find_one({'_id' : vid})
        return self.render(
            title = "Oche rechnete mit Dir: "+proposal['title'],
            description = proposal['html'],
            view = ProposalAdapter(proposal, self.config)
            )




class ProposalJSON(Handler):

    @asjson()
    def get(self, vid):
        proposal = self.config.dbs.haushalt.proposals.find_one({'_id' : vid})
        proposal['date'] = proposal['date'].isoformat()
        return proposal

class ProposalsJSON(Handler):

    @asjson()
    def get(self):
        start = int(self.request.args.get("start", 0))
        limit = int(self.request.args.get("limit", 20))
        proposals = self.config.dbs.haushalt.proposals.find().limit(limit).skip(start)
        res = []
        for p in proposals:
            n = {
                'url' : p['url'],
                'title' : p['title'],
                'rating' : p['rating'],
                'votes' : p['votes'],
                'comment_count' : p['comment_count'],
                'updown' : p['updown'],
                'type' : p['type'],
                'id' : p['_id'],
                'category' : p['category'],
                'detail_url' : "http://haushalt.oecher.info"+ self.url_for("proposal_json", vid = p['_id']),
            }
            res.append(n)
        return {
            'success' : True,
            'results' : res,
            'total' : proposals.count(),
            'returned' : len(res),
            'start' : start,
            'limit' : limit,
            'help' : {
                'fields' : {
                    'url' : 'Die URL zum Original-Vorschlag bei aachen-rechnet-mit-ihnen.de',
                    'title' : 'Titel des Vorschlags',
                    'rating' : 'Das Rating des Vorschlags. 1=pro, 2=neutral, 3=contra',
                    'votes' : 'Anzahl der Bewertungen',
                    'comment_count' : 'Anzahl der abgegebenen Kommentare',
                    'updown' : 'ob Sparvorschlag, Ausgabevorschlag oder keine Angabe',
                    'category' : 'Kategorie des Vorschlags',
                    'detail_url' : 'URL, unter der weitere Angaben zum Vorschlag ermittelt werden können',
                },
                'query_params' : {
                    'start' : 'Vorschläge ab diesem Index listen',
                    'limit' : 'nur soviel Vorschläge auflisten',
                },
            }
        }




