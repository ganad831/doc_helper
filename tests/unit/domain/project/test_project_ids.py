"""Tests for project IDs."""

import pytest
from uuid import UUID, uuid4

from doc_helper.domain.project.project_ids import ProjectId


class TestProjectId:
    """Tests for ProjectId."""

    def test_create_project_id(self) -> None:
        """ProjectId should be created with UUID."""
        uid = uuid4()
        project_id = ProjectId(uid)
        assert project_id.value == uid

    def test_project_id_requires_uuid(self) -> None:
        """ProjectId should require UUID value."""
        with pytest.raises(TypeError, match="ProjectId value must be a UUID"):
            ProjectId("not-a-uuid")  # type: ignore

    def test_project_id_equality(self) -> None:
        """ProjectId should support equality comparison."""
        uid = uuid4()
        id1 = ProjectId(uid)
        id2 = ProjectId(uid)
        id3 = ProjectId(uuid4())
        assert id1 == id2
        assert id1 != id3

    def test_project_id_hashable(self) -> None:
        """ProjectId should be hashable."""
        id1 = ProjectId(uuid4())
        id2 = ProjectId(uuid4())
        id_set = {id1, id2, id1}
        assert len(id_set) == 2

    def test_project_id_str(self) -> None:
        """ProjectId should convert to string."""
        uid = uuid4()
        project_id = ProjectId(uid)
        assert str(project_id) == str(uid)

    def test_project_id_repr(self) -> None:
        """ProjectId should have repr."""
        uid = uuid4()
        project_id = ProjectId(uid)
        assert repr(project_id) == f"ProjectId({uid!r})"

    def test_project_id_immutable(self) -> None:
        """ProjectId should be immutable."""
        project_id = ProjectId(uuid4())
        with pytest.raises(Exception):  # FrozenInstanceError
            project_id.value = uuid4()  # type: ignore

    def test_project_id_from_string(self) -> None:
        """ProjectId should work with UUID from string."""
        uid_str = "12345678-1234-5678-1234-567812345678"
        uid = UUID(uid_str)
        project_id = ProjectId(uid)
        assert str(project_id) == uid_str
