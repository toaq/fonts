{
  description = "Fonts for the Toaq language";

  inputs.flake-utils.url = github:numtide/flake-utils;

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        mkBuildPhase = fontNames:
          let
            names = pkgs.lib.strings.concatMapStringsSep
              " " (name: "\"${name}\"") fontNames;
          in ''
            for font in ${names}; do
              fontforge -lang=ff -c \
                'Open($1); Generate($2); Generate($3); Generate($4)' \
                "$font.sfd" "$font.otf" "$font.ttf" "$font.woff2"
            done
          '';
        installPhase = ''
          mkdir -p $out/share/fonts/{opentype,truetype,woff2}
          mv *.otf $out/share/fonts/opentype
          mv *.ttf $out/share/fonts/truetype
          mv *.woff2 $out/share/fonts/woff2
        '';
        derani = pkgs.stdenv.mkDerivation {
          name = "derani";
          src = self;
          buildInputs = [ pkgs.fontforge-fonttools ];
          buildPhase = mkBuildPhase [ "Derani" "Guezueq" "Neajiaq" ];
          inherit installPhase;
        };
        latin = pkgs.stdenv.mkDerivation {
          name = "latin";
          src = self;
          buildInputs = [ pkgs.fontforge-fonttools ];
          buildPhase = mkBuildPhase [
            "Commissioner Medium"
            "Commissioner Bold"
          ];
          inherit installPhase;
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
