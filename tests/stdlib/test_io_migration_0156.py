from sona.stdlib_manifest import manifest_entries


def test_io_filesystem_migrations_reference_exported_canonical_functions():
    modules = {entry["name"]: entry for entry in manifest_entries()}
    exports = {entry["name"]: entry for entry in modules["io"]["exports"]}
    fs_names = {entry["name"] for entry in modules["fs"]["exports"]}
    for legacy, canonical in (("read_file", "read_text"), ("write_file", "write_text")):
        assert exports[legacy]["replacement"] == f"fs.{canonical}"
        assert canonical in fs_names
