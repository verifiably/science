# Pilot v3 read log — 2026-10-30

Reader: Codex. Exact raw request/selection log remains off-tree as `pilot-v3-evidence/read-log.jsonl`; this portable log avoids republishing full selected copyrighted sections. Current source-ledger dispositions override mistaken contemporaneous “permitted” labels. Three abstracts read, only PMID37390336 retained for claims. Discussion37390336/41056512 fetched but unread; Discussion42492029 read and source stopped. Five full-text attempts, zero complete reads. No patient rows/matrices or review body read. 16 cumulative search attempts/67 identities; original v1/v2 logs remain attached. All URL-bearing rows below are separate requests, even empty/failed selection; family-search rows are quarry invocations. “Full-text attempt=no” is an accounting classification, not permission or proof no scientific text was encountered.

| # | UTC | Kind | Source/request | Full-text attempt | Selected/error record |
|---|---|---|---|---|---|
| 1 | 2026-10-30T13:19:40.151229+00:00 | metadata-preflight | metadata batch | no | {} |
| 2 | 2026-10-30T13:20:27.721483+00:00 | live-isolation-probe | pubmed:29712909 | no | {"http_status": 200, "selected_sha256": "659d8fbb8620dc2fd161109d6d3360cd9cc685c12a7cfabf4241882114903de8"} |
| 3 | 2026-10-30T13:21:16.115288+00:00 | isolated-mapping-design | pubmed:31221779 | no | {"http_status": 200} |
| 4 | 2026-10-30T13:21:16.116076+00:00 | isolated-mapping-design | pubmed:30635013 | no | {"http_status": 200} |
| 5 | 2026-10-30T13:21:16.116721+00:00 | isolated-mapping-design | pubmed:30275468 | no | {"http_status": 200} |
| 6 | 2026-10-30T13:21:16.117377+00:00 | isolated-mapping-design | pubmed:29712909 | no | {"http_status": 200} |
| 7 | 2026-10-30T13:21:20.085231+00:00 | isolated-mapping-design | pubmed:42926231 | no | {"http_status": 200} |
| 8 | 2026-10-30T13:21:21.589928+00:00 | isolated-mapping-design | pubmed:42928255 | no | {"http_status": 200} |
| 9 | 2026-10-30T13:21:23.635008+00:00 | isolated-mapping-design | pubmed:42930200 | no | {"http_status": 200} |
| 10 | 2026-10-30T13:21:23.734663+00:00 | isolated-mapping-design | pubmed:42935712 | no | {"http_status": 200} |
| 11 | 2026-10-30T13:22:01.585894+00:00 | analyst-section-read | pubmed:31221779 | no | {"file": "31221779-methods.txt"} |
| 12 | 2026-10-30T13:22:01.586106+00:00 | analyst-section-read | pubmed:29712909 | no | {"file": "29712909-methods.txt"} |
| 13 | 2026-10-30T13:22:56.217261+00:00 | section-structure-diagnosis | pubmed:30635013 | no | {} |
| 14 | 2026-10-30T13:24:44.595975+00:00 | availability-v3 | pubmed:30635013 | no | {"section_id": "_adda93_", "http_status": 200, "file": "30635013-availability-v3.txt", "sha256": "a6de3f40cf43fba7af043a7e44336044f8ccf5a0103d237b0f05a128046ef282"} |
| 15 | 2026-10-30T13:24:44.596590+00:00 | availability-v3 | pubmed:30275468 | no | {"section_id": null, "http_status": 200, "error": "expected one data-availability section, found 2"} |
| 16 | 2026-10-30T13:24:44.597278+00:00 | availability-v3 | pubmed:42926231 | no | {"section_id": null, "http_status": 200, "error": "expected one data-availability section, found 0"} |
| 17 | 2026-10-30T13:24:47.456103+00:00 | availability-v3 | pubmed:42928255 | no | {"section_id": null, "http_status": 200, "error": "expected one data-availability section, found 0"} |
| 18 | 2026-10-30T13:24:49.292827+00:00 | availability-v3 | pubmed:42930200 | no | {"section_id": null, "http_status": 200, "error": "expected one data-availability section, found 2"} |
| 19 | 2026-10-30T13:26:04.513470+00:00 | family-search | 9 | no | {"file": "family-heterogeneity.json"} |
| 20 | 2026-10-30T13:26:07.637919+00:00 | family-search | 10 | no | {"file": "family-progression.json"} |
| 21 | 2026-10-30T13:26:10.965787+00:00 | family-search | 11 | no | {"file": "family-measurement.json"} |
| 22 | 2026-10-30T13:26:13.482622+00:00 | family-search | 12 | no | {"file": "family-microenvironment.json"} |
| 23 | 2026-10-30T13:26:16.171096+00:00 | family-search | 13 | no | {"file": "family-treatment.json"} |
| 24 | 2026-10-30T13:26:18.802398+00:00 | family-search | 14 | no | {"file": "family-persistence.json"} |
| 25 | 2026-10-30T13:26:49.363978+00:00 | addressed-availability-and-design | pubmed:30275468 | no | {"http_status": 200, "availability_file": "30275468-availability-addressed.txt"} |
| 26 | 2026-10-30T13:26:49.364708+00:00 | addressed-availability-and-design | pubmed:42930200 | no | {"http_status": 200, "availability_file": "42930200-availability-addressed.txt"} |
| 27 | 2026-10-30T13:26:49.365304+00:00 | addressed-availability-and-design | pubmed:30635013 | no | {"http_status": 200} |
| 28 | 2026-10-30T13:27:13.797422+00:00 | family-oa-preflight | metadata batch | no | {"file": "family-sources.json"} |
| 29 | 2026-10-30T13:28:15.296077+00:00 | family-mapping | pubmed:38942927 | no | {"http_status": 200, "availability_error": "expected one data-availability section, found 0", "file": "38942927-mapping.json"} |
| 30 | 2026-10-30T13:28:15.296835+00:00 | family-mapping | pubmed:37390336 | no | {"http_status": 200, "availability_error": "expected one data-availability section, found 0", "file": "37390336-mapping.json"} |
| 31 | 2026-10-30T13:28:15.297560+00:00 | family-mapping | pubmed:42492029 | no | {"http_status": 200, "availability_section_id": "_adda93_", "file": "42492029-mapping.json"} |
| 32 | 2026-10-30T13:28:15.298289+00:00 | family-mapping | pubmed:42247308 | no | {"http_status": 200, "availability_error": "expected one data-availability section, found 0", "file": "42247308-mapping.json"} |
| 33 | 2026-10-30T13:28:19.242003+00:00 | family-mapping | pubmed:38514625 | no | {"http_status": 200, "availability_section_id": "_adda93_", "file": "38514625-mapping.json"} |
| 34 | 2026-10-30T13:28:20.502087+00:00 | family-mapping | pubmed:34521827 | no | {"http_status": 200, "availability_section_id": "_adda93_", "file": "34521827-mapping.json"} |
| 35 | 2026-10-30T13:28:20.895422+00:00 | family-mapping | pubmed:42358738 | no | {"http_status": 200, "availability_section_id": "_adda93_", "file": "42358738-mapping.json"} |
| 36 | 2026-10-30T13:28:23.913747+00:00 | family-mapping | pubmed:41056512 | no | {"http_status": 200, "availability_section_id": "_adda93_", "file": "41056512-mapping.json"} |
| 37 | 2026-10-30T13:28:26.009648+00:00 | family-mapping | pubmed:42027747 | no | {"http_status": 200, "availability_error": "expected one data-availability section, found 0", "file": "42027747-mapping.json"} |
| 38 | 2026-10-30T13:28:29.440555+00:00 | family-mapping | pubmed:41981199 | no | {"http_status": 200, "availability_error": "expected one data-availability section, found 0", "file": "41981199-mapping.json"} |
| 39 | 2026-10-30T13:29:49.236818+00:00 | addressed-method-design-read | pubmed:38942927 | no | {"subsection_id": "Sec12", "http_status": 200, "file": "38942927-design-Sec12.txt", "sha256": "9f7405e6ee576bcf4a43c170f8936583d071854c7c4a5a023341d9b40e752eb5"} |
| 40 | 2026-10-30T13:29:49.237834+00:00 | addressed-method-design-read | pubmed:37390336 | no | {"subsection_id": "sec2.1", "http_status": 200, "file": "37390336-design-sec2.1.txt", "sha256": "657f80b8a02a95585852196e449b35e747d2ffebf3a7418a4c383ff57bc263be"} |
| 41 | 2026-10-30T13:29:49.238678+00:00 | addressed-method-design-read | pubmed:42492029 | no | {"subsection_id": "sec8", "http_status": 200, "file": "42492029-design-sec8.txt", "sha256": "64547ad4b6d3bba6731b5a4e1e9acd1d4d284f69ee18345822f4d2b6bf62de89"} |
| 42 | 2026-10-30T13:29:49.239452+00:00 | addressed-method-design-read | pubmed:42358738 | no | {"subsection_id": "s2-1", "http_status": 200, "file": "42358738-design-s2-1.txt", "sha256": "643b5279d2232dbd4f30dce89a95df794a83a3d33cf6d0285abcadeea96add47"} |
| 43 | 2026-10-30T13:29:53.690795+00:00 | addressed-method-design-read | pubmed:41056512 | no | {"subsection_id": "sec015", "http_status": 200, "file": "41056512-design-sec015.txt", "sha256": "5b36a9b6cd121a8b82b9fd8059e90e9979c532fbf0610c63e49607f9baf9f301"} |
| 44 | 2026-10-30T13:29:53.797359+00:00 | addressed-method-design-read | pubmed:42027747 | no | {"subsection_id": "sec2.1", "http_status": 200, "file": "42027747-design-sec2.1.txt", "sha256": "135e35fa93097ef72f690c7f9a53546d5f17b833975781a930c1975363b22d95"} |
| 45 | 2026-10-30T13:29:54.227300+00:00 | addressed-method-design-read | pubmed:41981199 | no | {"subsection_id": "Sec10", "http_status": 200, "file": "41981199-design-Sec10.txt", "sha256": "0baa36309f0330aed77c8aa0e54d60d628084b92077715998c942d0ab76068f9"} |
| 46 | 2026-10-30T13:29:56.027118+00:00 | addressed-method-design-read | pubmed:42247308 | no | {"subsection_id": "sec2.5", "http_status": 200, "file": "42247308-design-sec2.5.txt", "sha256": "6712690bb0ac0784b000138ee292063fb742e3574c84a9ef945a8f7a9aa26d90"} |
| 47 | 2026-10-30T13:32:28.718334+00:00 | permitted-primary-partial-read | pubmed:37390336 | yes | {"http_status": 200} |
| 48 | 2026-10-30T13:32:28.719097+00:00 | permitted-primary-partial-read | pubmed:42492029 | yes | {"http_status": 200} |
| 49 | 2026-10-30T13:32:28.719977+00:00 | permitted-primary-partial-read | pubmed:41056512 | yes | {"http_status": 200} |
| 50 | 2026-10-30T13:33:16.975193+00:00 | abstract-structure | pubmed:37390336 | no | {} |
| 51 | 2026-10-30T13:33:16.975959+00:00 | abstract-structure | pubmed:41056512 | no | {} |
| 52 | 2026-10-30T13:34:20.523172+00:00 | permitted-addressed-abstract | pubmed:37390336 | yes | {"http_status": 200, "file": "37390336-abstract.txt", "sha256": "15368feed1299732a08bd909f03df60dcfed2dad494fea97ce7d97e86473672b"} |
| 53 | 2026-10-30T13:34:20.523828+00:00 | permitted-addressed-abstract | pubmed:41056512 | yes | {"http_status": 200, "file": "41056512-abstract.txt", "sha256": "85ac77dda0ef2b0814da376799b1d0217e28b70046a08c0576889442ec94e4ef"} |
| 54 | 2026-10-30T13:35:45.217764+00:00 | additional-dataset-name-projection | pubmed:41056512 | no | {} |
| 55 | 2026-10-30T13:37:56.025594+00:00 | external-cohort-design-projection | pubmed:41056512 | no | {} |
| 56 | 2026-10-30T13:39:41.794052+00:00 | external-cohort-design-context | pubmed:41056512 | no | {} |
| 57 | 2026-10-30T13:40:25.090590+00:00 | isolated-reference-identifiers | pubmed:41056512 | no | {} |
| 58 | 2026-10-30T13:46:01.215100+00:00 | isolated-reference-identifiers-by-id | metadata batch | no | {} |
| 59 | 2026-10-30T13:46:24.000352+00:00 | reference-identifiers-descendant-path | metadata batch | no | {} |
| 60 | 2026-10-30T13:47:45.120522+00:00 | additional-OA-preflight | 16 | no | {} |
| 61 | 2026-10-30T13:48:33.199528+00:00 | additional-mapping | pubmed:33250513 | no | {"http_status": 200, "availability_error": "expected one data-availability section, found 2"} |
| 62 | 2026-10-30T13:48:33.200316+00:00 | additional-mapping | pubmed:33147277 | no | {"http_status": 200, "availability_error": "expected one data-availability section, found 0"} |
| 63 | 2026-10-30T13:48:33.200938+00:00 | additional-mapping | pubmed:34691592 | no | {"http_status": 200, "availability_error": "expected one data-availability section, found 2"} |
| 64 | 2026-10-30T13:48:37.054197+00:00 | additional-mapping | pubmed:32215016 | no | {"http_status": 200, "availability_error": "expected one data-availability section, found 2"} |
| 65 | 2026-10-30T13:48:39.402790+00:00 | additional-mapping | pubmed:31970084 | no | {"http_status": 200} |
| 66 | 2026-10-30T13:48:42.676485+00:00 | additional-mapping | pubmed:31803627 | no | {"http_status": 200, "availability_error": "expected one data-availability section, found 2"} |
| 67 | 2026-10-30T13:49:47.508415+00:00 | complete-isolated-methods | pubmed:37390336 | no | {"sha256": "dccf83524109ad0cb4aba9a34dcaad596e1eb8d654f45011c092ca8855aa54d3"} |

Rows=67; URL-bearing requests=59; deliberate full-text attempts=5. Raw log SHA256 f5320dcc24b476e1e43ffa55edbc684d86ecb91a31e456bf1ff013c17b8bf08b.

## Retained selected text hashes (no full text included here)

- `29712909-availability.txt`: 659d8fbb8620dc2fd161109d6d3360cd9cc685c12a7cfabf4241882114903de8
- `29712909-data-availability.txt`: 659d8fbb8620dc2fd161109d6d3360cd9cc685c12a7cfabf4241882114903de8
- `29712909-methods.txt`: 6d25cc67dcf1fa8e1d8283c69ab47831938b2ff62ce152f552a4e6df71f08d70
- `30275468-availability-addressed.txt`: 75c95497a231c5642126ef24b8b347d9b9626b01a5ce57e31d1cddf3d0bb2909
- `30275468-methods-v3.txt`: 2f10780dbe2385a4255658e50fbe040e0c2ea1926655bdb69048c4395a21dd9b
- `30275468-methods.txt`: 2f10780dbe2385a4255658e50fbe040e0c2ea1926655bdb69048c4395a21dd9b
- `30635013-availability-v3.txt`: a6de3f40cf43fba7af043a7e44336044f8ccf5a0103d237b0f05a128046ef282
- `30635013-methods-v3.txt`: 9a097e878f2e773781d21551891e13b5e87b5fca4c1c79be17d85d5e65b10dae
- `31221779-methods.txt`: ea0be4a6cd86b17b13f6f54dc6a0264aadcaf4c4040417173d1a9e74fda878df
- `37390336-abstract.txt`: 15368feed1299732a08bd909f03df60dcfed2dad494fea97ce7d97e86473672b
- `37390336-design-sec2.1.txt`: 657f80b8a02a95585852196e449b35e747d2ffebf3a7418a4c383ff57bc263be
- `37390336-discussion.txt`: e35cad4daaaaf241f31b15a028c5831a3b795f4768f684ac6a05a44a2e604724
- `37390336-methods-complete.txt`: dccf83524109ad0cb4aba9a34dcaad596e1eb8d654f45011c092ca8855aa54d3
- `38942927-design-Sec12.txt`: 9f7405e6ee576bcf4a43c170f8936583d071854c7c4a5a023341d9b40e752eb5
- `41056512-abstract.txt`: 85ac77dda0ef2b0814da376799b1d0217e28b70046a08c0576889442ec94e4ef
- `41056512-design-sec015.txt`: 5b36a9b6cd121a8b82b9fd8059e90e9979c532fbf0610c63e49607f9baf9f301
- `41056512-discussion.txt`: e933890ac1b4378ea5d421c5bf0b12e6a3a5c669f1abaf7912f8d43431128fa7
- `41981199-design-Sec10.txt`: 0baa36309f0330aed77c8aa0e54d60d628084b92077715998c942d0ab76068f9
- `42027747-design-sec2.1.txt`: 135e35fa93097ef72f690c7f9a53546d5f17b833975781a930c1975363b22d95
- `42247308-design-sec2.5.txt`: 6712690bb0ac0784b000138ee292063fb742e3574c84a9ef945a8f7a9aa26d90
- `42358738-design-s2-1.txt`: 643b5279d2232dbd4f30dce89a95df794a83a3d33cf6d0285abcadeea96add47
- `42492029-abstract.txt`: de58bafb071606a7c1d4fa2724026c7f4136099067e8db86feb42a77e12a299c
- `42492029-design-sec8.txt`: 64547ad4b6d3bba6731b5a4e1e9acd1d4d284f69ee18345822f4d2b6bf62de89
- `42492029-discussion.txt`: 61f13aaca4405f67538207e1238942ccc17bd1cbe425d5b70ad87870f4ea2500
- `42930200-availability-addressed.txt`: f20452f1450c9046832caf904dc30cb75a90b72829e313167d9732d4b1b9e5eb
- `section-check-green.txt`: 17e52ffea64e74154951607f1861400bfd698de94fb5b76de9eeed5d6372dc86
- `world-status-v3.txt`: 729b18f756d6cafe8b8f4321e38df18d95a0743e6f3fa1f4c4fdcea0bb95a679

The selector's initial structured-abstract ambiguity and duplicate availability sections failed closed. A separate v3 helper restricted Methods to main body/back, supported specific IDs and specifically addressed method subsections; synthetic sentinel/refusal tests passed after observed failures. It is a run-local helper, not shipped product. Nested reference-list IDs were resolved after two empty projections; only reference identifier metadata was displayed, which included encoded result-bearing titles and was routed as an incident. Structural isolation cannot certify that a Methods section lacks results. Main Methods37390336 contains an observation from the already mapped primary cohort; it was read and is not used as independent support.
