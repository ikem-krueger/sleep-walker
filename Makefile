PKG_NAME=sleep-walker

deb:
	mkdir -p ${PKG_NAME}/DEBIAN
	cp debian/* ${PKG_NAME}/DEBIAN
	cp -r src/ ${PKG_NAME}/
	fakeroot dpkg-deb --build ${PKG_NAME}
