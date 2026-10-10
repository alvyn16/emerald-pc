$ErrorActionPreference = 'Stop'

$root = $PSScriptRoot
$checkout = Join-Path $root 'pokeemerald'
$patchDirectory = Join-Path $root 'patches'
$commit = '731ad5bfd6e6f265508d0efcca0ba42f9dcf5881'
$upstream = 'https://github.com/pret/pokeemerald.git'

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw 'Git no está instalado o no está en PATH.'
}

$patches = @(Get-ChildItem -LiteralPath $patchDirectory -File -Filter '*.patch' | Sort-Object Name)

if (Test-Path -LiteralPath $checkout) {
    if (-not (Test-Path -LiteralPath (Join-Path $checkout '.git'))) {
        throw "La carpeta $checkout ya existe y no es un repositorio Git. No se modificó."
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

$dirty = @(& git -C $checkout status --porcelain --untracked-files=no)
if ($LASTEXITCODE -ne 0 -or $dirty.Count -ne 0) {
    throw "El checkout $checkout tiene cambios locales en archivos seguidos por Git. No se modificó."
}
& git -C $checkout merge-base --is-ancestor $commit HEAD
if ($LASTEXITCODE -ne 0) {
    throw "El checkout existente no desciende del commit fijado $commit. No se modificó."
}

$applied = @(& git -C $checkout rev-list --reverse "$commit..HEAD")
if ($LASTEXITCODE -ne 0 -or $applied.Count -gt $patches.Count) {
    throw 'El checkout contiene commits que no corresponden a la serie de parches. No se modificó.'
}
for ($index = 0; $index -lt $applied.Count; $index++) {
    $expected = @(Get-Content -LiteralPath $patches[$index].FullName | & git patch-id --stable)
    $actual = @(& git -C $checkout show --format= --no-ext-diff $applied[$index] | & git patch-id --stable)
    if ($expected.Count -ne 1 -or $actual.Count -ne 1 -or
        ($expected[0] -split ' ')[0] -ne ($actual[0] -split ' ')[0]) {
        throw "El commit $($applied[$index]) no coincide con $($patches[$index].Name). No se modificó."
    }
}

for ($index = $applied.Count; $index -lt $patches.Count; $index++) {
    $patch = $patches[$index]
    Write-Host "Aplicando $($patch.Name)"
    & git -C $checkout am -- $patch.FullName
    if ($LASTEXITCODE -ne 0) {
        throw "Falló $($patch.Name). Revisa el error y usa 'git -C pokeemerald am --abort' antes de repetir el setup."
    }
}

Write-Host "pokeemerald preparado desde $commit. Parches aplicados: $($patches.Count)."
Write-Host 'Coloca tu propia ROM legal de Pokémon Emerald en inglés en roms/ y conserva el original intacto.'
Write-Host 'Consulta pokeemerald/INSTALL.md para instalar la toolchain y compilar.'
Write-Host 'Para el port PC usa MSYS2 MINGW32 (i686) con GCC y SDL2 de 32 bits.'
Write-Host 'Consulta port/docs/toolchain.md para instalar las versiones requeridas; compila con make -C port exe y verifica con make -C port test.'
