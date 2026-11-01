param(
    [Parameter(Position=0)]
    [ValidateSet('test', 'verify', 'lint', 'build', 'contracts', 'e2e', 'up', 'down', 'help')]
    [string]$Command = 'help'
)

function Show-Help {
    Write-Host '==========================================================' -ForegroundColor Cyan
    Write-Host ' FRS V7.1 K2 Production Monorepo Management (PowerShell)' -ForegroundColor Cyan
    Write-Host '==========================================================' -ForegroundColor Cyan
    Write-Host ''
    Write-Host 'Commands:'
    Write-Host '  .\run.ps1 test        Run all tests across backend, Playwright E2E, mobile, admin, contracts'
    Write-Host '  .\run.ps1 e2e         Run Playwright browser automation E2E suite'
    Write-Host '  .\run.ps1 verify      Run mathematical invariant and acceptance suite'
    Write-Host '  .\run.ps1 lint        Run Dart and TypeScript static analysis'
    Write-Host '  .\run.ps1 build       Compile Next.js admin console production build'
    Write-Host '  .\run.ps1 contracts   Verify OpenAPI / TypeScript contracts'
    Write-Host '  .\run.ps1 up          Launch Docker Compose services in background'
    Write-Host '  .\run.ps1 down        Tear down Docker Compose containers'
    Write-Host ''
}

switch ($Command) {
    'test' {
        Write-Host '[1/5] Running backend unit & security pytest...' -ForegroundColor Green
        Push-Location backend
        python -m pytest tests/ -k "not playwright" -v
        Pop-Location

        Write-Host '[2/5] Running Playwright browser E2E suite...' -ForegroundColor Green
        Push-Location backend
        python -m pytest tests/test_playwright_admin_console.py -v
        Pop-Location

        Write-Host '[3/5] Running admin console typecheck...' -ForegroundColor Green
        npm --prefix apps/admin_console run typecheck

        Write-Host '[4/5] Running mobile Dart static analyzer...' -ForegroundColor Green
        dart analyze apps/teacher_mobile

        Write-Host '[5/5] Validating shared TypeScript contracts...' -ForegroundColor Green
        node apps/admin_console/node_modules/typescript/bin/tsc --noEmit packages/contracts/src/index.ts

        Write-Host 'All monorepo test gates passed successfully!' -ForegroundColor Cyan
    }

    'e2e' {
        Write-Host 'Running Playwright browser automation E2E suite...' -ForegroundColor Green
        Push-Location backend
        python -m pytest tests/test_playwright_admin_console.py -v
        Pop-Location
    }

    'verify' {
        Write-Host 'Executing FRS V7.1 acceptance and mathematical invariant suite...' -ForegroundColor Green
        python backend/verify_backend.py
    }

    'lint' {
        Write-Host 'Analyzing teacher mobile...' -ForegroundColor Green
        dart analyze apps/teacher_mobile

        Write-Host 'Typechecking admin console...' -ForegroundColor Green
        npm --prefix apps/admin_console run typecheck
    }

    'build' {
        Write-Host 'Building Next.js Admin Console...' -ForegroundColor Green
        npm --prefix apps/admin_console run build
    }

    'contracts' {
        Write-Host 'Validating TypeScript contracts...' -ForegroundColor Green
        node apps/admin_console/node_modules/typescript/bin/tsc --noEmit packages/contracts/src/index.ts
    }

    'up' {
        Write-Host 'Starting local Docker Compose stack...' -ForegroundColor Green
        docker compose up -d
    }

    'down' {
        Write-Host 'Stopping local Docker Compose stack...' -ForegroundColor Green
        docker compose down
    }

    default {
        Show-Help
    }
}
