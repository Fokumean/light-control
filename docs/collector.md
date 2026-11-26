# Light Control — collector

The collector requests the public DTEK Kyiv region shutdown page directly. No API key, AI or third-party JSON dependency. It identifies itself, checks robots.txt, makes no attempts to evade blocks, parses strict JSON without executing upstream scripts, validates the daily schedule and preserves the last good file if collection fails.

Source: https://www.dtek-krem.com.ua/ua/shutdowns

Public data format researched using https://github.com/Baskerville42/outage-data-ua (Alexander Tartmin, MIT). The collector is independently written; it does not use the upstream browser-based anti-bot bypass.

## First run
In GitHub Actions, select Collect public DTEK schedule, Run workflow, main. The workflow runs synthetic tests before the network request. Review the result before enabling the commented 15-minute schedule. A successful run publishes data/kyiv-region.json. Failed runs leave the previous file untouched. The existence of a public page or a permissive robots.txt does not constitute explicit permission to republish data.

The app must check lastUpdated, the source fact.update and the local date; the schedule is not a measurement of actual electricity availability. Emergency notices may supersede schedules. Address lookup is not implemented. Do not publish personal addresses.

No live collection has been confirmed at initial setup.
