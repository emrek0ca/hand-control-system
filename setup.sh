#!/bin/bash
# 🚀 Hand Gesture Control System - Hızlı Kurulum Scripti (macOS/Linux)

echo "╔════════════════════════════════════════════════════════════╗"
echo "║        🎯 Hand Gesture Control System                      ║"
echo "║        Hızlı Kurulum Scripti                              ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Renkleri tanımla
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Python sürümünü kontrol et
echo -e "${BLUE}📝 Python sürümü kontrol ediliyor...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 bulunamadı. Lütfen Python 3.8+ kur.${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✅ Python $PYTHON_VERSION bulundu${NC}"

# Sanal ortam oluştur (isteğe bağlı)
echo ""
read -p "Sanal ortam oluştur? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}🔧 Sanal ortam oluşturuluyor...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    echo -e "${GREEN}✅ Sanal ortam aktif${NC}"
fi

# Bağımlılıkları kur
echo ""
echo -e "${BLUE}📦 Bağımlılıklar kurulmaya başlanıyor...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Tüm bağımlılıklar başarıyla kuruldu${NC}"
else
    echo -e "${RED}❌ Bağımlılıklar kurulurken hata oluştu${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}📁 Runtime klasörleri ilk açılışta kullanıcı dizininde oluşturulacak${NC}"

# Testleri çalıştır (isteğe bağlı)
echo ""
read -p "Sistem testlerini çalıştır? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}🧪 Testler çalıştırılıyor...${NC}"
    python3 test.py
fi

# Tamamlandı
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗"
echo "║        ✅ KURULUM BAŞARIYLA TAMAMLANDI!                 ║"
echo "╚════════════════════════════════════════════════════════════╝${NC}"

echo ""
echo -e "${YELLOW}📚 SONRAKI ADIMLAR:${NC}"
echo ""
echo "1. 🚀 Uygulamayı çalıştır:"
echo -e "   ${BLUE}python3 launcher.py${NC}"
echo ""
echo "2. 🎓 Dokümantasyonu oku:"
echo -e "   ${BLUE}cat QUICKSTART.md${NC}"
echo ""
echo "3. 🎬 Demosunu göz at:"
echo -e "   ${BLUE}python3 advanced_demo.py${NC}"
echo ""
echo "4. 📋 İnteraktif menü:"
echo -e "   ${BLUE}python3 start.py${NC}"
echo ""

echo -e "${YELLOW}💡 İpucu:${NC} İlk kez kullanıyorsanız QUICKSTART.md dosyasını okuyun!"
echo ""
