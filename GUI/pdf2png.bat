echo off
rem pdf2png.bat
rem %1 PDF filename without extension
rem %2 density
rem %3 alpha, choose one of {on,off,remove}


magick -density %2 "%~1.pdf" -resize 700 -alpha remove "%~1.png"