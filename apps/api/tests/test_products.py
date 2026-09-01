import asyncio
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.features.builds.catalog import fixture_parts
from app.features.ladder.service import ladder_entries
from app.features.products import service as product_service
from app.features.products.service import (
    get_product_detail,
    parse_jd_product_html,
    validate_jd_product_url,
)
from app.features.products.taobao_mcp import (
    TaobaoMcpResult,
    parse_product_result,
    validate_product_reference,
)
from app.features.products.zol_public import (
    ZolProductSnapshot,
    parse_zol_product_html,
    validate_zol_product_url,
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


def test_jd_public_html_parser_maps_detailed_hardware_fields():
    page = """
    <html><head><title>RTX 4060 商品详情</title></head><body>
    <dl><dt>芯片厂商</dt><dd>NVIDIA</dd>
    <dt>显卡芯片</dt><dd>GeForce RTX 4060</dd>
    <dt>CUDA 核心</dt><dd>3072个</dd>
    <dt>显存容量</dt><dd>8GB</dd>
    <dt>显存位宽</dt><dd>128bit</dd>
    <dt>产品尺寸</dt><dd>243.5×119.75×45.5mm</dd></dl>
    </body></html>
    """
    _, parameters = parse_jd_product_html(page)
    assert parameters["chipset_vendor"] == "NVIDIA"
    assert parameters["gpu_chip"] == "GeForce RTX 4060"
    assert parameters["cuda_cores"] == "3072个"
    assert parameters["vram_gb"] == "8GB"
    assert parameters["memory_bus_bit"] == "128bit"
    assert parameters["dimensions"] == "243.5×119.75×45.5mm"


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


def test_product_detail_returns_platform_search_entries_without_fake_amounts():
    settings = Settings(_env_file=None, jd_public_fetch_enabled=False)
    detail = asyncio.run(get_product_detail("mb-msi-x870e-carbon", settings))
    assert detail.part.specs["chipset"] == "AMD X870E"
    assert {offer.platform for offer in detail.offers} == {"jd", "pdd"}
    assert all(offer.is_live is False for offer in detail.offers)
    assert all(offer.price is None for offer in detail.offers)
    assert all(offer.captured_at is None for offer in detail.offers)
    assert all(offer.status == "待联网" for offer in detail.offers)
    assert any(source.provider == "京东公开商品页" for source in detail.sources)


def test_zol_public_parser_extracts_board_parameters_and_platform_reference_price():
    page = """
    <html><head><title>华硕TUF GAMING B760M-PLUS D4重炮手</title></head><body>
    <ul class="param-important">
      <li><p title="Intel B760"><span>主芯片组：</span>Intel B760</p>
      <p title="4×DDR4 DIMM"><span>内存类型：</span>4×DDR4 DIMM</p>
      <p title="128GB"><span>最大内存容量：</span>128GB</p></li>
      <li><p title="Micro ATX板型"><span>主板板型：</span>Micro ATX板型</p>
      <p title="24.4×24.4cm"><span>外形尺寸：</span>24.4×24.4cm</p></li>
    </ul>
    <div class="detailed-parameters"><table>
      <tr><th><span>CPU插槽</span></th><td><span>LGA 1700</span><em>纠错</em></td></tr>
      <tr><th><span>M.2接口数量</span></th><td><span>2个</span></td></tr>
      <tr><th><span>SATA接口数量</span></th><td><span>4个</span></td></tr>
      <tr><th><span>存储接口</span></th><td><span>2×M.2接口，4×SATA III接口</span></td></tr>
      <tr><th><span>USB（内置）</span></th><td><span>1×USB3.2 Gen1 Type-C</span></td></tr>
      <tr><th><span>USB（背板）</span></th><td><span>4×USB3.2 Gen2接口</span></td></tr>
    </table></div>
    <div class="goods-card__price">参考报价：<span>￥1159</span></div>
    <div id="brand-seller-jd"><a href="https://union-click.jd.com/jdc?x=1">京东商城</a>
      <div class="price-cell"><span class="price">￥1159</span></div>
    </div>
    </body></html>
    """
    snapshot = parse_zol_product_html(page)
    assert snapshot.title and "B760M" in snapshot.title
    assert snapshot.parameters["chipset"] == "Intel B760"
    assert snapshot.parameters["memory_type"] == "DDR4"
    assert snapshot.parameters["max_memory_gb"] == 128
    assert snapshot.parameters["form_factor"] == "mATX"
    assert snapshot.parameters["socket"] == "LGA1700"
    assert snapshot.parameters["m2_slots"] == 2
    assert snapshot.parameters["sata_ports"] == 4
    assert snapshot.parameters["usb_header"] == "1×USB3.2 Gen1 Type-C"
    assert snapshot.parameters["usb_ports"] == "4×USB3.2 Gen2接口"
    assert snapshot.reference_price == 1159
    assert snapshot.jd_price == 1159
    assert snapshot.jd_seller == "京东商城"
    assert snapshot.jd_url == "https://union-click.jd.com/jdc?x=1"


def test_zol_url_validation_only_accepts_numeric_parameter_pages():
    assert validate_zol_product_url("https://detail.zol.com.cn/1441/1440076/param.shtml")
    for url in (
        "http://detail.zol.com.cn/1441/1440076/param.shtml",
        "https://detail.zol.com.cn/1441/1440076/param.shtml?x=1",
        "https://detail.zol.com.cn/1441/1440076/index.shtml",
        "https://detail.zol.com.cn.evil.example/1441/1440076/param.shtml",
    ):
        with pytest.raises(ValueError):
            validate_zol_product_url(url)


def test_product_detail_merges_zol_public_parameters_and_jd_reference_price(monkeypatch):
    async def fake_fetch(_url, _settings):
        return ZolProductSnapshot(
            title="华硕 TUF GAMING B760M-PLUS D4 重炮手",
            parameters={
                "chipset": "Intel B760",
                "socket": "LGA1700",
                "memory_type": "DDR4",
                "max_memory_gb": 128,
                "form_factor": "mATX",
            },
            reference_price=1159,
            jd_price=1159,
            jd_url="https://union-click.jd.com/jdc?x=1",
            jd_seller="京东商城",
        )

    monkeypatch.setattr(product_service, "fetch_zol_public_product", fake_fetch)
    detail = asyncio.run(
        get_product_detail(
            "mb-asus-tuf-b760m-plus-d4",
            Settings(_env_file=None, zol_public_fetch_enabled=True),
        )
    )
    assert detail.part.price == 1159
    assert detail.part.specs["socket"] == "LGA1700"
    jd_offer = next(offer for offer in detail.offers if offer.platform == "jd")
    pdd_offer = next(offer for offer in detail.offers if offer.platform == "pdd")
    assert jd_offer.price == 1159
    assert jd_offer.status == "公开参考价"
    assert jd_offer.seller == "京东商城"
    assert pdd_offer.price is None
    assert any(
        source.provider == "中关村在线公开参数页" and source.status == "public_reference"
        for source in detail.sources
    )


def test_product_detail_route_and_unknown_product():
    with TestClient(app) as client:
        response = client.get("/api/products/gpu-4070s")
        assert response.status_code == 200
        assert len(response.json()["offers"]) == 2
        assert response.json()["evidence"][0]["url"].startswith("https://vga.zol.com.cn/")
        missing = client.get("/api/products/not-found")
        assert missing.status_code == 404


def test_taobao_mcp_parser_keeps_live_price_store_and_parameters():
    part = next(part for part in fixture_parts() if part.id == "gpu-4070s")
    result = SimpleNamespace(
        structured_content={
            "title": "华硕 RTX 4070 SUPER",
            "price": "4299.00",
            "store_name": "华硕官方旗舰店",
            "product_id": "123456789012",
            "parameters": {"显存容量": "12GB", "显存位宽": "192bit"},
        },
        content=[],
    )
    parsed = parse_product_result(part, result, "123456789012")
    assert parsed.status == "live"
    assert parsed.offer is not None
    assert parsed.offer.price == 4299.0
    assert parsed.offer.seller == "华硕官方旗舰店"
    assert parsed.offer.is_live is True
    assert parsed.parameters["显存位宽"] == "192bit"
    assert parsed.parameters["memory_bus_bit"] == "192bit"


def test_taobao_mcp_parser_accepts_markdown_and_rejects_untrusted_reference():
    part = next(part for part in fixture_parts() if part.id == "gpu-4070s")
    result = SimpleNamespace(
        structured_content=None,
        content=[
            SimpleNamespace(
                type="text",
                text="商品标题：华硕 RTX 4070 SUPER\n店铺：华硕官方旗舰店\n价格：¥4299",
            )
        ],
    )
    parsed = parse_product_result(part, result, "https://detail.tmall.com/item.htm?id=123456789012")
    assert parsed.offer is not None and parsed.offer.is_live
    assert parsed.offer.seller == "华硕官方旗舰店"
    assert validate_product_reference("https://detail.tmall.com/item.htm?id=123456789012")
    with pytest.raises(ValueError):
        validate_product_reference("https://example.com/item?id=123456789012")


def test_realtime_mode_does_not_return_fixture_amounts_without_live_provider():
    settings = Settings(_env_file=None, realtime_prices_required=True)
    detail = asyncio.run(get_product_detail("gpu-4070s", settings))
    assert {offer.platform for offer in detail.offers} == {"jd", "pdd"}
    assert all(offer.price is None for offer in detail.offers)
    assert any(
        source.status == "unavailable" for source in detail.sources if source.kind == "price"
    )


def test_product_detail_keeps_taobao_parameters_when_price_is_unavailable(monkeypatch):
    async def fake_fetch(_part, _settings):
        return TaobaoMcpResult(
            title="淘宝商品参数",
            parameters={"memory_bus_bit": "128bit", "dimensions": "245mm"},
            note="已读取参数，价格暂不可用。",
            status="unavailable",
        )

    monkeypatch.setattr(product_service, "fetch_taobao_offer", fake_fetch)
    settings = Settings(
        _env_file=None,
        taobao_mcp_enabled=True,
        taobao_product_urls_json='{"gpu-4070s":"123456789012"}',
    )
    detail = asyncio.run(product_service.get_product_detail("gpu-4070s", settings))
    assert detail.part.specs["memory_bus_bit"] == "128bit"
    assert detail.part.specs["dimensions"] == "245mm"
    assert any(e.source == "淘宝 MCP" for e in detail.evidence)
