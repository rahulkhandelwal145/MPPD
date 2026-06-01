import subprocess
from pathlib import Path

log_path = Path('mysql_command.log')
cmd = [
    r'C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe',
    '-u', 'root',
    '-pPhamysql#145',
    '-h', 'localhost',
    '-P', '3306',
    '-e', 'CREATE DATABASE IF NOT EXISTS mpscorer CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;'
]
result = subprocess.run(cmd, capture_output=True, text=True)
log_path.write_text('STDOUT:\n' + result.stdout + '\nSTDERR:\n' + result.stderr + '\nRETURNCODE:\n' + str(result.returncode) + '\n')
print('WROTE', log_path)
