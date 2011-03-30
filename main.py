from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
import api

import os
from google.appengine.ext.webapp import template

class Vote(db.Model):
    orderItemId = db.StringProperty(required=True)
    productId = db.StringProperty(required=True)
    zip = db.StringProperty(required=True)
    blue_vote = db.FloatProperty(required=True)
    red_vote = db.FloatProperty(required=True)

class Tally(db.Model):
    productId = db.StringProperty(required=True)
    productName = db.StringProperty(required=True)
    brandName = db.StringProperty(required=True)
    defaultProductUrl = db.LinkProperty(required=True)
    defaultImageUrl = db.LinkProperty(required=True)
    blue_votes = db.FloatProperty(required=True)
    red_votes = db.FloatProperty(required=True)
    ratio = db.FloatProperty(required=True)
    difference = db.FloatProperty()

class DataFixer(webapp.RequestHandler):
    def get(self):
        n = 0
        for tally in Tally.all().filter("difference =", None)
            tally.difference = tally.blue_votes-tally.red_votes
            tally.put()
            n += 1

        self.response.out.write( str(n) )

class MainPage(webapp.RequestHandler):
    def get(self):
        red_shoes = Tally.all().order('difference').fetch(5)
        blue_shoes = Tally.all().order('-difference').fetch(5)

        path = os.path.join(os.path.dirname(__file__), 'views/index.html')
        self.response.out.write(template.render(path, {'red_shoes':red_shoes,'blue_shoes':blue_shoes}))

class Poll(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        for result in api.results():
            # check that a vote for this orderItemId hasn't already been registered
            v = Vote.all().filter('orderItemId =', result['orderItemId']).get()
            if v is not None:
                self.response.out.write( "already voted on %s with orderid %s\n"%(result['productId'],result['orderItemId']) )
                continue

            votes = api.votes_for_result(result)

            if votes is not None:
                
                blue_votes, red_votes, other_votes = votes
                total = sum(votes)

                blue_vote = blue_votes/float(total)
                red_vote = red_votes/float(total)

                # create a vote
                v = Vote(orderItemId=result['orderItemId'],
                         productId=result['productId'],
                         zip=result['zip'],
                         blue_vote=blue_vote,
                         red_vote=red_vote)
                v.put()
                self.response.out.write( "voting %0.2f,%0.2f for %s\n"%(blue_vote,red_vote,result['productId']) )

                # update the tally
                tally = Tally.all().filter('productId =', result['productId']).get()
                if tally is None:
                    tally = Tally(productId=result['productId'],
                                  productName=result['productName'],
                                  brandName=result['brandName'],
                                  defaultProductUrl=result['defaultProductUrl'],
                                  defaultImageUrl=result['defaultImageUrl'],
                                  blue_votes=0.0,
                                  red_votes=0.0,
                                  ratio=0.5,
                                  difference=0.0)
                tally.blue_votes += blue_vote
                tally.red_votes += red_vote
                tally.ratio = tally.blue_votes/float(tally.red_votes)
                tally.difference = tally.blue_votes-tally.red_votes
                tally.put()

application = webapp.WSGIApplication(
                                     [('/poll',Poll),
                                      ('/fix',DataFixer),
                                      ('/', MainPage)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
