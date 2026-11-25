"""Deterministic unit fixtures only; never dashboard observations."""
import pandas as pd
import pytest
from src.data import parse_facet, join
def test_facet_case():
    d,n=parse_facet({"count":3,"facets":[{"field":"BASIS_OF_RECORD","counts":[{"name":"X","count":3}]}]},"basisOfRecord")
    assert n==3 and d.occurrences.sum()==3
def test_missing_facet():
    with pytest.raises(ValueError): parse_facet({"facets":[]},"country")
def test_exact_year():
    c=pd.DataFrame({"iso3":["X","Y"]})
    f=pd.DataFrame({"iso3":["X"],"year":[2020],"forest_pct":[1.]})
    assert join(c,f,2021).forest_pct.isna().all()
