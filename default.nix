{ pkgs ? import <nixpkgs> {} }:

let
  python = pkgs.python3;
  wgha = python.pkgs.buildPythonPackage {
    pname = "wgha";
    version = "1.0";
    src = ./.;
    format = "setuptools";
    propagatedBuildInputs = [ python.pkgs.requests ];
    doCheck = false;
  };
in
{
  wgha = wgha;
  shell = pkgs.mkShell {
    buildInputs = [ wgha python.pkgs.ruff python.pkgs.setuptools ];
  };
}