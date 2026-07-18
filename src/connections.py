"""Multi-Traveller coordination for the MgT 2022 Connections Rule.

``GameSession`` deliberately remains the single-character step engine. A
``PartySession`` composes two or more of those sessions, records career events,
and coordinates the two-sided proposal/acceptance transaction that grants a
connection. This keeps party concerns out of career term routing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from pydantic import BaseModel

from src.character import AssociateType, Character
from src.character_summary import CharacterSummary
from src.engine import GameSession
from src.terms.base import SubmitResult


CONNECTION_RELATIONSHIPS = {
    AssociateType.CONTACT,
    AssociateType.ALLY,
    AssociateType.RIVAL,
}
MAX_CONNECTIONS = 2


class ConnectionEvent(BaseModel):
    """A career event that can be shared with another Traveller."""

    id: str
    traveller_id: str
    description: str
    term_label: str | None = None


class ConnectionProposal(BaseModel):
    """One Traveller's offer to involve another in a recorded event."""

    id: str
    event_id: str
    proposer_id: str
    partner_id: str
    proposer_skill: str
    proposer_relationship: AssociateType
    narrative: str


class ConnectionRecord(BaseModel):
    """An accepted connection and both Travellers' chosen benefits."""

    id: str
    event_id: str
    traveller_ids: tuple[str, str]
    skills: dict[str, str]
    relationships: dict[str, AssociateType]
    narrative: str


@dataclass
class PartyMember:
    id: str
    session: GameSession
    events: list[ConnectionEvent] = field(default_factory=list)

    @property
    def character(self) -> Character:
        return self.session.character


class PartySession:
    """Coordinate independent character sessions and their shared events."""

    def __init__(
        self,
        traveller_names: list[str],
        *,
        anagathics_enabled: bool = False,
    ) -> None:
        names = [name.strip() for name in traveller_names]
        if len(names) < 2:
            raise ValueError("A party needs at least two Travellers.")
        if any(not name for name in names):
            raise ValueError("Every Traveller needs a name.")
        if len({name.casefold() for name in names}) != len(names):
            raise ValueError("Traveller names must be unique within a party.")

        self.members: dict[str, PartyMember] = {}
        for name in names:
            session = GameSession(anagathics_enabled=anagathics_enabled)
            session.character.name = name
            member_id = str(uuid4())
            self.members[member_id] = PartyMember(id=member_id, session=session)

        self.proposals: dict[str, ConnectionProposal] = {}
        self.connections: list[ConnectionRecord] = []

    def start(self) -> dict[str, SubmitResult]:
        """Start every member's independent creation flow."""
        return {
            member_id: member.session.start()
            for member_id, member in self.members.items()
        }

    def submit(
        self,
        traveller_id: str,
        player_input: dict | None = None,
    ) -> SubmitResult:
        """Advance one Traveller and retain any career event they resolve."""
        member = self._member(traveller_id)
        result = member.session.submit(player_input)
        for step in result.resolved_steps:
            if step.step_id == "events_roll":
                member.events.append(
                    ConnectionEvent(
                        id=str(uuid4()),
                        traveller_id=traveller_id,
                        description=step.description,
                        term_label=step.term_label,
                    )
                )
        return result

    def events_for(self, traveller_id: str) -> list[ConnectionEvent]:
        """Return the career events available for that Traveller to share."""
        return list(self._member(traveller_id).events)

    def character_summaries(self) -> dict[str, dict]:
        """Serialize every party member without exposing engine internals."""
        return {
            traveller_id: CharacterSummary.from_character(member.character).model_dump()
            for traveller_id, member in self.members.items()
        }

    def propose_connection(
        self,
        *,
        proposer_id: str,
        partner_id: str,
        event_id: str,
        skill: str,
        relationship: AssociateType,
        narrative: str = "",
    ) -> ConnectionProposal:
        """Record one side's agreement to share an event.

        No character state changes until the named partner explicitly accepts.
        """
        proposer = self._member(proposer_id)
        self._member(partner_id)
        self._validate_pair(proposer_id, partner_id)
        event = self._event(proposer_id, event_id)
        proposer.character.validate_connection_skill(skill)
        self._validate_relationship(relationship)

        proposal = ConnectionProposal(
            id=str(uuid4()),
            event_id=event_id,
            proposer_id=proposer_id,
            partner_id=partner_id,
            proposer_skill=skill.strip(),
            proposer_relationship=relationship,
            narrative=narrative.strip() or event.description,
        )
        self.proposals[proposal.id] = proposal
        return proposal

    def accept_connection(
        self,
        proposal_id: str,
        *,
        partner_id: str,
        skill: str,
        relationship: AssociateType,
    ) -> ConnectionRecord:
        """Accept a proposal, atomically granting both connection benefits."""
        proposal = self.proposals.get(proposal_id)
        if proposal is None:
            raise ValueError("Unknown connection proposal.")
        if proposal.partner_id != partner_id:
            raise ValueError("Only the proposed partner can accept this connection.")

        self._validate_pair(proposal.proposer_id, partner_id)
        proposer = self._member(proposal.proposer_id)
        partner = self._member(partner_id)

        # Validate the complete transaction before mutating either character.
        proposer_skill = proposer.character.validate_connection_skill(
            proposal.proposer_skill
        )
        partner_skill = partner.character.validate_connection_skill(skill)
        self._validate_relationship(proposal.proposer_relationship)
        self._validate_relationship(relationship)

        proposer.character.grant_connection_skill(proposer_skill)
        partner.character.grant_connection_skill(partner_skill)
        proposer.character.add_associate(
            partner.character.name,
            proposal.proposer_relationship,
            description=proposal.narrative,
            source_event=self._event(
                proposal.proposer_id, proposal.event_id
            ).description,
        )
        partner.character.add_associate(
            proposer.character.name,
            relationship,
            description=proposal.narrative,
            source_event=self._event(
                proposal.proposer_id, proposal.event_id
            ).description,
        )

        record = ConnectionRecord(
            id=proposal.id,
            event_id=proposal.event_id,
            traveller_ids=(proposal.proposer_id, partner_id),
            skills={
                proposal.proposer_id: proposer_skill,
                partner_id: partner_skill,
            },
            relationships={
                proposal.proposer_id: proposal.proposer_relationship,
                partner_id: relationship,
            },
            narrative=proposal.narrative,
        )
        self.connections.append(record)
        del self.proposals[proposal_id]
        return record

    def _member(self, traveller_id: str) -> PartyMember:
        try:
            return self.members[traveller_id]
        except KeyError as exc:
            raise ValueError("Unknown Traveller in this party.") from exc

    def _event(self, traveller_id: str, event_id: str) -> ConnectionEvent:
        for event in self._member(traveller_id).events:
            if event.id == event_id:
                return event
        raise ValueError("The selected event does not belong to that Traveller.")

    def _connected_partners(self, traveller_id: str) -> set[str]:
        partners: set[str] = set()
        for connection in self.connections:
            if traveller_id not in connection.traveller_ids:
                continue
            partners.update(connection.traveller_ids)
        partners.discard(traveller_id)
        return partners

    def _validate_pair(self, proposer_id: str, partner_id: str) -> None:
        if proposer_id == partner_id:
            raise ValueError("A Traveller cannot connect an event to themselves.")
        self._member(proposer_id)
        self._member(partner_id)
        proposer_partners = self._connected_partners(proposer_id)
        partner_partners = self._connected_partners(partner_id)
        if partner_id in proposer_partners:
            raise ValueError("Each connection must be with a different Traveller.")
        if len(proposer_partners) >= MAX_CONNECTIONS:
            raise ValueError("A Traveller can gain at most two connection skills.")
        if len(partner_partners) >= MAX_CONNECTIONS:
            raise ValueError("The proposed partner already has two connections.")

    @staticmethod
    def _validate_relationship(relationship: AssociateType) -> None:
        if relationship not in CONNECTION_RELATIONSHIPS:
            raise ValueError(
                "A connection relationship must be Contact, Ally, or Rival."
            )
