@echo off
echo Building HEAL Application...

REM Clean up previous builds and cache
rd /s /q HEAL-Build\
rd /s /q __pycache__\
rd /s /q src\heal\__pycache__\
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"

echo Installing dependencies...
python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple/
pip install -r requirements-build.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/

echo Building executable...
pyinstaller -w -i ./src/heal/resources/images/icon.ico ./main.py -n HEAL --add-data "src/heal/resources;src/heal/resources"

echo Copying resources...
xcopy /s /e /y dist\HEAL\ HEAL-Build\
xcopy /s /e /y src\heal\resources\ HEAL-Build\src\heal\resources\
xcopy /s /e /y config\ HEAL-Build\config\
xcopy /s /e /y icons\ HEAL-Build\icons\

echo Cleaning up build artifacts...
rd /s /q dist\
rd /s /q build\
del /f /q HEAL.spec

echo Cleaning up cache files...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"

echo Build complete! Starting application...
start ./HEAL-Build/HEAL.exe