## Követelmények
Python 3.9

## Szükséges külső alkalmazások:
 - Tesseract (Karakterfelismerés)
 - ImageMagick-7.1.0-Q16-HDRI (Latex fájlból generált .pdf konvertálása .png képfájlba)
 - TeXstudio (Latex fájl módosítása és pdf generálása)

## Alkalmazás futtatása:
1. ImageMagick letöltése a https://imagemagick.org/script/download.php címről, majd hozzáadása a PATH környezeti változóhoz
2. TeXstudio letöltése a https://www.texstudio.org/ címről, majd hozzáadása a PATH környezeti változóhoz
3. Tesseract letöltése a https://github.com/UB-Mannheim/tesseract/wiki címről, majd hozzáadása a PATH környezeti változóhoz
4. Chart_scanner.zip kibontása
5. Chart_scanner\ útvonalon Parancssor nyitása
6. **_virtual_environment\Scripts\activate_** parancs határása elindul a virtuális környezet
7. **_pip install -r requirements.txt_** parancs kiadása során az összes szükséges python könyvtár letöltésre kerül
8. **_python ._** parancs kiadása után megnyílik a grafikus felület

## Példafájlok
 - A **_Chart_scanner\example_input_charts\\_** útvonalon találhatóak generált diagramok és a hozzájuk tartozó latex fájlok.