cp /etc/letsencrypt/live/app.markturner.uk/privkey.pem privkey.pem
cp /etc/letsencrypt/live/app.markturner.uk/fullchain.pem fullchain.pem
docker stop ceah-backend
docker rm ceah-backend
docker rmi -f ceah-backend
docker build -t ceah-backend . --no-cache
