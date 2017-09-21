clean:
	rm -r src/DEBIAN
	rm *.deb

deb:
	cp -r debian/ src/DEBIAN
	fakeroot dpkg-deb -b src/
	dpkg-name src.deb
