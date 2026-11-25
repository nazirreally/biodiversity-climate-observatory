import streamlit as st
import plotly.express as px
import pandas as pd
from src.data import facet, forest, join, country_frame

st.set_page_config(page_title="Forest / Field",page_icon="🌿",layout="wide")
st.markdown("""<style>
.block-container{max-width:1440px;padding-top:2rem}
[data-testid="stMetric"]{border:1px solid #47685b;border-radius:14px;padding:18px;background:#142c26}
h1{letter-spacing:-.05em;font-size:3rem!important}
[data-testid="stTabs"] button{font-weight:600}
</style>""",unsafe_allow_html=True)
st.caption("FIELD NOTES  /  GLOBAL OBSERVATION INTELLIGENCE")
st.title("Forest / Field")
st.write("Explore biodiversity reporting effort alongside observed forest cover. Indexed records are not population estimates.")
@st.cache_data(ttl=3600,show_spinner=False)
def load(start,end):
    c,total=facet("country",start,end)
    y,_=facet("year",start,end)
    b,_=facet("basisOfRecord",start,end)
    return country_frame(c),total,y,b,forest()
start,end=st.slider("Collection-year window",1990,2026,(2000,2025))
try:
    with st.spinner("Retrieving publisher observations…"):
        c,total,y,b,f=load(start,end)
except Exception as exc:
    st.error("Publisher data unavailable. No substitute data is displayed.")
    st.caption(str(exc))
    st.stop()
if c.empty:
    st.warning("No mapped country observations for this selection.")
    st.stop()
year=st.selectbox("Forest reporting year",sorted(f.year.unique(),reverse=True))
d=join(c,f,year)
a,z,q,w=st.columns(4)
a.metric("GBIF index records",f"{total:,}")
z.metric("Mapped countries",len(c))
q.metric("Forest observations",f"{len(f):,}")
w.metric("Matched countries",int(d.forest_pct.notna().sum()))
def chart(fig):
    fig.update_layout(template="plotly_dark",paper_bgcolor="#10231e",plot_bgcolor="#10231e",margin=dict(l=20,r=20,t=40,b=20))
    st.plotly_chart(fig,use_container_width=True)
tabs=st.tabs(["Field map","Country history","Observation methods","Data audit"])
with tabs[0]:
    metric=st.radio("Map measure",["occurrences","forest_pct"],horizontal=True)
    projection=st.selectbox("Projection",["natural earth","orthographic","equirectangular"])
    mode=st.radio("Map style",["Choropleth","Bubbles"],horizontal=True)
    m=d.dropna(subset=[metric])
    if m.empty: st.info("No matched observations.")
    elif mode=="Choropleth": chart(px.choropleth(m,locations="iso3",color=metric,hover_name="country",projection=projection,color_continuous_scale="Tealgrn"))
    else: chart(px.scatter_geo(m,locations="iso3",size=metric,color=metric,hover_name="country",projection=projection,color_continuous_scale="Tealgrn"))
    left,right=st.columns(2)
    with left: chart(px.bar(m.nlargest(20,metric).sort_values(metric),x=metric,y="country",orientation="h",title="Top 20 countries"))
    with right: chart(px.histogram(m,x=metric,title="Country distribution"))
with tabs[1]:
    selected=st.multiselect("Compare countries",c.country.sort_values().tolist(),default=c.nlargest(2,"occurrences").country.tolist())
    hist=f.merge(c[["iso3","country"]],on="iso3")
    hist=hist[hist.country.isin(selected)].sort_values(["country","year"])
    if hist.empty: st.info("Select countries with forest observations.")
    else:
        chart(px.line(hist,x="year",y="forest_pct",color="country",title="Forest share of land (%)"))
        hist["change"]=hist.groupby("country").forest_pct.diff().where(hist.groupby("country").year.diff().eq(1))
        chart(px.bar(hist,x="year",y="change",color="country",barmode="group",title="Adjacent-year change (percentage points)"))
with tabs[2]:
    y=y.assign(year=pd.to_numeric(y.key,errors="coerce")).dropna(subset=["year"]).sort_values("year")
    chart(px.line(y,x="year",y="occurrences",markers=True,title="Indexed records by collection year"))
    chart(px.bar(b.sort_values("occurrences"),x="occurrences",y="key",orientation="h",title="Basis of record"))
with tabs[3]:
    st.write("Country, year and basis facets are separate aggregates; they cannot be cross-tabulated. Forest cover is joined at one exact reporting year, not over the GBIF collection window.")
    st.write(f"Forest coverage: {f.year.min()}–{f.year.max()}; {len(f):,} country-year rows. GBIF mapped facet rows: {len(c)}.")
    st.dataframe(d,use_container_width=True)
    st.download_button("Export observed joined rows",d.to_csv(index=False),"country_forest.csv","text/csv")
    st.download_button("Export forest history",f.to_csv(index=False),"forest_history.csv","text/csv")
    st.markdown("[GBIF API](https://techdocs.gbif.org/en/openapi/v1/occurrence) · [World Bank indicator](https://data.worldbank.org/indicator/AG.LND.FRST.ZS)")
