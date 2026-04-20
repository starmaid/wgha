
# wg-ha

WireGuard-HomeAssistant updater packaged as a Python package, with Nix and NixOS module support.

## Usage

### Build and Run Manually

```bash
nix build ./wgha
./result/bin/wgha --config /path/to/config.ini /path/to/ha_token.key
```

Or enter a dev shell:

```bash
nix develop
wgha --config /path/to/config.ini /path/to/ha_token.key
```

### NixOS Module (systemd timer)

Add this flake as an input to your `flake.nix`:

```nix
inputs.wgha.url = "github:starmaid/wg-ha"
```

Then in your `nixosConfiguration`:

```nix
{
	imports = [ inputs.wgha.nixosModules.wgha ];
	services.wgha = {
		enable = true;
		tokenFile = "/etc/nixos/ha_token.key";
		configText = ''
			[section]
			key = value
		'';
		schedule = "hourly"; # or any systemd OnCalendar value
	};
}
```

This will:
- Install the `wgha` package
- Write `/etc/wgha/config.ini` with your config
- Set up a systemd service and timer to run `wgha` on the schedule you choose

#### Configuration Options

- `services.wgha.enable` (bool): Enable the updater
- `services.wgha.tokenFile` (path): Path to Home Assistant token file
- `services.wgha.configText` (string): Contents of `config.ini` (will be written to `/etc/wgha/config.ini`)
- `services.wgha.schedule` (string): systemd timer schedule (default: `hourly`)

#### Example: Custom Schedule

```nix
services.wgha.schedule = "*/10 * * * *"; # every 10 minutes
```

---

For more details, see the `flake.nix` and source code.
