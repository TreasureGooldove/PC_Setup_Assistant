from app.domain import NeedProfile
from app.features.builds.service import get_plan, save_plans
from app.features.conversations.service import append_message, create_conversation


def test_message_updates_structured_profile():
    conversation = create_conversation(NeedProfile())
    updated = append_message(conversation.id, "我预算 1.2 万，想要 AMD CPU、N卡，2K 游戏，水冷")
    assert updated.profile.budget == 12000
    assert updated.profile.cpu_brand == "amd"
    assert updated.profile.gpu_brand == "nvidia"
    assert updated.profile.cooling == "water"


def test_saved_plan_round_trip():
    plans = save_plans("conversation-test", NeedProfile(budget=9000))
    assert get_plan(plans[0].id).id == plans[0].id
    assert get_plan(plans[0].id).items
