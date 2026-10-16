lines = [
    '@echo off',
    'cd /d "%~dp0"',
    'title GhostChain MV',
    'echo Starting GhostChain MV server... keep this window open while watching.',
    'where python >nul 2>nul',
    'if errorlevel 1 goto trypy',
    'python tools\\serve.py',
    'goto end',
    ':trypy',
    'py tools\\serve.py',
    ':end',
    'echo.',
    'echo Server stopped or failed to start. Press any key to close.',
    'pause >nul',
    '',
]
import os
p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'play_MV.bat')
open(p, 'wb').write('\r\n'.join(lines).encode('ascii'))
d = open(p, 'rb').read()
print('CRLF', d.count(b'\r\n'), 'LF', d.count(b'\n'))
