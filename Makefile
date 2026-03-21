.PHONY: install run test clean help

help:
	@echo "Hand Gesture Control System - Make Commands"
	@echo "==========================================="
	@echo ""
	@echo "make install    - Tüm bağımlılıkları kur ve ortamı hazırla"
	@echo "make run        - Uygulamayı çalıştır"
	@echo "make test       - Test suite'ini çalıştır"
	@echo "make clean      - Geçici dosyaları temizle"
	@echo "make help       - Bu yardım mesajını göster"

install:
	@echo "Installing Hand Gesture Control System..."
	python install.py

run:
	@echo "Starting Hand Gesture Control System..."
	python launcher.py

test:
	@echo "Running test suite..."
	python test.py

clean:
	@echo "Cleaning up temporary files..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".DS_Store" -delete
	@echo "✅ Cleanup complete"
