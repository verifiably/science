Run `projects` to list every project in the world: its `coord:<project>`
address, its name, the revision that stands, and a mark on the one this
session has selected. Two projects may share a name; the address tells
them apart and is what `project-select` takes when a name is ambiguous. A
project shown as `divergent` has more than one standing revision: report
it as listed, and do not pick one.
