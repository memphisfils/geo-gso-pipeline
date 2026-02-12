# install.ps1 - Script d'installation automatique pour GEO/GSO Pipeline
# Compatible: Windows 10/11 avec PowerShell

$ErrorActionPreference = "Stop"

# Couleurs
function Write-Info { Write-Host "ℹ $args" -ForegroundColor Blue }
function Write-Success { Write-Host "✓ $args" -ForegroundColor Green }
function Write-Warning { Write-Host "⚠ $args" -ForegroundColor Yellow }
function Write-Error { Write-Host "✗ $args" -ForegroundColor Red }

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Blue
Write-Host "║  GEO/GSO Pipeline - Installation Automatique             ║" -ForegroundColor Blue
Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Blue
Write-Host ""

# Vérifier PowerShell version
Write-Info "Vérification de PowerShell..."
$psVersion = $PSVersionTable.PSVersion.Major
if ($psVersion -lt 5) {
    Write-Error "PowerShell 5+ requis. Version actuelle: $psVersion"
    exit 1
}
Write-Success "PowerShell $psVersion trouvé"

# Vérifier Python
Write-Info "Vérification de Python..."

try {
    $pythonVersion = python --version 2>&1
    Write-Success "$pythonVersion trouvé"
} catch {
    Write-Error "Python n'est pas installé"
    Write-Host ""
    Write-Host "Installation Python:"
    Write-Host "  1. Télécharger depuis https://www.python.org/downloads/"
    Write-Host "  2. Cocher 'Add Python to PATH' pendant l'installation"
    exit 1
}

# Vérifier version Python
$versionString = (python -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
$versionParts = $versionString -split '\.'
$major = [int]$versionParts[0]
$minor = [int]$versionParts[1]

if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 8)) {
    Write-Error "Python 3.8+ requis. Version actuelle: $versionString"
    exit 1
}

# Créer environnement virtuel
Write-Info "Création de l'environnement virtuel..."

if (Test-Path "venv") {
    Write-Warning "Le dossier venv existe déjà"
    $response = Read-Host "Supprimer et recréer? (y/N)"
    if ($response -eq "y" -or $response -eq "Y") {
        Remove-Item -Recurse -Force venv
        python -m venv venv
        Write-Success "Environnement virtuel recréé"
    } else {
        Write-Info "Utilisation de l'environnement existant"
    }
} else {
    python -m venv venv
    Write-Success "Environnement virtuel créé"
}

# Activer venv
Write-Info "Activation de l'environnement virtuel..."
& .\venv\Scripts\Activate.ps1

# Upgrade pip
Write-Info "Mise à jour de pip..."
python -m pip install --upgrade pip --quiet
Write-Success "pip mis à jour"

# Installer dépendances
Write-Info "Installation des dépendances..."
Write-Warning "Cette étape peut prendre 5-10 minutes (téléchargement des modèles)"

pip install -r requirements.txt --quiet
Write-Success "Dépendances installées"

# Pré-télécharger modèles
Write-Info "Pré-téléchargement des modèles d'embeddings..."
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')" 2>$null
Write-Success "Modèles téléchargés"

# Créer .env si nécessaire
if (-not (Test-Path ".env")) {
    Write-Info "Création du fichier .env..."
    Copy-Item .env.example .env
    Write-Success ".env créé depuis .env.example"
    Write-Warning "⚠️  N'oubliez pas d'éditer .env avec vos clés API"
} else {
    Write-Info ".env existe déjà"
}

# Créer dossier de sortie
New-Item -ItemType Directory -Force -Path out | Out-Null
Write-Success "Dossier de sortie créé: .\out"

# Test rapide
Write-Info "Test de l'installation..."
python generate.py --help | Out-Null
Write-Success "Installation vérifiée"

# Afficher les prochaines étapes
Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║           Installation terminée avec succès !             ║" -ForegroundColor Green
Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "Prochaines étapes:" -ForegroundColor Blue
Write-Host ""
Write-Host "1. Activer l'environnement:"
Write-Host "   .\venv\Scripts\Activate.ps1" -ForegroundColor Yellow
Write-Host ""
Write-Host "2. Éditer le fichier .env avec vos clés API:"
Write-Host "   notepad .env" -ForegroundColor Yellow
Write-Host ""
Write-Host "3. Test rapide (gratuit, sans API):"
Write-Host "   python generate.py --input topics_single.json --output .\out --demo" -ForegroundColor Yellow
Write-Host ""
Write-Host "4. Exécution complète (requiert API key):"
Write-Host "   python generate.py --input topics.json --output .\out" -ForegroundColor Yellow
Write-Host ""
Write-Host "Documentation complète: README.md" -ForegroundColor Blue
Write-Host ""
