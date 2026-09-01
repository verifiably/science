---
name: "status"
description: "Show the world: corpora and their lifecycle status, the current epoch, record counts by kind."
---

You are working over one world of governed records through the `science`
commands. Until the coordination layer lands there is no current view:
commands read world state directly. Every write is a kernel act that
returns its own record or a refusal — report refusals verbatim, and never
retry with altered inputs, repair, or write around one. Results are
budgeted: a truncated result ends with a cursor, and continuing with that
cursor is the only way to see the rest. A command's declared inputs are its
whole interface; there is nothing to reach around.

Run `status` when the user asks where things stand, what corpora exist, or
whether an epoch is current. It takes no inputs. Render its output as-is;
if it ends with a truncation marker, continue with the cursor it names
rather than summarizing what you have not seen.
