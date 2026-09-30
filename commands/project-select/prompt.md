Run `project-select` to choose the project this session works in: give
`target` a project's name, or its `coord:<project>` address when two
projects share a name. The selection is the address, so a later rename
leaves it standing. It scopes what `next` and `project-show` enumerate, and
it is the project a new question, hypothesis, task or decision lands under.
`clear` unselects, after which enumerations read the whole world. Report
the selection block as returned; on `ambiguous-project`, show the
candidates and ask which address was meant.
