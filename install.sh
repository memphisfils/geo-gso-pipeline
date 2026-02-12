#!/bin/bash
# install.sh - Script d'installation automatique pour GEO/GSO Pipeline
# Compatible: Linux, macOS

set -e  # Exit on error

# Couleurs pour output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║  GEO/GSO Pipeline - Installation Automatique             ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Fonction pour afficher les messages
log_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

# Détecter OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="Linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macOS"
else
    log_error "OS non supporté: $OSTYPE"
    exit 1
fi

log_info "OS détecté: $OS"

# Vérifier Python
log_info "Vérification de Python..."

if ! command -v python3 &> /dev/null; then
    log_error "Python 3 n'est pas installé"
    echo ""
    echo "Installation Python:"
    if [[ "$OS" == "Linux" ]]; then
        echo "  sudo apt update && sudo apt install python3 python3-pip python3-venv"
    else
        echo "  brew install python3"
    fi
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
log_success "Python $PYTHON_VERSION trouvé"

# Vérifier version Python
REQUIRED_VERSION="3.8"
if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    log_error "Python 3.8+ requis. Version actuelle: $PYTHON_VERSION"
    exit 1
fi

# Créer environnement virtuel
log_info "Création de l'environnement virtuel..."

if [ -d "venv" ]; then
    log_warning "Le dossier venv existe déjà"
    read -p "Supprimer et recréer? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf venv
        python3 -m venv venv
        log_success "Environnement virtuel recréé"
    else
        log_info "Utilisation de l'environnement existant"
    fi
else
    python3 -m venv venv
    log_success "Environnement virtuel créé"
fi

# Activer venv
log_info "Activation de l'environnement virtuel..."
source venv/bin/activate

# Upgrade pip
log_info "Mise à jour de pip..."
pip install --upgrade pip --quiet
log_success "pip mis à jour"

# Installer dépendances
log_info "Installation des dépendances..."
log_warning "Cette étape peut prendre 5-10 minutes (téléchargement des modèles)"

pip install -r requirements.txt --quiet
log_success "Dépendances installées"

# Pré-télécharger modèles
log_info "Pré-téléchargement des modèles d'embeddings..."
python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')" 2>/dev/null
log_success "Modèles téléchargés"

# Créer .env si nécessaire
if [ ! -f ".env" ]; then
    log_info "Création du fichier .env..."
    cp .env.example .env
    log_success ".env créé depuis .env.example"
    log_warning "⚠️  N'oubliez pas d'éditer .env avec vos clés API"
else
    log_info ".env existe déjà"
fi

# Créer dossier de sortie
mkdir -p out
log_success "Dossier de sortie créé: ./out"

# Test rapide
log_info "Test de l'installation..."
python3 generate.py --help > /dev/null 2>&1
log_success "Installation vérifiée"

# Afficher les prochaines étapes
echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           Installation terminée avec succès !             ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Prochaines étapes:${NC}"
echo ""
echo -e "1. Activer l'environnement:"
echo -e "   ${YELLOW}source venv/bin/activate${NC}"
echo ""
echo -e "2. Éditer le fichier .env avec vos clés API:"
echo -e "   ${YELLOW}nano .env${NC}"
echo ""
echo -e "3. Test rapide (gratuit, sans API):"
echo -e "   ${YELLOW}python generate.py --input topics_single.json --output ./out --demo${NC}"
echo ""
echo -e "4. Exécution complète (requiert API key):"
echo -e "   ${YELLOW}python generate.py --input topics.json --output ./out${NC}"
echo ""
echo -e "${BLUE}Documentation complète:${NC} README.md"
echo ""
