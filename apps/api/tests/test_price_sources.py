from app.features.builds.price_sources import (
    ConfiguredMarketplaceProvider,
    enabled_marketplaces,
    normalize_offer,
)


def test_normalize_pdd_price_keeps_coupon_and_source_fields():
    offer = normalize_offer(
        "gpu-1",
        "pdd",
        {
            "goods_sign": "abc",
            "min_normal_price": 359900,
            "min_group_price": 329900,
            "coupon_discount": 30000,
            "mall_name": "示例店铺",
        },
    )
    assert offer is not None
    assert offer.price == 2999.0
    assert offer.discount_price == 3299.0
    assert offer.list_price == 3599.0
    assert offer.sku == "abc"
    assert offer.source == "拼多多多多客"
    assert offer.coupon_note == "优惠约 ¥300.00"


def test_normalize_taobao_and_jd_price_fields():
    taobao = normalize_offer(
        "cpu-1",
        "taobao",
        {"item_id": 123, "reserve_price": "1899", "zk_final_price": "1699"},
    )
    jd = normalize_offer("cpu-1", "jd", {"sku_id": 456, "price": "1799"})
    assert taobao is not None and taobao.price == 1699.0
    assert taobao.sku == "123"
    assert jd is not None and jd.price == 1799.0
    assert jd.sku == "456"


def test_normalize_taobao_keeps_store_name():
    offer = normalize_offer(
        "cpu-1",
        "taobao",
        {"item_id": 123, "price": "1699", "store_name": "测试旗舰店"},
    )
    assert offer is not None
    assert offer.seller == "测试旗舰店"


def test_marketplace_credentials_are_all_or_nothing():
    env = {
        "JD_APP_KEY": "key",
        "JD_APP_SECRET": "secret",
        "JD_PID": "pid",
        "PDD_CLIENT_ID": "client",
        "PDD_CLIENT_SECRET": "secret",
        "PDD_PID": "pid",
    }
    assert enabled_marketplaces(env) == ["jd", "pdd"]
    assert ConfiguredMarketplaceProvider("taobao", env).enabled is False
