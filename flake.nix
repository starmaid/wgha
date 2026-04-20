{
  description = "WireGuard-HomeAssistant Python package and NixOS module";
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };
  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
        python = pkgs.python3;
        wgha = python.pkgs.buildPythonPackage {
          pname = "wgha";
          version = "1.0";
          src = ./.;
          format = "setuptools";
          propagatedBuildInputs = [ python.pkgs.requests ];
          doCheck = false;
        };
      in {
        packages.default = wgha;
        devShells.default = pkgs.mkShell {
          buildInputs = [ wgha python.pkgs.ruff python.pkgs.setuptools ];
        };
        nixosModules.wgha = { config, lib, pkgs, ... }:
          with lib; {
            options.services.wgha = {
              enable = mkEnableOption "WireGuard-HomeAssistant updater";
              schedule = mkOption {
                type = types.str;
                default = "hourly";
                description = "systemd timer schedule (OnCalendar value)";
              };
              configText = mkOption {
                type = types.str;
                default = "";
                description = "Contents of config.ini for wgha";
              };
              tokenFile = mkOption {
                type = types.path;
                description = "Path to Home Assistant token file";
              };
            };
            config = mkIf config.services.wgha.enable {
              systemd.services.wgha = {
                description = "WireGuard-HomeAssistant updater";
                serviceConfig = {
                  Type = "oneshot";
                  ExecStart = ''
                    ${wgha}/bin/wgha --config /etc/wgha/config.ini ${config.services.wgha.tokenFile}
                  '';
                };
                environment = {};
                wantedBy = [ "multi-user.target" ];
              };
              systemd.timers.wgha = {
                wantedBy = [ "timers.target" ];
                timerConfig = {
                  OnCalendar = config.services.wgha.schedule;
                };
              };
              environment.etc."wgha/config.ini".text = config.services.wgha.configText;
            };
          };
      });
}
