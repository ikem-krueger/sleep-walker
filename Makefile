deb:
	cp -r debian/ src/DEBIAN
	fakeroot dpkg-deb -b src/
