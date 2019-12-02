#!/bin/sh
# A simple script to backup a MariaDB/MySQL database in a Docker container.
# (c) 2019 Enrique Matías Sánchez <quique@unizar.es>
# Released under the GNU GPL v3+
#
# This script can be scheduled with a crontab such as
# 42 1 * * * /home/foo/mariadb-backup.sh >> /home/foo/logs/mariadb-backup.log 2>&1

DB_CONTAINER=geoda2_db_1
BACKUPDIR=/moodleapps/geoda2/backups
ROTATION_DAILY=30  # Keep backups for 30 days

docker exec $DB_CONTAINER bash -c 'mysqldump -h localhost -u ${MYSQL_USER} -p${MYSQL_PASSWORD} ${MYSQL_DATABASE} --single-transaction --complete-insert | bzip2' > $BACKUPDIR/db-$(date +%F).sql.bz2

# Rotation could also be achieved via logrotate, but this is simpler.
find $BACKUPDIR -maxdepth 2 -mtime +$ROTATION_DAILY -type f -delete
