# Light Control — schedule source

Current source: [outage-data-ua](https://github.com/Baskerville42/outage-data-ua), Alexander Tartmin (MIT code license; source data belongs to its provider).
Public feed: https://raw.githubusercontent.com/Baskerville42/outage-data-ua/main/data/kyiv-region.json
Original provider: https://www.dtek-krem.com.ua/ua/shutdowns

The direct collector is retained for future authorized access only. Its first run stopped because DTEK robots.txt disallows automatic collection. The active workflow does not contact DTEK or circumvent its restrictions.

The mirror synchronizer checks the upstream success flag, original timestamps (maximum age two hours), today's Kyiv-local schedule, all twelve groups and hourly states. It refuses older snapshots and preserves the last good file on failure. It never relabels old data as newly collected.

GitHub Actions checks every 15 minutes (execution may be delayed), on manual dispatch and when the workflow changes. Successful runs publish data/kyiv-region.json. The app must independently check freshness, source date and emergency notices; schedules do not measure actual electrical supply. Address search is not implemented. No personal address is stored.

No API key or AI is needed. The upstream public feed can disappear or stop updating; permission for direct collection remains unresolved. Public availability and the upstream code license do not guarantee redistribution rights over the provider's data.
