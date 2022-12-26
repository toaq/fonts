{
  description = "Fonts for the Toaq language";

  inputs.flake-utils.url = github:numtide/flake-utils;

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        derani = pkgs.stdenv.mkDerivation {
          name = "derani";
          src = self;
          buildInputs = [ pkgs.fontforge-fonttools ];
          buildPhase = "fontforge -lang=ff -c 'Open($1); Generate($2); Generate($3); Generate($4)' Derani.sfd Derani.otf Derani.ttf Derani.woff2";
          installPhase = ''
            mkdir -p $out/share/fonts/{opentype,truetype,woff2}
            mv *.otf $out/share/fonts/opentype
            mv *.ttf $out/share/fonts/truetype
            mv *.woff2 $out/share/fonts/woff2
          '';
        };
        latin = pkgs.stdenv.mkDerivation {
          name = "latin";
          src = self;
          buildInputs = [ pkgs.fontforge-fonttools ];
          buildPhase = "fontforge -lang=ff -c 'Open($1); Generate($2); Generate($3); Generate($4); Open($5); Generate($6); Generate($7); Generate($8)' \"Commissioner Medium.sfd\" \"Commissioner Medium.otf\" \"Commissioner Medium.ttf\" \"Commissioner Medium.woff2\" \"Commissioner Bold.sfd\" \"Commissioner Bold.otf\" \"Commissioner Bold.ttf\" \"Commissioner Bold.woff2\"";
          installPhase = ''
            mkdir -p $out/share/fonts/{opentype,truetype,woff2}
            mv *.otf $out/share/fonts/opentype
            mv *.ttf $out/share/fonts/truetype
            mv *.woff2 $out/share/fonts/woff2
          '';
        };
        allPkgs = { inherit derani latin; };
      in {
        packages = allPkgs // {
          all = pkgs.symlinkJoin {
            name = "all";
            paths = builtins.attrValues allPkgs;
          };
        };
        defaultPackage = self.packages.${system}.all;
      }
    );
}
