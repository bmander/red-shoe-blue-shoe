from urllib import urlopen, urlencode, quote
try:
    import json
except ImportError:
    import simplejson as json
from apikey import APIKEY
import csv

class Zappos:
    domain = "api.zappos.com"

    def __init__(self, apikey):
        self.apikey = apikey

    def statistics( self, locationval=None, locationtype="state", type="latestStyles" ):
        query = {'type':'latestStyles',
                 'filters':json.dumps({"categorization":{"categoryType":"Shoes"}}),
                 'key':self.apikey}
        if locationval:
            location = {locationtype:locationval}
            query['location']=json.dumps(location)

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

    @property
    def location(self):
        return self.jsonblob['geometry']['location']

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

class DataScienceToolkit():
    def __init__(self):
        pass

    def politics(self, lat, lon):
        point = [{"latitude":str(lat),"longitude":str(lon)}]
        url = "http://www.datasciencetoolkit.org/coordinates2politics/"+quote(json.dumps(point))
       
        for result in json.loads( urlopen(url).read() ):
            yield DSTPoliticsResult(result)

class DSTPoliticsResult():
    def __init__(self, jsonblob):
        self.jsonblob = jsonblob

    @property
    def county(self):
        for region in self.jsonblob['politics']:
            if region['friendly_type']=='county':
                return region['name']

    @property
    def state(self):
        for region in self.jsonblob['politics']:
            if region['friendly_type']=='state':
                return region['name']

def zip_to_county(zip):
    gg = GoogleGeocode()
    resp = gg.geocode(zip)

    # the google geocoder couldn't handle it. all hope is lost
    if resp.status != "OK":
        return None

    # ditto
    if len(resp.results)==0:
        return None

    result = resp.results[0]

    state = result.state
    county = result.county

    # sometimes google returns a location but not a state/county pair. in this case,
    # fall back on the DataScienceToolkit API
    if state is None or county is None:
        dst = DataScienceToolkit()
        location = result.location 
        polresult = list(dst.politics(location['lat'],location['lng']))[0]

        state = polresult.state
        county = polresult.county

    return (state, county)

def votes(state,county):
    fp = open("election.csv")

    rd = csv.reader( fp )
    rd.next()

    for recstate,abbr,reccounty,precincts,reporting,obama,mccain,other in rd:
        if recstate.lower().strip()==state.lower().strip() and reccounty.lower().strip()==county.lower().strip():
            return int(obama),int(mccain),int(other)

def votes_for_result(result):
    zip = result.get('zip')
    if zip is None:
        return None

    loc = zip_to_county( zip)
    if loc is None:
        return None

    state,county = loc
    if state and county:
        return votes(state,county)

def results(state=None):
    zz = Zappos(APIKEY)
    stats = zz.statistics(state)
   
    for result in stats['results']:
        yield result

def main():
    for result in results():
        yield votes_for_result(result)
    
if __name__=='__main__':
    for phrase in main():
        print phrase
