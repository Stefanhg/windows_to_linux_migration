## Development

# Testing strategy
We use behavior based testing, meaning it tests actual behavior in OS to verify it works to cover user's experince rather than simulated tests.

See [desktop testing instructions](tests/README.md). Verify the second-screen
clock with `sh tests/desktop.sh --tags clock`. The script backfills supported
applets on existing second panels and copies their initial settings, including
clock format. Applets limited to one instance (sound, network, power) stay on
the primary panel; supported items such as clock/calendar and keyboard can
appear on both. Reapplying does not create duplicate copies on a panel.
