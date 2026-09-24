Run `project` to start a project: a name and a query over the world
(`science.view-query.v1`, as YAML or JSON text). A project is a label over
a query, never a container — the world facts its query selects are its
content, and they belong to every other project whose query selects them
too. Minting a project needs no selected project. Report the minted
record; its address is `coord:<project>`, the identity every later
reference uses, since names may be shared.
