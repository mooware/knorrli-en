set INPUT_EXE="%1"
set GAME_DIR="%2"

copy %INPUT_EXE% ATL.exe
python translation.py translation.txt ATL.exe
copy ATL.exe "%GAME_DIR%\ATL.exe"

python graphics.py encode_pal GENFRAME.GRA.png "%GAME_DIR%\GENFRAME.GRA"
copy GENFRAME.GRA.png.gra "%GAME_DIR%\GENFRAME.GRA"

python graphics.py encode FX1_.GRA.png "%GAME_DIR%\GENFRAME.GRA"
copy FX1_.GRA.png.gra "%GAME_DIR%\FX1_.GRA"