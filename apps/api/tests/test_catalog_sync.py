import asyncio
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.domain import Part, PartCategory
from app.features.builds.catalog import fixture_parts
from app.features.catalog_sync.service import (
    CATALOG_URLS,
    catalog_sync_status,
    find_catalog_part,
    mark_sync_queued,
    parse_zol_catalog_html,
    query_catalog,
    save_catalog_parts,
    sync_catalog,
    validate_catalog_url,
)
from app.features.jobs.service import process_one
from app.main import app
from app.queue import JobQueue


def test_every_fixture_category_has_at_least_twelve_candidates():
    parts = fixture_parts()
    ids = [part.id for part in parts]
    assert len(ids) == len(set(ids))
    for category in PartCategory:
        candidates = [part for part in parts if part.category == category]
        assert len(candidates) >= 12, category.value

    gpu_vendors = {part.brand for part in parts if part.category == PartCategory.GPU}
    assert {"华硕 ASUS", "微星 MSI", "技嘉 GIGABYTE", "七彩虹 COLORFUL"} <= gpu_vendors


def test_zol_catalog_parser_extracts_vendor_price_image_and_specs():
    page = """
    <div class="pic-mode-box"><ul id="J_PicMode">
      <li data-follow-id="p2034278">
        <a href="/vga/index2034278.shtml" class="pic">
          <img width="220" height="165" .src="https://example.invalid/gpu.jpg" alt="华硕显卡">
        </a>
        <h3><a href="/vga/index2034278.shtml">华硕 TUF RTX 5070 O12G GAMING
          <span>12GB GDDR7 192bit 三风扇</span></a></h3>
        <div class="price-row"><b class="price-type">7,699</b></div>
      </li>
    </ul></div>
    """
    parts = parse_zol_catalog_html(page, PartCategory.GPU)
    assert len(parts) == 1
    part = parts[0]
    assert part.id == "zol-gpu-2034278"
    assert part.brand == "华硕"
    assert part.price == 7699
    assert part.image_url == "https://example.invalid/gpu.jpg"
    assert part.url == "https://detail.zol.com.cn/vga/index2034278.shtml"
    assert part.specs["catalog_kind"] == "RTX 5070"
    assert part.specs["vram_gb"] == 12
    assert part.specs["memory_type"] == "GDDR7"
    assert part.specs["memory_bus_bit"] == 192


@pytest.mark.parametrize(
    ("name", "expected_brand"),
    [
        ("瀚铠Radeon RX 9070 XT 超合金PRO", "瀚铠"),
        ("蓝戟Intel Arc A380 Photon 6G OC", "蓝戟"),
        ("万丽雪狐GeForce RTX 5070 OC 12GB", "万丽"),
    ],
)
def test_zol_catalog_parser_keeps_vendor_name_separate_from_chip_brand(
    name: str, expected_brand: str
):
    page = f"""
    <ul id="J_PicMode"><li data-follow-id="p88">
      <h3><a href="/vga/index88.shtml">{name}<span>12GB GDDR7</span></a></h3>
      <div class="price-row"><b class="price-type">4,999</b></div>
    </li></ul>
    """
    assert parse_zol_catalog_html(page, PartCategory.GPU)[0].brand == expected_brand


def test_catalog_url_is_fixed_allowlist_only():
    assert validate_catalog_url(PartCategory.GPU, CATALOG_URLS[PartCategory.GPU])
    with pytest.raises(ValueError):
        validate_catalog_url(PartCategory.GPU, "https://detail.zol.com.cn/vga/new.html")
    with pytest.raises(ValueError):
        validate_catalog_url(PartCategory.GPU, "https://example.com/vga/")
    with pytest.raises(ValueError):
        validate_catalog_url(PartCategory.GPU, "https://detail.zol.com.cn/vga/?redirect=x")


def test_queued_catalog_without_cached_capture_remains_stale():
    mark_sync_queued(PartCategory.GPU)
    status = catalog_sync_status(PartCategory.GPU, Settings(catalog_sync_ttl_hours=12))
    assert status["status"] == "queued"
    assert status["stale"] is True


def test_unexpected_sync_failure_updates_status_and_keeps_fallback(monkeypatch):
    async def fail_fetch(*_args, **_kwargs):
        raise RuntimeError("parser changed")

    monkeypatch.setattr(
        "app.features.catalog_sync.service.fetch_zol_catalog",
        fail_fetch,
    )
    with pytest.raises(RuntimeError):
        asyncio.run(sync_catalog(PartCategory.GPU, Settings()))
    status = catalog_sync_status(PartCategory.GPU, Settings())
    assert status["status"] == "unavailable"
    assert status["stale"] is True
    assert int(query_catalog(PartCategory.GPU)["total"]) >= 12


def test_cached_catalog_merges_filters_and_keeps_specific_vendor():
    cached = Part(
        id="zol-gpu-99",
        category=PartCategory.GPU,
        name="TUF RTX 5070 O12G GAMING",
        brand="华硕 ASUS",
        price=7699,
        source="ZOL 公开产品目录",
        specs={
            "catalog_kind": "RTX 5070",
            "vram_gb": 12,
            "memory_type": "GDDR7",
            "memory_bus_bit": 192,
        },
    )
    save_catalog_parts(
        PartCategory.GPU,
        [cached],
        Settings(catalog_sync_ttl_hours=12),
    )
    result = query_catalog(
        PartCategory.GPU,
        brand="华硕 ASUS",
        kind="RTX 5070",
        min_price=7000,
        max_price=8000,
    )
    assert [item["id"] for item in result["items"]] == ["zol-gpu-99"]
    assert find_catalog_part("zol-gpu-99") == cached
    assert any(item["value"] == "华硕 ASUS" for item in result["facets"]["brands"])


def test_twenty_concurrent_catalog_reads_are_consistent():
    def read_count(_: int) -> int:
        return int(query_catalog(PartCategory.COOLING)["total"])

    with ThreadPoolExecutor(max_workers=8) as pool:
        counts = list(pool.map(read_count, range(20)))
    assert len(set(counts)) == 1
    assert counts[0] >= 12


def test_catalog_refresh_job_uses_persistent_queue(monkeypatch):
    async def fake_sync(category: PartCategory):
        assert category == PartCategory.GPU
        return {"category": category.value, "item_count": 17}

    monkeypatch.setattr("app.features.jobs.service.sync_catalog", fake_sync)
    queue = JobQueue()
    first = queue.enqueue("refresh_catalog", {"category": "gpu"}, "catalog-job")
    second = queue.enqueue("refresh_catalog", {"category": "gpu"}, "catalog-job")
    assert first.id == second.id
    assert asyncio.run(process_one(queue)) is True
    completed = queue.get(first.id)
    assert completed is not None
    assert completed.status == "completed"
    assert completed.result == {"category": "gpu", "item_count": 17}


def test_completed_bucket_refresh_does_not_reset_sync_state_to_queued():
    cached = Part(
        id="zol-gpu-completed",
        category=PartCategory.GPU,
        name="已缓存显卡",
        brand="测试厂商",
        price=3999,
        source="ZOL 公开产品目录",
        specs={"catalog_kind": "RTX 5070"},
    )
    with TestClient(app) as client:
        first = client.post("/api/catalog/gpu/refresh")
        assert first.status_code == 202
        job_id = first.json()["id"]
        JobQueue().complete(job_id, {"category": "gpu", "item_count": 1})
        save_catalog_parts(PartCategory.GPU, [cached], Settings())

        second = client.post("/api/catalog/gpu/refresh")
        assert second.json()["id"] == job_id
        assert second.json()["status"] == "completed"
        assert client.get("/api/catalog/gpu").json()["sync"]["status"] == "completed"
