# PowerShell script to update Claude Code to use the current development version of zen-mcp-server

Write-Host "Updating Claude Code to use current development version of zen-mcp-server..." -ForegroundColor Cyan

# Get the absolute path of the current directory
$CurrentDir = Get-Location
$ServerPath = Join-Path $CurrentDir "server.py"
$PythonPath = Join-Path $CurrentDir ".zen_venv\Scripts\python.exe"

Write-Host "Current directory: $CurrentDir" -ForegroundColor Green
Write-Host "Server path: $ServerPath" -ForegroundColor Green
Write-Host "Python path: $PythonPath" -ForegroundColor Green

# Check if virtual environment exists
if (!(Test-Path $PythonPath)) {
    Write-Warning "Virtual environment Python not found at $PythonPath"
    Write-Host "Please run .\run-server.ps1 first to set up the environment" -ForegroundColor Yellow
    exit 1
}

# Check if server.py exists
if (!(Test-Path $ServerPath)) {
    Write-Error "server.py not found at $ServerPath"
    exit 1
}

# Update Claude CLI configuration if available
if (Get-Command "claude" -ErrorAction SilentlyContinue) {
    Write-Host "Updating Claude CLI configuration..." -ForegroundColor Yellow
    
    try {
        # Remove existing zen configuration
        claude mcp remove zen 2>$null
        
        # Add current development version
        claude mcp add -s user zen $PythonPath $ServerPath
        
        Write-Host "Claude CLI updated to use current development version" -ForegroundColor Green
    }
    catch {
        Write-Warning "Could not update Claude CLI automatically: $_"
        Write-Host "Please manually update Claude CLI with:" -ForegroundColor Yellow
        Write-Host "  claude mcp remove zen" -ForegroundColor White
        Write-Host "  claude mcp add -s user zen $PythonPath $ServerPath" -ForegroundColor White
    }
} else {
    Write-Warning "Claude CLI not found in PATH"
}

# Update Claude Desktop configuration
$claudeConfigPath = "$env:APPDATA\Claude\claude_desktop_config.json"

if (Test-Path $claudeConfigPath) {
    Write-Host "Updating Claude Desktop configuration..." -ForegroundColor Yellow
    
    try {
        # Create backup
        $backupPath = $claudeConfigPath + ".backup.$(Get-Date -Format 'yyyyMMdd_HHmmss')"
        Copy-Item $claudeConfigPath $backupPath
        Write-Host "Backup created: $backupPath" -ForegroundColor Gray
        
        # Read existing config
        $config = Get-Content $claudeConfigPath -Raw | ConvertFrom-Json
        
        # Ensure mcpServers exists
        if (!$config.PSObject.Properties["mcpServers"]) {
            $config | Add-Member -MemberType NoteProperty -Name "mcpServers" -Value (New-Object PSObject)
        }
        
        # Update zen server configuration
        $zenConfig = @{
            command = $PythonPath
            args = @($ServerPath)
            type = "stdio"
        }
        
        $config.mcpServers | Add-Member -MemberType NoteProperty -Name "zen" -Value $zenConfig -Force
        
        # Write updated config
        $config | ConvertTo-Json -Depth 10 | Out-File $claudeConfigPath -Encoding UTF8
        
        Write-Host "Claude Desktop configuration updated" -ForegroundColor Green
    }
    catch {
        Write-Warning "Could not update Claude Desktop automatically: $_"
        Write-Host "Please manually update Claude Desktop configuration at:" -ForegroundColor Yellow
        Write-Host "  $claudeConfigPath" -ForegroundColor White
    }
} else {
    Write-Warning "Claude Desktop configuration not found at $claudeConfigPath"
}

Write-Host ""
Write-Host "Configuration updated successfully!" -ForegroundColor Green
Write-Host "Please restart Claude Code to apply the changes." -ForegroundColor Yellow
Write-Host ""
Write-Host "Your Claude Code will now use:" -ForegroundColor Cyan
Write-Host "  Python: $PythonPath" -ForegroundColor White
Write-Host "  Server: $ServerPath" -ForegroundColor White
Write-Host ""
Write-Host "All changes you make to the server code will now be reflected immediately after restart." -ForegroundColor Green
