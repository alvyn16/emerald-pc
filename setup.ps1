$ErrorActionPreference = 'Stop'

$root = $PSScriptRoot
$checkout = Join-Path $root 'pokeemerald'
$patchDirectory = Join-Path $root 'patches'
$commit = '731ad5bfd6e6f265508d0efcca0ba42f9dcf5881'
$upstream = 'https://github.com/pret/pokeemerald.git'

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw 'Git no está instalado o no está en PATH.'
}

if (Test-Path -LiteralPath $checkout) {
    if (-not (Test-Path -LiteralPath (Join-Path $checkout '.git'))) {
        throw "La carpeta $checkout ya existe y no es un repositorio Git. No se modificó."
    }
    $head = (& git -C $checkout rev-parse HEAD).Trim()
    if ($LASTEXITCODE -ne 0 -or $head -ne $commit) {
        throw "El checkout existente no está en el commit fijado $commit. No se modificó."
    }
} else {
    & git clone --depth 1 --no-checkout $upstream $checkout
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo clonar pret/pokeemerald.' }

    $head = (& git -C $checkout rev-parse HEAD).Trim()
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo leer el commit clonado.' }
    if ($head -ne $commit) {
        & git -C $checkout fetch --depth 1 origin $commit
        if ($LASTEXITCODE -ne 0) { throw "No se pudo obtener el commit fijado $commit." }
    }
    & git -C $checkout checkout --detach $commit
    if ($LASTEXITCODE -ne 0) { throw "No se pudo fijar el checkout en $commit." }
}

$patches = @(Get-ChildItem -LiteralPath $patchDirectory -File -Filter '*.patch' | Sort-Object Name)
foreach ($patch in $patches) {
    Write-Host "Aplicando $($patch.Name)"
    & git -C $checkout am -- $patch.FullName
    if ($LASTEXITCODE -ne 0) {
        throw "Falló $($patch.Name). Revisa el error y usa 'git -C pokeemerald am --abort' antes de repetir el setup."
    }
}

Write-Host "pokeemerald preparado desde $commit. Parches aplicados: $($patches.Count)."
Write-Host 'Coloca tu propia ROM legal de Pokémon Emerald en inglés en roms/ y conserva el original intacto.'
Write-Host 'Consulta pokeemerald/INSTALL.md para instalar la toolchain y compilar.'
