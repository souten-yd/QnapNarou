# Reviewable upstream synchronization

The baseline narou.rs source is **pinned as a Git submodule** at `upstream/narou.rs`. The QTS runtime is compiled from that pinned source and contains the original UI. Never replace bundled upstream files with an arbitrary partial copy.

```sh
git clone --recurse-submodules https://github.com/souten-yd/QnapNarou.git
cd QnapNarou
git submodule status
git -C upstream/narou.rs rev-parse HEAD
```

To review a proposed upstream update, use an isolated feature branch. Fetch upstream manually; inspect its exact version and changes, including dependencies, licenses, embedded JS, EPUB delivery and QNAP network settings. Move the gitlink to a reviewed SHA, then rerun the stage/build/EPUB tests and QTS device acceptance before merging or releasing. Do not automatically merge, rewrite or rebuild upstream on NAS startup.

**QNAP overlays must survive an upstream update:** `tools/build_epub_lite.py` applies the EPUB cached-text guard and iPhone download-link attributes to the checked-out source *before* the Rust binary compiles. The script validates the exact upstream markers and rejects drift; tests confirm a missing, doubled or changed download route is not silently accepted. Do not disable these checks simply to make a newer upstream build pass. If upstream natively fixes the issue, intentionally remove the now-obsolete overlay in a reviewed PR with equivalent regression tests.

```sh
python3 -m unittest discover -s tests -v
# Rebuild complete upstream runtime before the QNAP GPL/lite override.
# See the manual release workflow and tools/build_epub_lite.py.
```

Distributions must provide complete corresponding GPL source, including the pinned upstream commit and the QNAP overlay. Preserve `Third-Party-License.md` and the AozoraEpub3_Lite license notices.

The QPKG currently covers x86_64 only; ARM64 is not tested. Low-write / memory-batching and fully automatic update/rollback are separate unfinished milestones.
