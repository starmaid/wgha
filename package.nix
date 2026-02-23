{ pkgs ? import <nixpkgs> {} }:

pkgs.python3Packages.buildPythonApplication {
  pname = "wgha";
  version = "1.0";
  src = ./.;
  # Only requests is needed, as per default.nix
  propagatedBuildInputs = [ pkgs.python3Packages.requests ];
  # Install main.py as the executable 'wgha'
  installPhase = ''
    mkdir -p $out/bin
    cp main.py $out/bin/wgha
    chmod +x $out/bin/wgha
    # Add a shebang for python3
    sed -i '1i#!/usr/bin/env python3' $out/bin/wgha
  '';
}
