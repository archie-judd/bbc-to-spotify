{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.05";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        python = pkgs.python313;

        app = python.pkgs.buildPythonApplication {
          pname = "bbc-to-spotify";
          version = "0.0.7";
          pyproject = true;
          src = ./.;

          build-system = [ python.pkgs.hatchling ];
          dependencies = with python.pkgs; [
            beautifulsoup4
            pydantic
            requests
          ];

          pythonImportsCheck = [ "bbc_to_spotify" ];
        };
      in
      {
        packages.default = app;

        apps.default = {
          type = "app";
          program = "${app}/bin/bbc-to-spotify";
        };

        devShells.default = pkgs.mkShell {
          inputsFrom = [ app ];
          packages = with python.pkgs; [
            black
            pylint
          ];
        };
      }
    );
}
