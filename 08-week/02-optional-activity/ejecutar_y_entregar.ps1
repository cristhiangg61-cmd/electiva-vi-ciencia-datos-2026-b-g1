# ejecutar_y_entregar.ps1
# Semana 8 - Pipeline ETL (Ciencia de Datos, CORHUILA)
#
# Que hace, en orden:
#   1. Busca Python (py / python / python3) y comprueba que funcione.
#   2. Instala 'requests'.
#   3. Corre las pruebas offline (18 pruebas).
#   4. Ejecuta api_clima.py contra Open-Meteo (REQUIERE INTERNET) y guarda la salida.
#   5. Pega esa salida real en la seccion 4 de Actividad_Semana8_CGG.md.
#   6. Revisa que no quede el marcador y muestra el estado de git.
#   7. Con -Push: git add, commit y push. Sin -Push solo muestra los comandos.
#
# Uso (PowerShell, dentro de la carpeta 08-week\02-optional-activity de tu fork):
#   powershell -ExecutionPolicy Bypass -File .\ejecutar_y_entregar.ps1
#   powershell -ExecutionPolicy Bypass -File .\ejecutar_y_entregar.ps1 -Push
#
# El archivo es ASCII a proposito (sin tildes) para que PowerShell 5.1 no lo
# lea mal al pasarlo entre equipos.

param(
    [switch]$Push,
    [string]$Mensaje = "Entrega semana 08"
)

$ErrorActionPreference = "Continue"  # los errores se manejan con $LASTEXITCODE
Set-Location -Path $PSScriptRoot

function Escribir($texto, $color = "Cyan") { Write-Host $texto -ForegroundColor $color }
function Fallar($texto) { Write-Host "ERROR: $texto" -ForegroundColor Red; exit 1 }

# --- 1. Python ---------------------------------------------------------------
$py = $null
foreach ($candidato in @("py", "python", "python3")) {
    if (Get-Command $candidato -ErrorAction SilentlyContinue) {
        & $candidato --version *> $null
        if ($LASTEXITCODE -eq 0) { $py = $candidato; break }
    }
}
if (-not $py) { Fallar "No se encontro Python. Instalalo desde python.org (3.10 o superior) y marca 'Add to PATH'." }
Escribir "[1/6] Python encontrado: $py ($( & $py --version ))"

# --- 2. Dependencias ---------------------------------------------------------
& $py -c "import requests" *> $null
if ($LASTEXITCODE -eq 0) {
    Escribir "[2/6] 'requests' ya esta instalado."
} else {
    Escribir "[2/6] Instalando dependencias (requests)..."
    & $py -m pip install --disable-pip-version-check -q -r requirements.txt
    if ($LASTEXITCODE -ne 0) { Fallar "No se pudo instalar 'requests'. Revisa tu conexion a internet." }
}

# --- 3. Pruebas offline ------------------------------------------------------
Escribir "[3/6] Corriendo pruebas offline..."
& $py test_api_clima.py
if ($LASTEXITCODE -ne 0) { Fallar "Fallaron las pruebas. No se continua." }

# --- 4. Ejecucion real contra la API -----------------------------------------
Escribir "[4/6] Consultando Open-Meteo (requiere internet)..."
if (Test-Path "salida_api.txt") { Remove-Item "salida_api.txt" -Force }
& $py api_clima.py --guardar-salida salida_api.txt
if ($LASTEXITCODE -ne 0) { Fallar "La consulta a la API fallo (revisa internet o el mensaje de arriba). El entregable NO se modifico." }

# --- 5. Pegar la salida real en el entregable --------------------------------
Escribir "[5/6] Pegando la salida real en Actividad_Semana8_CGG.md (seccion 4)..."
& $py insertar_salida.py
if ($LASTEXITCODE -ne 0) { Fallar "No se pudo insertar la salida en el entregable." }

if (Select-String -Path "Actividad_Semana8_CGG.md" -Pattern "PEGAR AQU" -Quiet) {
    Fallar "Sigue apareciendo el marcador PEGAR AQUI en el entregable."
}

# --- 6. Git ------------------------------------------------------------------
Escribir "[6/6] Estado de git:"
if (-not ($PSScriptRoot -match "08-week")) {
    Write-Host "AVISO: esta carpeta no esta dentro de 08-week\ de tu fork. Copia los archivos ahi antes del push." -ForegroundColor Yellow
}
$hayGit = Get-Command git -ErrorAction SilentlyContinue
if (-not $hayGit) {
    Write-Host "AVISO: git no esta instalado o no esta en el PATH. Haz el push desde otro equipo o instala Git." -ForegroundColor Yellow
} else {
    & git rev-parse --show-toplevel *> $null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "AVISO: esta carpeta no esta dentro de un repositorio git (tu fork clonado)." -ForegroundColor Yellow
    } else {
        & git status --short .
        if ($Push) {
            Escribir "Haciendo commit y push..."
            & git add .
            & git commit -m $Mensaje
            & git push
            if ($LASTEXITCODE -ne 0) { Fallar "git push fallo. Revisa tu sesion de GitHub." }
            Escribir "Listo: entrega subida." "Green"
        } else {
            Write-Host ""
            Write-Host "Para subir la entrega (o vuelve a correr este script con -Push):"
            Write-Host "  git add ."
            Write-Host "  git commit -m `"$Mensaje`""
            Write-Host "  git push"
        }
    }
}

Write-Host ""
Escribir "Pendiente manual:" "Yellow"
Write-Host "  - Abrir Actividad_Semana8_CGG.md en GitHub y confirmar que el diagrama se ve."
Write-Host "  - Confirmar que tu repo de perfil tiene el bloque CONFIG (FULL_NAME + GITHUB_USER)."
