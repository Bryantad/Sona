@echo off
REM Sona 0.9.6 Test Suite Runner for Windows
REM Runs all test files sequentially

echo ========================================
echo Sona 0.9.6 - Test Suite Runner
echo ========================================
echo.

echo [1/8] Running complete verification test...
sona tests\sona\test_all_096.sona
if %errorlevel% neq 0 (
    echo ERROR: tests\sona\test_all_096.sona failed!
    exit /b 1
)
echo.

echo [2/8] Running basic modules test...
sona tests\sona\test_stdlib_basics.sona
if %errorlevel% neq 0 (
    echo ERROR: tests\sona\test_stdlib_basics.sona failed!
    exit /b 1
)
echo.

echo [3/8] Running data processing test...
sona tests\sona\test_stdlib_data.sona
if %errorlevel% neq 0 (
    echo ERROR: tests\sona\test_stdlib_data.sona failed!
    exit /b 1
)
echo.

echo [4/8] Running collections test...
sona tests\sona\test_stdlib_collections.sona
if %errorlevel% neq 0 (
    echo ERROR: tests\sona\test_stdlib_collections.sona failed!
    exit /b 1
)
echo.

echo [5/8] Running time and random test...
sona tests\sona\test_stdlib_time.sona
if %errorlevel% neq 0 (
    echo ERROR: tests\sona\test_stdlib_time.sona failed!
    exit /b 1
)
echo.

echo [6/8] Running filesystem test...
sona tests\sona\test_stdlib_filesystem.sona
if %errorlevel% neq 0 (
    echo ERROR: tests\sona\test_stdlib_filesystem.sona failed!
    exit /b 1
)
echo.

echo [7/8] Running regex test...
sona tests\sona\test_stdlib_regex.sona
if %errorlevel% neq 0 (
    echo ERROR: tests\sona\test_stdlib_regex.sona failed!
    exit /b 1
)
echo.

echo [8/8] Running simple arithmetic test...
sona tests\sona\test.sona
if %errorlevel% neq 0 (
    echo ERROR: tests\sona\test.sona failed!
    exit /b 1
)
echo.

echo ========================================
echo ALL TESTS COMPLETED SUCCESSFULLY!
echo ========================================
echo.
echo Sona 0.9.6 is fully operational.
echo.
