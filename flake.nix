{
  description = "Firefox Theme Switcher — develop shell";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }:
    let
      forAllSystems = nixpkgs.lib.genAttrs [ "x86_64-linux" "aarch64-linux" ];
    in
    {
      devShells = forAllSystems (system:
        let
          pkgs = import nixpkgs { inherit system; };
        in
        {
          default = pkgs.mkShell {
            packages = with pkgs; [
              (python3.withPackages (ps: with ps; [ tkinter ]))   # Python with tkinter
              xdg-utils                           # xdg-open for opening folders
              dejavu_fonts                        # font fallback (DejaVu Sans)
              noto-fonts                          # extra CJK/emoji coverage
            ];

            shellHook = ''
              echo "🔥 Firefox Theme Switcher dev shell"
              echo "   Run: python3 app.py"
              echo "   Font: DejaVu Sans (fallback)"
            '';
          };
        });
    };
}
