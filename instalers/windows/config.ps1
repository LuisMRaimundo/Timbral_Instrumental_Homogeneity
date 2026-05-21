# Orchomogeneity - Windows installer constants
$script:OrchomogeneityConfig = @{
    GitHubRepoUrl   = 'https://github.com/LuisMRaimundo/Orchomogeneity_Analyser'
    GitHubZipUrl    = 'https://github.com/LuisMRaimundo/Orchomogeneity_Analyser/archive/refs/heads/main.zip'
    GitHubZipFolder = 'Orchomogeneity_Analyser-main'
    GitHubBranch    = 'main'
    AppName         = 'Orchomogeneity'
    PythonVersion   = '3.11'
    PythonMinMinor  = 10
    PythonMaxMinor  = 11
    PythonInstallerUrl = 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe'
    InstallRoot     = Join-Path $env:LOCALAPPDATA 'Programs\Orchomogeneity'
    LaunchScript    = 'homogeneity-analyser'
}
