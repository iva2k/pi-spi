@echo off

set NETNAME=PI-SPI

::set NETUSER=PI-SPI\pi
set NETUSER=pi

echo Removing existing connections...
net use Z: /delete
net session \\%NETNAME% /delete

echo Connecting \\%NETNAME%\pi to Z: (as user %NETUSER%)...
net use Z: \\%NETNAME%\pi /persistent:yes /user:%NETUSER%

pause