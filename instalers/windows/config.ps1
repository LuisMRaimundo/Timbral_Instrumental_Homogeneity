# Timbral_Instrumental_Homogeneity - Windows installer constants
$script:TimbralInstrumentalHomogeneityConfig = @{
    GitHubRepoUrl   = 'https://github.com/LuisMRaimundo/Timbral_Instrumental_Homogeneity'
    GitHubZipUrl    = 'https://github.com/LuisMRaimundo/Timbral_Instrumental_Homogeneity/archive/refs/heads/main.zip'
    GitHubZipFolder = 'Timbral_Instrumental_Homogeneity-main'
    GitHubBranch    = 'main'
    AppName         = 'Timbral_Instrumental_Homogeneity'
    PythonVersion   = '3.11'
    PythonMinMinor  = 10
    PythonMaxMinor  = 11
    PythonInstallerUrl = 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe'
    InstallRoot     = Join-Path $env:LOCALAPPDATA 'Programs\Timbral_Instrumental_Homogeneity'
    LaunchScript    = 'timbral-instrumental-homogeneity'
}
