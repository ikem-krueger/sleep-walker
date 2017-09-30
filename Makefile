clean:
	rm -r src/DEBIAN
	rm *.deb

deb:
	cp -r debian/ src/DEBIAN
	find src/ -type f -not -path "src/DEBIAN/*" -exec md5sum '{}' \; > src/DEBIAN/md5sum
	sed -i 's|src/||' src/DEBIAN/md5sum
	fakeroot dpkg-deb -b src/
	dpkg-name src.deb
