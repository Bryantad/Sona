@echo off
:: Sona launcher - forwards arguments to the project's Python
:: Usage:
::   sona -m <module> [args]   -> runs: python -m <module> [args]
::   sona <args>               -> runs: python cli.py <args>

setlocal



:: If first arg is -m, forward module mode to python -m
if "%~1"=="-m" (
	:: Ensure there is a module name following -m
	if "%~2"=="" (
		echo Missing module name after -m
		endlocal
		exit /b 1
	)
	:: Capture module name and shift twice
	set "MODULE=%~2"
	shift
	shift
	:: Run the module under the project's Python
	python -m %MODULE% %*
	set "RC=%ERRORLEVEL%"
	endlocal
	@echo off
	:: Sona launcher - forwards arguments to Python
	:: Usage:
	::   sona -m <module> [args]   -> python -m <module> [args]
	::   sona [args]               -> python cli.py [args]

	setlocal

	:: Resolve Python executable preference: .venv -> venv -> python -> py -3
	set "PYCMD="
	set "PYARG="
	if exist "%~dp0\.venv\Scripts\python.exe" (
		set "PYCMD=%~dp0\.venv\Scripts\python.exe"
	) else if exist "%~dp0\venv\Scripts\python.exe" (
		set "PYCMD=%~dp0\venv\Scripts\python.exe"
	) else (
		where python >nul 2>nul
		if not errorlevel 1 (
			set "PYCMD=python"
		) else (
			where py >nul 2>nul
			if not errorlevel 1 (
				set "PYCMD=py"
				set "PYARG=-3"
			) else (
				echo Python interpreter not found. Please install Python or create a .venv.
				endlocal
				exit /b 1
			)
		)
	)

	:: If first arg is -m, forward to python -m
	if "%~1"=="-m" (
		if "%~2"=="" (
			echo Missing module name after -m
			endlocal
			exit /b 1
		)
		set "MODULE=%~2"
		shift
		shift
		%PYCMD% %PYARG% -m %MODULE% %*
		set "RC=%ERRORLEVEL%"
		endlocal
		exit /b %RC%
	)

	:: Default: run the CLI script directly
	%PYCMD% %PYARG% "%~dp0\cli.py" %*
	set "RC=%ERRORLEVEL%"
	endlocal
	exit /b %RC%
