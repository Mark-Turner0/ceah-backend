cp /etc/letsencrypt/live/app.markturner.uk/privkey.pem ceah-backend/privkey.pem
cp /etc/letsencrypt/live/app.markturner.uk/fullchain.pem ceah-backend/fullchain.pem
docker stop ceah-backend
docker rm ceah-backend
docker rmi -f ceah-backend
docker build -t ceah-backend ./ceah-backend --no-cache
