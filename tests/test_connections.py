import pytest
from fastapi.testclient import TestClient

from src.api import app, party_sessions
from src.character import AssociateType, Character, Characteristic, Skill
from src.connections import ConnectionEvent, PartySession
from src.terms.base import (
    LifepathPhase,
    LifepathProgress,
    StepPrompt,
    StepType,
    SubmitResult,
)


def party_with_events(*names: str) -> tuple[PartySession, list[str]]:
    party = PartySession(list(names))
    ids = list(party.members)
    for index, traveller_id in enumerate(ids):
        party.members[traveller_id].events.append(
            ConnectionEvent(
                id=f"event-{index}",
                traveller_id=traveller_id,
                description=f"Shared event {index}",
                term_label="Scout — Term 1",
            )
        )
    return party, ids


def connect(
    party: PartySession,
    proposer_id: str,
    partner_id: str,
    *,
    event_id: str,
    proposer_skill: str = "Pilot",
    partner_skill: str = "Engineer",
):
    proposal = party.propose_connection(
        proposer_id=proposer_id,
        partner_id=partner_id,
        event_id=event_id,
        skill=proposer_skill,
        relationship=AssociateType.ALLY,
        narrative="They escaped the patrol together.",
    )
    return party.accept_connection(
        proposal.id,
        partner_id=partner_id,
        skill=partner_skill,
        relationship=AssociateType.CONTACT,
    )


def test_party_requires_unique_named_travellers() -> None:
    with pytest.raises(ValueError, match="at least two"):
        PartySession(["Solo"])
    with pytest.raises(ValueError, match="unique"):
        PartySession(["Alex", "alex"])


def test_connection_requires_partner_acceptance_before_mutating_characters() -> None:
    party, (alex_id, blair_id) = party_with_events("Alex", "Blair")

    proposal = party.propose_connection(
        proposer_id=alex_id,
        partner_id=blair_id,
        event_id="event-0",
        skill="Pilot",
        relationship=AssociateType.ALLY,
        narrative="They escaped the patrol together.",
    )

    assert not party.members[alex_id].character.has_skill("Pilot")
    assert not party.members[blair_id].character.associates

    record = party.accept_connection(
        proposal.id,
        partner_id=blair_id,
        skill="Engineer",
        relationship=AssociateType.CONTACT,
    )

    alex = party.members[alex_id].character
    blair = party.members[blair_id].character
    assert alex.skills["Pilot"].base_rank == 1
    assert blair.skills["Engineer"].base_rank == 1
    assert alex.associates[0].name == "Blair"
    assert alex.associates[0].type == AssociateType.ALLY
    assert blair.associates[0].name == "Alex"
    assert blair.associates[0].type == AssociateType.CONTACT
    assert record.narrative == "They escaped the patrol together."


def test_only_named_partner_can_accept() -> None:
    party, (alex_id, blair_id, casey_id) = party_with_events(
        "Alex", "Blair", "Casey"
    )
    proposal = party.propose_connection(
        proposer_id=alex_id,
        partner_id=blair_id,
        event_id="event-0",
        skill="Pilot",
        relationship=AssociateType.ALLY,
    )

    with pytest.raises(ValueError, match="Only the proposed partner"):
        party.accept_connection(
            proposal.id,
            partner_id=casey_id,
            skill="Engineer",
            relationship=AssociateType.CONTACT,
        )


@pytest.mark.parametrize("skill", ["Jack-of-all-Trades", "jack of all trades"])
def test_connections_exclude_jack_of_all_trades(skill: str) -> None:
    character = Character(name="Alex", characteristics={}, skills={})

    with pytest.raises(ValueError, match="Jack-of-all-Trades"):
        character.grant_connection_skill(skill)


def test_connection_skill_cannot_exceed_level_three() -> None:
    character = Character(
        name="Alex",
        characteristics={},
        skills={"Pilot": Skill(name="Pilot", base_rank=3, specialties={})},
    )

    with pytest.raises(ValueError, match="above level 3"):
        character.grant_connection_skill("Pilot")


def test_connection_skill_can_raise_level_two_to_three() -> None:
    character = Character(
        name="Alex",
        characteristics={},
        skills={"Pilot": Skill(name="Pilot", base_rank=2, specialties={})},
    )

    character.grant_connection_skill("Pilot")

    assert character.skills["Pilot"].base_rank == 3


def test_connection_respects_total_skill_budget() -> None:
    character = Character(
        name="Alex",
        characteristics={
            "Intelligence": Characteristic(name="Intelligence", value=0),
            "Education": Characteristic(name="Education", value=0),
        },
        skills={},
    )

    with pytest.raises(ValueError, match="total skill-level cap"):
        character.grant_connection_skill("Pilot")


def test_each_connection_requires_a_different_partner_and_maximum_is_two() -> None:
    party, (alex_id, blair_id, casey_id, devon_id) = party_with_events(
        "Alex", "Blair", "Casey", "Devon"
    )
    connect(party, alex_id, blair_id, event_id="event-0")

    with pytest.raises(ValueError, match="different Traveller"):
        party.propose_connection(
            proposer_id=alex_id,
            partner_id=blair_id,
            event_id="event-0",
            skill="Recon",
            relationship=AssociateType.RIVAL,
        )

    connect(
        party,
        alex_id,
        casey_id,
        event_id="event-0",
        proposer_skill="Recon",
        partner_skill="Medic",
    )

    with pytest.raises(ValueError, match="at most two"):
        party.propose_connection(
            proposer_id=alex_id,
            partner_id=devon_id,
            event_id="event-0",
            skill="Survival",
            relationship=AssociateType.CONTACT,
        )


def test_enemy_is_not_a_connections_relationship() -> None:
    party, (alex_id, blair_id) = party_with_events("Alex", "Blair")

    with pytest.raises(ValueError, match="Contact, Ally, or Rival"):
        party.propose_connection(
            proposer_id=alex_id,
            partner_id=blair_id,
            event_id="event-0",
            skill="Pilot",
            relationship=AssociateType.ENEMY,
        )


def test_party_submit_records_resolved_career_events() -> None:
    party = PartySession(["Alex", "Blair"])
    traveller_id = next(iter(party.members))
    member = party.members[traveller_id]
    member.session.submit = lambda player_input: SubmitResult(
        resolved_steps=[
            StepPrompt(
                step_id="events_roll",
                step_type=StepType.AUTOMATIC,
                description="Event (2d6 = 7): A shared discovery.",
                term_label="Scout — Term 1",
            )
        ],
        next_prompt=None,
        character={},
        progress=LifepathProgress(
            phase=LifepathPhase.CAREER,
            phase_index=3,
        ),
    )

    party.submit(traveller_id)

    assert party.events_for(traveller_id)[0].description.endswith(
        "A shared discovery."
    )


def test_party_connection_api_exposes_two_sided_flow() -> None:
    client = TestClient(app)
    start_response = client.post(
        "/api/party/start",
        json={"traveller_names": ["Alex", "Blair"]},
    )
    assert start_response.status_code == 200
    started = start_response.json()
    party_id = started["party_id"]
    alex_id, blair_id = [member["traveller_id"] for member in started["members"]]
    party_sessions[party_id].members[alex_id].events.append(
        ConnectionEvent(
            id="api-event",
            traveller_id=alex_id,
            description="Event: Alex and Blair crossed the frontier.",
        )
    )

    propose_response = client.post(
        "/api/party/connections/propose",
        json={
            "party_id": party_id,
            "proposer_id": alex_id,
            "partner_id": blair_id,
            "event_id": "api-event",
            "skill": "Pilot",
            "relationship": "ally",
            "narrative": "They crossed the frontier together.",
        },
    )
    assert propose_response.status_code == 200

    accept_response = client.post(
        "/api/party/connections/accept",
        json={
            "party_id": party_id,
            "proposal_id": propose_response.json()["id"],
            "partner_id": blair_id,
            "skill": "Engineer",
            "relationship": "contact",
        },
    )

    assert accept_response.status_code == 200
    characters = accept_response.json()["characters"]
    assert characters[alex_id]["skills"]["Pilot"]["base_rank"] == 1
    assert characters[blair_id]["associates"][0]["name"] == "Alex"
