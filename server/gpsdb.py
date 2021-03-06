import logging
import MySQLdb

from configobj import ConfigObj

class GpsDb(object):

    def __init__(self, config_file, logging_level=logging.ERROR):
        self.logger = logging.getLogger("GpsDB")
        self.logger.setLevel(logging_level)
        self.logger.debug("Loading database config")
        self.db_config = GpsDbConfig(config_file)
        self.db = None
        self.connect()

    def connect(self):
        host = self.db_config.server
        user = self.db_config.user
        password = self.db_config.password
        database = self.db_config.database
        try:
            db = MySQLdb.connect(
                host=host, user=user,
                passwd=password, db=database)
            self.logger.info("Connected to database %s on %s", database, host)
            self.db = db
        except MySQLdb.Error, e:
            self.logger.critical(
                "Unable to connect to db %s on %s as user %s",
                database, host, user)
            self.logger.critical(e)
            raise GpsDbError(str(e))

    def connected(self):
        return self.db is not None

    def get_data_count(self, imei):
        if not self.connected():
            raise GpsDbError()
        self.db.query("SELECT COUNT(*) FROM tracker_data WHERE imei = %s"% imei)
        return self.db.store_result().fetch_row(maxrows=1)[0][0]


    def get_unprocessed_messages(self):
        if not self.connected():
            raise GpsDbError()
        self.db.query("SELECT id, imei, data FROM iridium_raw WHERE processed = 0")
        return self.db.store_result().fetch_row(maxrows=0)

    def get_data(self):
        if not self.connected():
            raise GpsDbError()
        self.db.query("SELECT * FROM tracker_overview ORDER BY imei, timestamp ASC")
        return self.db.store_result().fetch_row(maxrows=0)

    def get_data_imei(self, imei):
        if not self.connected():
            raise GpsDbError()
        cursor = self.db.cursor()
        cursor.execute(
            "SELECT * FROM tracker_overview WHERE imei = %s ORDER BY timestamp ASC", [imei])
        data = cursor.fetchall()
        cursor.close()
        return data

    def get_sats(self, imei=None):
        if not self.connected():
            raise GpsDbError()
        cursor = self.db.cursor()
        if imei is not None:
            cursor.execute(
                "SELECT imei, timestamp, sats FROM tracker_data WHERE imei = %s ORDER BY timestamp ASC", [imei])
        else:
            cursor.execute(
                "SELECT imei, timestamp, sats FROM tracker_data ORDER BY timestamp ASC")
        data = cursor.fetchall()
        cursor.close()
        return data

    def get_altitude(self, imei=None):
        if not self.connected():
            raise GpsDbError()
        cursor = self.db.cursor()
        if imei is not None:
            cursor.execute(
                "SELECT imei, timestamp, altitude FROM tracker_data WHERE imei = %s ORDER BY timestamp ASC", [imei])
        else:
            cursor.execute(
                "SELECT imei, timestamp, altitude FROM tracker_data ORDER BY timestamp ASC")
        data = cursor.fetchall()
        cursor.close()
        return data


    def get_temperature(self, imei=None):
        if not self.connected():
            raise GpsDbError()
        cursor = self.db.cursor()
        if imei is not None:
            cursor.execute(
                "SELECT imei, timestamp, temperature  FROM tracker_data WHERE imei = %s AND temperature IS NOT NULL ORDER BY timestamp ASC", [imei])
        else:
            cursor.execute(
                "SELECT imei, timestamp, temperature FROM tracker_data WHERE temperature IS NOT NULL ORDER BY timestamp ASC")
        data = cursor.fetchall()
        cursor.close()
        return data

    def get_latest_data(self):
        if not self.connected():
            raise GpsDbError()
        self.db.query("SELECT Glacier, tracker_overview.imei,tracker_overview.timestamp, longitude, latitude, altitude, quality, hdop, sats,temperature FROM (SELECT MAX(timestamp) AS timestamp, imei FROM `tracker_data` GROUP BY `imei`) AS latest, tracker_overview WHERE latest.imei = tracker_overview.imei AND latest.timestamp = tracker_overview.timestamp ")
        return self.db.store_result().fetch_row(maxrows=0)

    def get_unprocessed_message_count(self):
        return len(self.get_unprocessed_messages())

    def set_processed(self, msg_id):
        if not self.connected():
            raise GpsDbError()
        cursor = self.db.cursor()
        self.logger.debug("marking %d", msg_id)
        cursor.execute(
            "UPDATE iridium_raw SET processed = 1 WHERE id = %s",
            [msg_id])
        cursor.close()
        self.logger.debug("Message %d marked as processed", msg_id)
        self.db.commit()

    def save_position(
            self, imei, timestamp, lat, lon, alt, qual, hdop, sats, temp=None):
        if not self.connected():
            raise GpsDbError()
        cursor = self.db.cursor()
        if temp is None:
            cursor.execute(
                "INSERT IGNORE INTO tracker_data (imei, timestamp, longitude, latitude, altitude, quality, hdop, sats) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (imei, str(timestamp), lon, lat, alt, qual, hdop, sats))
        else: # new format doesn't have quality or hdop
            cursor.execute(
                "INSERT IGNORE INTO tracker_data (imei, timestamp, longitude, latitude, altitude, sats, temperature) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (imei, str(timestamp), lon, lat, alt, sats, temp))
        cursor.close()
        self.db.commit()
        self.logger.debug("Position saved")


class GpsDbConfig(object):
    def __init__(self, config_file):
        try:
            config = ConfigObj(config_file)
            self.database = config["database"]
            self.server = config["server"]
            self.user = config["user"]
            self.password = config["pass"]
        except KeyError:
            raise ConfigError("Invalid config File")


class ConfigError(Exception):
    """
        An error for when something has gone wrong reading the config
    """
    pass

class GpsDbError(Exception):
    pass
