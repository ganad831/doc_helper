"""Tests for override entity."""

import pytest
from uuid import uuid4

from doc_helper.domain.override.override_entity import Override
from doc_helper.domain.override.override_ids import OverrideId
from doc_helper.domain.override.override_state import OverrideState
from doc_helper.domain.project.project_ids import ProjectId
from doc_helper.domain.schema.schema_ids import FieldDefinitionId


class TestOverrideId:
    """Tests for OverrideId."""

    def test_create_override_id(self) -> None:
        """OverrideId should be created with UUID."""
        uid = uuid4()
        override_id = OverrideId(uid)
        assert override_id.value == uid

    def test_override_id_requires_uuid(self) -> None:
        """OverrideId should require UUID value."""
        with pytest.raises(TypeError, match="OverrideId value must be a UUID"):
            OverrideId("not-a-uuid")  # type: ignore

    def test_override_id_equality(self) -> None:
        """OverrideId should support equality comparison."""
        uid = uuid4()
        id1 = OverrideId(uid)
        id2 = OverrideId(uid)
        id3 = OverrideId(uuid4())
        assert id1 == id2
        assert id1 != id3

    def test_override_id_hashable(self) -> None:
        """OverrideId should be hashable."""
        id1 = OverrideId(uuid4())
        id2 = OverrideId(uuid4())
        id_set = {id1, id2, id1}
        assert len(id_set) == 2

    def test_override_id_str(self) -> None:
        """OverrideId should convert to string."""
        uid = uuid4()
        override_id = OverrideId(uid)
        assert str(override_id) == str(uid)

    def test_override_id_repr(self) -> None:
        """OverrideId should have repr."""
        uid = uuid4()
        override_id = OverrideId(uid)
        assert repr(override_id) == f"OverrideId({uid!r})"

    def test_override_id_immutable(self) -> None:
        """OverrideId should be immutable."""
        override_id = OverrideId(uuid4())
        with pytest.raises(Exception):  # FrozenInstanceError
            override_id.value = uuid4()  # type: ignore


class TestOverride:
    """Tests for Override entity."""

    def test_create_override(self) -> None:
        """Override should be created with required fields."""
        override = Override(
            id=OverrideId(uuid4()),
            project_id=ProjectId(uuid4()),
            field_id=FieldDefinitionId("total"),
            override_value=1600,
            original_value=1500,
        )
        assert override.field_id == FieldDefinitionId("total")
        assert override.override_value == 1600
        assert override.original_value == 1500
        assert override.state == OverrideState.PENDING
        assert override.reason is None
        assert override.conflict_type is None

    def test_create_override_with_reason(self) -> None:
        """Override should accept optional reason."""
        override = Override(
            id=OverrideId(uuid4()),
            project_id=ProjectId(uuid4()),
            field_id=FieldDefinitionId("total"),
            override_value=1600,
            original_value=1500,
            reason="Manual adjustment",
        )
        assert override.reason == "Manual adjustment"

    def test_create_override_with_state(self) -> None:
        """Override should accept initial state."""
        override = Override(
            id=OverrideId(uuid4()),
            project_id=ProjectId(uuid4()),
            field_id=FieldDefinitionId("total"),
            override_value=1600,
            original_value=1500,
            state=OverrideState.ACCEPTED,
        )
        assert override.state == OverrideState.ACCEPTED

    def test_override_requires_project_id(self) -> None:
        """Override should require ProjectId."""
        with pytest.raises(TypeError, match="project_id must be a ProjectId"):
            Override(
                id=OverrideId(uuid4()),
                project_id="invalid",  # type: ignore
                field_id=FieldDefinitionId("total"),
                override_value=1600,
                original_value=1500,
            )

    def test_override_requires_field_definition_id(self) -> None:
        """Override should require FieldDefinitionId."""
        with pytest.raises(TypeError, match="field_id must be a FieldDefinitionId"):
            Override(
                id=OverrideId(uuid4()),
                project_id=ProjectId(uuid4()),
                field_id="total",  # type: ignore
                override_value=1600,
                original_value=1500,
            )

    def test_override_requires_override_state(self) -> None:
        """Override should require OverrideState."""
        with pytest.raises(TypeError, match="state must be an OverrideState"):
            Override(
                id=OverrideId(uuid4()),
                project_id=ProjectId(uuid4()),
                field_id=FieldDefinitionId("total"),
                override_value=1600,
                original_value=1500,
                state="pending",  # type: ignore
            )

    def test_accept_pending_override(self) -> None:
        """accept() should transition PENDING → ACCEPTED."""
        override = Override(
            id=OverrideId(uuid4()),
            project_id=ProjectId(uuid4()),
            field_id=FieldDefinitionId("total"),
            override_value=1600,
            original_value=1500,
            state=OverrideState.PENDING,
        )
        override.accept()
        assert override.state == OverrideState.ACCEPTED

    def test_accept_non_pending_raises(self) -> None:
        """accept() should raise if not PENDING."""
        override = Override(
            id=OverrideId(uuid4()),
            project_id=ProjectId(uuid4()),
            field_id=FieldDefinitionId("total"),
            override_value=1600,
            original_value=1500,
            state=OverrideState.ACCEPTED,
        )
        with pytest.raises(ValueError, match="Cannot accept override in state accepted"):
            override.accept()

    def test_accept_touches_entity(self) -> None:
        """accept() should update modified timestamp."""
        import time

        override = Override(
            id=OverrideId(uuid4()),
            project_id=ProjectId(uuid4()),
            field_id=FieldDefinitionId("total"),
            override_value=1600,
            original_value=1500,
        )
        original_modified = override.modified_at
        time.sleep(0.001)
        override.accept()
        assert override.modified_at > original_modified

    def test_mark_synced_accepted_override(self) -> None:
        """mark_synced() should transition ACCEPTED → SYNCED."""
        override = Override(
            id=OverrideId(uuid4()),
            project_id=ProjectId(uuid4()),
            field_id=FieldDefinitionId("total"),
            override_value=1600,
            original_value=1500,
            state=OverrideState.ACCEPTED,
        )
        override.mark_synced()
        assert override.state == OverrideState.SYNCED

    def test_mark_synced_non_accepted_raises(self) -> None:
        """mark_synced() should raise if not ACCEPTED."""
        override = Override(
            id=OverrideId(uuid4()),
            project_id=ProjectId(uuid4()),
            field_id=FieldDefinitionId("total"),
            override_value=1600,
            original_value=1500,
            state=OverrideState.PENDING,
        )
        with pytest.raises(ValueError, match="Cannot sync override in state pending"):
            override.mark_synced()

    def test_mark_synced_touches_entity(self) -> None:
        """mark_synced() should update modified timestamp."""
        import time

        override = Override(
            id=OverrideId(uuid4()),
            project_id=ProjectId(uuid4()),
            field_id=FieldDefinitionId("total"),
            override_value=1600,
            original_value=1500,
            state=OverrideState.ACCEPTED,
        )
        original_modified = override.modified_at
        time.sleep(0.001)
        override.mark_synced()
        assert override.modified_at > original_modified

    def test_state_machine_flow(self) -> None:
        """Override should follow state machine: PENDING → ACCEPTED → SYNCED."""
        override = Override(
            id=OverrideId(uuid4()),
            project_id=ProjectId(uuid4()),
            field_id=FieldDefinitionId("total"),
            override_value=1600,
            original_value=1500,
        )
        assert override.is_pending

        override.accept()
        assert override.is_accepted

        override.mark_synced()
        assert override.is_synced

    def test_update_reason(self) -> None:
        """update_reason() should update reason."""
        override = Override(
            id=OverrideId(uuid4()),
            project_id=ProjectId(uuid4()),
            field_id=FieldDefinitionId("total"),
            override_value=1600,
            original_value=1500,
        )
        override.update_reason("New reason")
        assert override.reason == "New reason"

    def test_update_reason_to_none(self) -> None:
        """update_reason() should allow None to clear."""
        override = Override(
            id=OverrideId(uuid4()),
            project_id=ProjectId(uuid4()),
            field_id=FieldDefinitionId("total"),
            override_value=1600,
            original_value=1500,
            reason="Old reason",
        )
        override.update_reason(None)
        assert override.reason is None

    def test_update_reason_requires_string(self) -> None:
        """update_reason() should require string or None."""
        override = Override(
            id=OverrideId(uuid4()),
            project_id=ProjectId(uuid4()),
            field_id=FieldDefinitionId("total"),
            override_value=1600,
            original_value=1500,
        )
        with pytest.raises(TypeError, match="reason must be a string or None"):
            override.update_reason(123)  # type: ignore

    def test_mark_conflict(self) -> None:
        """mark_conflict() should set conflict_type."""
        override = Override(
            id=OverrideId(uuid4()),
            project_id=ProjectId(uuid4()),
            field_id=FieldDefinitionId("total"),
            override_value=1600,
            original_value=1500,
        )
        override.mark_conflict("formula")
        assert override.conflict_type == "formula"
        assert override.has_conflict

    def test_mark_conflict_requires_string(self) -> None:
        """mark_conflict() should require string."""
        override = Override(
            id=OverrideId(uuid4()),
            project_id=ProjectId(uuid4()),
            field_id=FieldDefinitionId("total"),
            override_value=1600,
            original_value=1500,
        )
        with pytest.raises(TypeError, match="conflict_type must be a string"):
            override.mark_conflict(123)  # type: ignore

    def test_mark_conflict_cannot_be_empty(self) -> None:
        """mark_conflict() should reject empty string."""
        override = Override(
            id=OverrideId(uuid4()),
            project_id=ProjectId(uuid4()),
            field_id=FieldDefinitionId("total"),
            override_value=1600,
            original_value=1500,
        )
        with pytest.raises(ValueError, match="conflict_type cannot be empty"):
            override.mark_conflict("   ")

    def test_clear_conflict(self) -> None:
        """clear_conflict() should clear conflict_type."""
        override = Override(
            id=OverrideId(uuid4()),
            project_id=ProjectId(uuid4()),
            field_id=FieldDefinitionId("total"),
            override_value=1600,
            original_value=1500,
            conflict_type="formula",
        )
        override.clear_conflict()
        assert override.conflict_type is None
        assert not override.has_conflict

    def test_is_pending_property(self) -> None:
        """is_pending should reflect current state."""
        override = Override(
            id=OverrideId(uuid4()),
            project_id=ProjectId(uuid4()),
            field_id=FieldDefinitionId("total"),
            override_value=1600,
            original_value=1500,
            state=OverrideState.PENDING,
        )
        assert override.is_pending is True
        assert override.is_accepted is False
        assert override.is_synced is False

    def test_is_accepted_property(self) -> None:
        """is_accepted should reflect current state."""
        override = Override(
            id=OverrideId(uuid4()),
            project_id=ProjectId(uuid4()),
            field_id=FieldDefinitionId("total"),
            override_value=1600,
            original_value=1500,
            state=OverrideState.ACCEPTED,
        )
        assert override.is_pending is False
        assert override.is_accepted is True
        assert override.is_synced is False

    def test_is_synced_property(self) -> None:
        """is_synced should reflect current state."""
        override = Override(
            id=OverrideId(uuid4()),
            project_id=ProjectId(uuid4()),
            field_id=FieldDefinitionId("total"),
            override_value=1600,
            original_value=1500,
            state=OverrideState.SYNCED,
        )
        assert override.is_pending is False
        assert override.is_accepted is False
        assert override.is_synced is True

    def test_has_conflict_property(self) -> None:
        """has_conflict should check conflict_type."""
        override1 = Override(
            id=OverrideId(uuid4()),
            project_id=ProjectId(uuid4()),
            field_id=FieldDefinitionId("total"),
            override_value=1600,
            original_value=1500,
        )
        assert override1.has_conflict is False

        override2 = Override(
            id=OverrideId(uuid4()),
            project_id=ProjectId(uuid4()),
            field_id=FieldDefinitionId("total"),
            override_value=1600,
            original_value=1500,
            conflict_type="formula",
        )
        assert override2.has_conflict is True

    def test_has_reason_property(self) -> None:
        """has_reason should check reason."""
        override1 = Override(
            id=OverrideId(uuid4()),
            project_id=ProjectId(uuid4()),
            field_id=FieldDefinitionId("total"),
            override_value=1600,
            original_value=1500,
        )
        assert override1.has_reason is False

        override2 = Override(
            id=OverrideId(uuid4()),
            project_id=ProjectId(uuid4()),
            field_id=FieldDefinitionId("total"),
            override_value=1600,
            original_value=1500,
            reason="Manual adjustment",
        )
        assert override2.has_reason is True
