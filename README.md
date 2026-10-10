# pytest cache directory #

This directory contains data from the pytest's cache plugin,
which provides the `--lf` and `--ff` options, as well as the `cache` fixture.

**Do not** commit this to version control.

See [the docs](https://docs.pytest.org/en/stable/how-to/cache.html) for more information.

### Future Improvements
- [ ] Parse and retain RSS `pubDate` as a timezone-aware datetime.
- [ ] Archive raw RSS XML responses for debugging and future reprocessing.
- [ ] Implement persistent ingestion history keyed by `guid` to deduplicate entries and preserve historical activity across runs.
- [ ] Distinguish explicit `No` values from missing/unknown values for `liked` and `rewatch`.
- [ ] Review additional RSS fields worth retaining in the internal data model.