from urllib import urlopen, urlencode
import json
from apikey import APIKEY

class Zappos:
    domain = "api.zappos.com"

    def __init__(self, apikey):
        self.apikey = apikey

    def statistics( self, locationval, locationtype="state", type="latestStyles" ):
        location = {locationtype:locationval}
        query = {'type':'latestStyles','location':json.dumps(location),'key':self.apikey}

        url = "http://%s/Statistics?%s"%(self.domain, urlencode(query))

        fp = urlopen( url )
        body = fp.read()
    
        return json.loads( body )
    
if __name__=='__main__':
    zz = Zappos(APIKEY)
    stats = zz.statistics("CA")
    print json.dumps( stats, indent=2 )
