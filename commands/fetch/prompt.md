Run `fetch` when a dataset record is mounted from another installation and this
machine does not yet hold its bytes. Give the dataset's address and a `source`:
an absolute path or an https:// URL. The bytes are held only if they match the
digest the dataset declares, and the configuration's `[fetch]` policy allows it
(`records-only` refuses). The output is the holdings observation; if it refuses,
report the refusal and change nothing.
