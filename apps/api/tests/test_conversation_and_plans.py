from app.domain import NeedProfile
from app.features.builds.planner import generate_plans
from app.features.builds.service import get_plan, save_plans
from app.features.conversations.service import append_message, create_conversation


def test_message_updates_structured_profile():
    conversation = create_conversation(NeedProfile())
    updated = append_message(conversation.id, "我预算 1.2 万，想要 AMD CPU、N卡，2K 游戏，水冷")
    assert updated.profile.budget == 12000
    assert updated.profile.cpu_brand == "amd"
    assert updated.profile.gpu_brand == "nvidia"
    assert updated.profile.cooling == "water"


def test_message_recognizes_war_thunder_as_game_use_case():
    conversation = create_conversation(NeedProfile())
    updated = append_message(conversation.id, "8000元玩战争雷霆的游戏主机")
    assert updated.profile.budget == 8000
    assert updated.profile.use_case == "游戏与日常"


def test_saved_plan_round_trip():
    plans = save_plans("conversation-test", NeedProfile(budget=9000))
    assert get_plan(plans[0].id).id == plans[0].id
    assert get_plan(plans[0].id).items


def test_over_budget_plan_is_explicitly_marked():
    plans = generate_plans(NeedProfile(budget=3000))
    assert any(issue.code == "BUDGET_OVER" for issue in plans[1].compatibility)


def test_low_budget_changes_selection_and_reports_minimum_complete_reference():
    plans = generate_plans(NeedProfile(budget=2500))
    assert all(plan.budget == 2500 for plan in plans)
    assert all(plan.total_price < 7000 for plan in plans)
    assert all(
        any(
            issue.code == "BUDGET_OVER" and "最低参考价" in issue.detail
            for issue in plan.compatibility
        )
        for plan in plans
    )
