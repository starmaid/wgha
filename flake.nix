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
          format = "pyproject";
          nativeBuildInputs = [ python.pkgs.setuptools ];
          propagatedBuildInputs = [ python.pkgs.requests ];
          doCheck = false;
        };
      in
      {
        packages.default = wgha;
        devShells.default = pkgs.mkShell {
          buildInputs = [
            wgha 
            pkgs.nixpkgs-fmt
            python.pkgs.ruff
            python.pkgs.setuptools
          ];
        };

        nixosModules.wgha = { config, lib, pkgs, ... }:
          with lib; {
            options.services.wgha = {
              enable = mkEnableOption "WireGuard-HomeAssistant updater";
              schedule = mkOption {
                type = types.str;
                default = "*-*-* *:*/3:00";
                description = "systemd timer schedule (OnCalendar value)";
              };
              baseurl = mkOption {
                type = types.str;
                default = "";
                description = "Base URL of Homeassistant instance";
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
                path = [ pkgs.docker ];
                serviceConfig = {
                  Type = "oneshot";
                  ExecStart = ''
                    ${wgha}/bin/wgha --config /etc/wgha/config.ini --baseurl ${config.services.wgha.baseurl} ${config.services.wgha.tokenFile}
                  '';
                };
                environment = { };
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
