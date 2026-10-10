# Sync upstream

Upstream: https://github.com/Rumia-Channel/narou.rs

For milestone M1, this repo uses a source checkout supplied by the operator. Do not copy upstream binaries from unrelated architectures. To use a pinned upstream source:

```sh
git clone https://github.com/Rumia-Channel/narou.rs.git upstream/narou.rs
git -C upstream/narou.rs rev-parse HEAD
# build on a compatible Linux environment
git -C upstream/narou.rs submodule update --init --recursive
# build and assemble upstream narou/ using the documented cargo local-build workflow
python3 tools/stage_release.py --source upstream/narou.rs/narou --dest build/runtime
python3 -m unittest discover -s tests -v
```

Record exact upstream commit SHA, package checksums, dependencies, and license flavor for each release. M2 must pin upstream as a real Git submodule and provide QDK configuration. No upstream source or QPKG binary has yet been committed.
