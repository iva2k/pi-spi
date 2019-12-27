:: Upload this package to remote host over SSH

@echo off
setlocal enableextensions enabledelayedexpansion
set me=%~n0
set parent=%~dp0
set parent=%parent:~0,-1%  && rem ## trim trailing slash
set interactive=0
echo %CMDCMDLINE% | findstr /L /I %COMSPEC% >NUL 2>&1
if %ERRORLEVEL% == 0 set interactive=1

call :last_dir %parent%
set "dirname=%_last_dir%"

set cmd=scp
set u=pi
set host=raspberrypi
set dir=
:params

rem ## unquote: %~1%
set a=%~1%

if "%a%"=="" goto endparams
if "%a%"=="--user"    (set "u=%~2%" & shift & shift & goto params)
if "%a%"=="--host"    (set "host=%~2%" & shift & shift & goto params)
rem if "%a%"=="--dir"     (set "dir=%~2%" & shift & shift & goto params)
if "%a%"=="--path"    (set "dir=%~2%" & shift & shift & goto params)
if "%a%"=="--cmd"     (set "cmd=%~2%" & shift & shift & goto params)
::if "%a%"=="build"     (shift & set clean=0 & set build=1 & set doinstall=0 & goto params)

goto usage
:endparams

rem if [%dir%] == [] (set dir=/home/%u%/%dirname% )
rem scp is finicky to create directory - seems to work only if not renaming the directory
if [%dir%] == [] (set dir=/home/%u%/ )

:: Debug:
:: echo me=%me%
:: echo parent=%parent%
:: echo dirname=%dirname%
:: echo interactive=%intercative%

:: Copy package to host
echo.Copying %dirname% directory to %host%:%dir%, command:
echo.  %cmd% -pr ../%dirname%/ %u%@%host%:%dir%
echo:
%cmd% -pr ../%dirname%/ %u%@%host%:%dir%

echo:
echo.DONE.

goto :eof

:last_dir
:: get name of last folder in the path (return value in _last_dir)
setlocal
set _TMP_FOLDERNAME=%1
rem echo :last_dir %_TMP_FOLDERNAME%
for %%g in ("%_TMP_FOLDERNAME%") do set _TMP_FOLDERNAME=%%~nxg
endlocal & set _last_dir=%_TMP_FOLDERNAME%
goto :eof

:usage
  echo Script usage is:
  echo     %me% [options]
  echo where [options] are:
  echo:
  echo:   --user ^<user_name^> (default "pi")
  echo:   --host ^<host_name_or_ip^> (default "raspberrypi")
  echo:   --path ^<target_directory^> (default "/home/<user>/%dirname%")
  echo:   --cmd ^<scp_command^> (default "scp")
  echo:
  echo For example:
  echo     %me%
  echo     %me% --user not_pi
  echo     %me% --host 10.1.2.3
goto :eof
