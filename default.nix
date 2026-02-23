{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    (pkgs.python3.withPackages (python-pkgs: [
      python-pkgs.requests
    ]))
  ];
}