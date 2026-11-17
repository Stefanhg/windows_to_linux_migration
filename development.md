# Development

## Testing strategy

We use behavior-based tests to verify what users experience in a live Cinnamon session. The [desktop testing instructions](tests/README.md) cover prerequisites, commands, and what the tests observe.

## Second-screen applets

The [tweak script](tweaks.sh) fills in missing supported applets on existing second panels and copies their initial settings, including the clock format. Cinnamon limits some applets, such as sound, network, and power, to one instance on the primary panel. Supported applets such as clock/calendar and keyboard can appear on both panels. You can reapply the tweaks without creating duplicate applets.

To verify the clock on both panels, run this from the repository root:

```sh
sh tests/desktop.sh --tags clock
```
