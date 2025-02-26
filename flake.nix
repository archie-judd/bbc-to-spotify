{
  inputs = {

    flake-utils.url = "github:numtide/flake-utils";

    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";

    poetry2nix = {
      url = "github:nix-community/poetry2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, flake-utils, poetry2nix }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

        _poetry2nix = poetry2nix.lib.mkPoetry2Nix { inherit pkgs; };

        overrides = _poetry2nix.defaultPoetryOverrides.extend (self: super: {
          bs4 = super.bs4.overridePythonAttrs (old: {
            buildInputs = (old.buildInputs or [ ]) ++ [ super.setuptools ];
          });
        });

        env = _poetry2nix.mkPoetryEnv {
          projectDir = ./.;
          editablePackageSources = {
            radio_6_to_spotify = "${builtins.getEnv "PWD"}/src";
          };
          overrides = overrides;
        };

        app = _poetry2nix.mkPoetryApplication {
          projectDir = ./.;
          preferWheels = true;
          overrides = overrides;
        };

      in {
        devShells.default = pkgs.mkShell {
          inputsFrom = [ env.env ];
          packages = [ pkgs.poetry ];
        };

        apps.default = {
          type = "app";
          program = "${app}/bin/bbc-to-spotify";
        };

        packages.default = app;

      });
}
