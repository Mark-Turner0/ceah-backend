mkdir /etc/cron.hourly
echo "#!/bin/sh" > /etc/cron.hourly/update.sh
echo "python3 -u /ceah-backend/update.py $DB_USERNAME $DB_PASSWORD" >> /etc/cron.hourly/update.sh
chmod +x /etc/cron.hourly/update.sh
python3 -u main.py $DB_USERNAME $DB_PASSWORD
