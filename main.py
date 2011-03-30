from urllib import urlopen, urlencode
import json
from apikey import APIKEY
import csv

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

class GoogleGeocode:
    def __init__(self):
        pass

    def geocode(self,address):
        url = "http://maps.googleapis.com/maps/api/geocode/json?address=%s&sensor=false"%address

        return GoogleGeocodeResponse( json.loads( urlopen(url).read() ) )

class GoogleGeocodeResult():
    def __init__(self, jsonblob):
        self.jsonblob = jsonblob

    @property
    def address_components(self):
        return self.jsonblob['address_components']

    def _address_component(self,name):
        for comp in self.address_components:
            if name in comp['types']:
                return comp['long_name']

        return None

    @property
    def county(self):
        return self._address_component("administrative_area_level_2")

    @property
    def state(self):
        return self._address_component("administrative_area_level_1")

class GoogleGeocodeResponse():
    def __init__(self, jsonblob):
        self.jsonblob = jsonblob

    @property
    def status(self):
        return self.jsonblob['status']

    @property
    def results(self):
        ret = []
        for result in self.jsonblob['results']:
            ret.append( GoogleGeocodeResult(result) )
        return ret

def zip_to_county(zip):
    gg = GoogleGeocode()
    resp = gg.geocode(zip)

    if resp.status != "OK":
        return None

    if len(resp.results)==0:
        return None

    result = resp.results[0]

    return (result.state, result.county)

def votes(state,county):
    fp = open("election.csv")

    rd = csv.reader( fp )
    rd.next()

    for recstate,abbr,reccounty,precincts,reporting,obama,mccain,other in rd:
        if recstate.lower().strip()==state.lower().strip() and reccounty.lower().strip()==county.lower().strip():
            return int(obama),int(mccain),int(other)

    
if __name__=='__main__':
    zz = Zappos(APIKEY)
    stats = zz.statistics("CA")
    print json.dumps( stats, indent=2 )
   
    for result in stats['results']:
        zip = result['zip']
        
        print zip
        state,county = zip_to_county( zip )
        print state,county
        if state and county:
            print votes(state,county)
        print
