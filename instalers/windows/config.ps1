# Orchomogeneity — Windows installer constants
$script:OrchomogeneityConfig = @{
    GitHubRepoUrl   = 'https://github.com/LuisMRaimundo/orchomogeneity'
    GitHubZipUrl    = 'https://github.com/LuisMRaimundo/orchomogeneity/archive/refs/heads/main.zip'
    GitHubZipFolder = 'orchomogeneity-main'
    GitHubBranch    = 'main'
    AppName         = 'Orchomogeneity'
    PythonVersion   = '3.11'
    PythonMinMinor  = 10
    PythonMaxMinor  = 11
    PythonInstallerUrl = 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe'
    InstallRoot     = Join-Path $env:LOCALAPPDATA 'Programs\Orchomogeneity'
    LaunchScript    = 'homogeneity-analyser'
}
