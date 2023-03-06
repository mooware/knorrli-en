set INPUT_EXE="%1"
set GAME_DIR="%2"

copy %INPUT_EXE% ATL.exe
python translation.py translation.txt ATL.exe
copy ATL.exe "%GAME_DIR%\ATL.exe"

python graphics.py encode GENFRAME.GRA.png "%GAME_DIR%\GENFRAME.GRA"
copy GENFRAME.GRA.png.gra "%GAME_DIR%\GENFRAME.GRA"