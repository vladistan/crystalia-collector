echo Building the image

copy "C:\Program Files\OpenSSL-Win64\bin\openssl.exe" .
copy "C:\Program Files\OpenSSL-Win64\bin\*.dll" .

docker build -f Dockerfile.win -t cr1 .