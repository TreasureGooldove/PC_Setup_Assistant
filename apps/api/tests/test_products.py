import asyncio

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.features.builds.catalog import fixture_parts
from app.features.ladder.service import ladder_entries
from app.features.products.service import (
    get_product_detail,
    parse_jd_product_html,
    validate_jd_product_url,
)
from app.main import app


def test_expanded_catalog_and_ladder_share_ids():
    parts = fixture_parts()
    ids = [part.id for part in parts]
    assert len(ids) == len(set(ids))
    assert len([part for part in parts if str(part.category) == "cpu"]) >= 15
    assert len([part for part in parts if str(part.category) == "gpu"]) >= 15
    assert len([part for part in parts if str(part.category) == "motherboard"]) >= 10
    catalog_ids = set(ids)
    entries = ladder_entries()
    assert len(entries) >= 30
    assert all(entry.id in catalog_ids for entry in entries)
    assert all(entry.source_url and "zol.com.cn" in entry.source_url for entry in entries)


def test_jd_public_html_parser_extracts_title_and_parameters():
    page = """
    <html><head><title>微星 MPG X870E CARBON MAX WIFI - 京东</title></head>
    <body><dl><dt>品牌</dt><dd>微星（MSI）</dd>
    <dt>型号</dt><dd>MPG X870E CARBON MAX WIFI</dd>
    <dt>CPU插槽</dt><dd>AMD AM5</dd><dt>M.2接口数量</dt><dd>5个</dd></dl></body></html>
    """
    title, parameters = parse_jd_product_html(page)
    assert title and "X870E" in title
    assert parameters["brand_name"] == "微星（MSI）"
    assert parameters["model"] == "MPG X870E CARBON MAX WIFI"
    assert parameters["socket"] == "AMD AM5"
    assert parameters["m2_slots"] == "5个"


def test_jd_url_validation_has_strict_public_product_allowlist():
    assert validate_jd_product_url("https://item.jd.com/100012345678.html")
    for url in (
        "http://item.jd.com/100012345678.html",
        "https://example.com/100012345678.html",
        "https://item.jd.com.evil.example/100012345678.html",
        "https://item.jd.com/list.html",
    ):
        with pytest.raises(ValueError):
            validate_jd_product_url(url)


def test_product_detail_returns_two_marked_fixture_offers():
    settings = Settings(_env_file=None, jd_public_fetch_enabled=False)
    detail = asyncio.run(get_product_detail("mb-msi-x870e-carbon", settings))
    assert detail.part.specs["chipset"] == "AMD X870E"
    assert {offer.platform for offer in detail.offers} == {"jd", "pdd"}
    assert all(offer.is_live is False for offer in detail.offers)
    assert all("示例报价" in offer.status for offer in detail.offers)
    assert any(source.provider == "京东公开商品页" for source in detail.sources)


def test_product_detail_route_and_unknown_product():
    with TestClient(app) as client:
        response = client.get("/api/products/gpu-4070s")
        assert response.status_code == 200
        assert len(response.json()["offers"]) == 2
        assert response.json()["evidence"][0]["url"].startswith("https://vga.zol.com.cn/")
        missing = client.get("/api/products/not-found")
        assert missing.status_code == 404
