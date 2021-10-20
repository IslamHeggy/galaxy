from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    TEXT
)
from sqlalchemy.orm import relation

from galaxy.model import tool_shed_install as install_model
from galaxy.model.base import ModelMapping
from galaxy.model.custom_types import (
    MutableJSONType,
    TrimmedString
)
from galaxy.model.orm.engine_factory import build_engine
from galaxy.model.orm.now import now
from galaxy.model.tool_shed_install import mapper_registry

metadata = mapper_registry.metadata

install_model.ToolShedRepository.table = Table("tool_shed_repository", metadata,
                                               Column("id", Integer, primary_key=True),
                                               Column("create_time", DateTime, default=now),
                                               Column("update_time", DateTime, default=now, onupdate=now),
                                               Column("tool_shed", TrimmedString(255), index=True),
                                               Column("name", TrimmedString(255), index=True),
                                               Column("description", TEXT),
                                               Column("owner", TrimmedString(255), index=True),
                                               Column("installed_changeset_revision", TrimmedString(255)),
                                               Column("changeset_revision", TrimmedString(255), index=True),
                                               Column("ctx_rev", TrimmedString(10)),
                                               Column("metadata", MutableJSONType, nullable=True),
                                               Column("includes_datatypes", Boolean, index=True, default=False),
                                               Column("tool_shed_status", MutableJSONType, nullable=True),
                                               Column("deleted", Boolean, index=True, default=False),
                                               Column("uninstalled", Boolean, default=False),
                                               Column("dist_to_shed", Boolean, default=False),
                                               Column("status", TrimmedString(255)),
                                               Column("error_message", TEXT))

install_model.ToolDependency.table = Table("tool_dependency", metadata,
                                           Column("id", Integer, primary_key=True),
                                           Column("create_time", DateTime, default=now),
                                           Column("update_time", DateTime, default=now, onupdate=now),
                                           Column("tool_shed_repository_id", Integer, ForeignKey("tool_shed_repository.id"), index=True, nullable=False),
                                           Column("name", TrimmedString(255)),
                                           Column("version", TEXT),
                                           Column("type", TrimmedString(40)),
                                           Column("status", TrimmedString(255), nullable=False),
                                           Column("error_message", TEXT))

install_model.ToolVersion.table = Table("tool_version", metadata,
                                        Column("id", Integer, primary_key=True),
                                        Column("create_time", DateTime, default=now),
                                        Column("update_time", DateTime, default=now, onupdate=now),
                                        Column("tool_id", String(255)),
                                        Column("tool_shed_repository_id", Integer, ForeignKey("tool_shed_repository.id"), index=True, nullable=True))

install_model.ToolVersionAssociation.table = Table("tool_version_association", metadata,
                                                   Column("id", Integer, primary_key=True),
                                                   Column("tool_id", Integer, ForeignKey("tool_version.id"), index=True, nullable=False),
                                                   Column("parent_id", Integer, ForeignKey("tool_version.id"), index=True, nullable=False))

mapper_registry.map_imperatively(install_model.ToolShedRepository, install_model.ToolShedRepository.table,
       properties=dict(tool_versions=relation(install_model.ToolVersion,
                                              primaryjoin=(install_model.ToolShedRepository.table.c.id == install_model.ToolVersion.table.c.tool_shed_repository_id),
                                              backref='tool_shed_repository'),
                       tool_dependencies=relation(install_model.ToolDependency,
                                                  primaryjoin=(install_model.ToolShedRepository.table.c.id == install_model.ToolDependency.table.c.tool_shed_repository_id),
                                                  order_by=install_model.ToolDependency.table.c.name,
                                                  backref='tool_shed_repository'),
                       required_repositories=relation(install_model.RepositoryRepositoryDependencyAssociation,
                                                      primaryjoin=(install_model.ToolShedRepository.table.c.id == install_model.RepositoryRepositoryDependencyAssociation.tool_shed_repository_id))))

mapper_registry.map_imperatively(install_model.ToolDependency, install_model.ToolDependency.table)

mapper_registry.map_imperatively(install_model.ToolVersion, install_model.ToolVersion.table,
       properties=dict(
           parent_tool_association=relation(install_model.ToolVersionAssociation,
                                            primaryjoin=(install_model.ToolVersion.table.c.id == install_model.ToolVersionAssociation.table.c.tool_id)),
           child_tool_association=relation(install_model.ToolVersionAssociation,
                                           primaryjoin=(install_model.ToolVersion.table.c.id == install_model.ToolVersionAssociation.table.c.parent_id))))

mapper_registry.map_imperatively(install_model.ToolVersionAssociation, install_model.ToolVersionAssociation.table)


def init(url, engine_options=None, create_tables=False):
    """Connect mappings to the database"""
    # Load the appropriate db module
    engine_options = engine_options or {}
    engine = build_engine(url, engine_options)
    # Connect the metadata to the database.
    metadata.bind = engine
    result = ModelMapping([install_model], engine=engine)
    # Create tables if needed
    if create_tables:
        metadata.create_all()
        # metadata.engine.commit()
    result.create_tables = create_tables
    # load local galaxy security policy
    return result
