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
          buildPhase = "fontforge -lang=ff -c 'Open($1); Generate($2); Generate($3); Generate($4)' Derani.sfd Derani.otf Derani.ttf Derani.woff2";
          installPhase = ''
            mkdir -p $out/share/fonts/{opentype,truetype,woff2}
            mv *.otf $out/share/fonts/opentype
            mv *.ttf $out/share/fonts/truetype
            mv *.woff2 $out/share/fonts/woff2
          '';
        };
        latin-fonts = pkgs.stdenv.mkDerivation {
          name = "latin-fonts";
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
      in { packages = { inherit derani-fonts latin-fonts; }; }
    );
}
