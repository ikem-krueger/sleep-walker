deb:
	ln -s debian/ src/DEBIAN
	fakeroot dpkg-deb -b src/
