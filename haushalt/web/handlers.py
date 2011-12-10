from starflyer import Handler, ashtml

class Impressum(Handler):
    """display impressum"""

    template = "impressum.html"

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

class Proposals(Handler):
    """display proposals"""

    template = "proposals.html"

    @ashtml()
    def get(self):
        sort = self.request.args.get("sort", "popular-down")
        if sort=="popular-down":
            proposals = self.config.dbs.haushalt.proposals.find().sort("rating", 1)
        elif sort=="popular-up":
            proposals = self.config.dbs.haushalt.proposals.find().sort("rating", -1)
        elif sort=="comment-down":
            proposals = self.config.dbs.haushalt.proposals.find().sort("comment_count", -1)
        elif sort=="comment-up":
            proposals = self.config.dbs.haushalt.proposals.find().sort("comment_count", 1)
        proposals = [ProposalAdapter(p, self.config) for p in proposals]
        return self.render(
            proposals = proposals, 
            sort = sort)


class Proposal(Handler):

    template = "proposal.html"

    @ashtml()
    def get(self, vid):
        proposal = self.config.dbs.haushalt.proposals.find_one({'_id' : vid})
        return self.render(view = ProposalAdapter(proposal, self.config))




