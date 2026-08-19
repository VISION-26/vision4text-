@echo off
setlocal
set "SITE=https://vision4text.in"

echo.
echo === Health endpoint ===
curl.exe -i "%SITE%/health"
if errorlevel 1 goto :failed

echo.
echo === Example asset endpoint ===
curl.exe -I "%SITE%/example-assets/bottle/good"
if errorlevel 1 goto :failed

echo.
echo === API proxy endpoint ===
curl.exe -i "%SITE%/api/v1/datasets"
if errorlevel 1 goto :failed

echo.
echo If /health returns HTML instead of JSON, Vercel is still serving the old deployment or the wrong Root Directory.
echo If the API returns 401 Not authenticated, the Vercel to Modal rewrite is working.
pause
exit /b 0

:failed
echo Live verification failed. Check the Vercel deployment and Modal endpoint.
pause
exit /b 1
