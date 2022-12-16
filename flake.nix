{
  description = "Fonts for the Derani alphabet";

  inputs.flake-utils.url = github:numtide/flake-utils;

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        derani-fonts = pkgs.stdenv.mkDerivation {
          name = "derani-fonts";
          src = self;
          buildInputs = [ pkgs.fontforge-fonttools ];
          buildPhase = "fontforge -lang=ff -c 'Open($1); Generate($2); Generate($3)' Derani.sfd Derani.otf Derani.woff2";
          installPhase = ''
            mkdir -p $out/share/fonts/{opentype,woff2}
            mv Derani.otf   $out/share/fonts/opentype
            mv Derani.woff2 $out/share/fonts/woff2
          '';
        };
      in {
        defaultPackage = derani-fonts;
        packages.derani-fonts = derani-fonts;
      }
    );
}
