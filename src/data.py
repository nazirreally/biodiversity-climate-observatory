import requests
import pandas as pd
import pycountry

GBIF = "https://api.gbif.org/v1/occurrence/search"
WB = "https://api.worldbank.org/v2/country/all/indicator/AG.LND.FRST.ZS"
def get(url, params):
    r = requests.get(url, params=params, timeout=90)
    r.raise_for_status()
    return r.json()

def parse_facet(payload, field):
    matches = [f for f in payload["facets"] if f["field"].replace("_","").lower() == field.replace("_","").lower()]
    if len(matches) != 1:
        raise ValueError("Missing or ambiguous facet")
    df = pd.DataFrame(matches[0]["counts"]).rename(columns={"name":"key","count":"occurrences"})
    if df.empty or df.key.duplicated().any() or (df.occurrences < 0).any():
        raise ValueError("Invalid facet")
    return df, int(payload["count"])

def facet(field, start, end):
    return parse_facet(get(GBIF, {"limit":0,"facet":field,"facetLimit":300,"facetMincount":1,"hasCoordinate":"true","hasGeospatialIssue":"false","year":f"{start},{end}"}),field)

def forest():
    rows=[]
    page=1
    while True:
        meta, data=get(WB, {"format":"json","date":"1990:2026","per_page":10000,"page":page})
        rows.extend(data or [])
        if page >= int(meta["pages"]): break
        page+=1
    valid={c.alpha_3 for c in pycountry.countries}
    df=pd.DataFrame([{"iso3":r["countryiso3code"],"year":int(r["date"]),"forest_pct":r["value"]} for r in rows if r["value"] is not None and r["countryiso3code"] in valid])
    if df.empty or df.duplicated(["iso3","year"]).any() or not df.forest_pct.between(0,100).all():
        raise ValueError("Invalid forest series")
    return df

def join(countries, forests, year):
    return countries.merge(forests.loc[forests.year.eq(year),["iso3","forest_pct"]],on="iso3",how="left",validate="one_to_one")

def country_frame(df):
    codes={c.alpha_2:c.alpha_3 for c in pycountry.countries}
    names={c.alpha_2:c.name for c in pycountry.countries}
    return df.assign(iso3=df.key.map(codes),country=df.key.map(names)).dropna(subset=["iso3"])
