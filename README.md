# wg-ha

```
sudo nix-shell --run "python3 main.py"
```

```
*/5 * * * * python3 /home/pi/test.py >> /home/pi/cron_out.txt
0 */2 * * * rm -f /home/pi/cron_out.txt
```

### Build the package
To build the package and get the `wgha` executable:

```bash
nix-build package.nix
./result/bin/wgha /path/to/ha_token.key
```

### Add to system configuration (NixOS)
To add this package to your NixOS system configuration, add the following to your `configuration.nix`:

```nix
{ pkgs, ... }:
{
	environment.systemPackages = with pkgs; [
		(import /path/to/wg-ha/package.nix {})
	];
}
```
