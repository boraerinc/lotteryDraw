import logging
import mysql.connector
from mysql.connector import Error
from datetime import datetime, timedelta
import mailchimp_marketing as Mailchimp
from mailchimp_marketing.api_client import ApiClientError
import sys
import random

logging.basicConfig()

def send_email(user_email, show_name, win):
    mailchimp_client = Mailchimp.Client()
    mailchimp_client.set_config({
        "api_key": "YOUR_MAILCHIMP_API_KEY",
        "server": "YOUR_SERVER_PREFIX"
    })

    list_id = "YOUR_MAILCHIMP_LIST_ID"

    if(win):
        message = "Congratulations, you have won a ticket to {}".format(show_name)
    else:
        message = "Sorry, you have failed to redeem your ticket to {}, your ticket will be given to someone else".format(show_name)
    try:
        response = mailchimp_client.messages.send({"message": message, "email_address": user_email, "list_id": list_id})
        print("Email sent successfully: ", response)
        logging.info(f"Email sent to {user_email}")
    except ApiClientError as error:
        print("Error sending email: ", error.text)
        logging.error(f"Error sending email to {user_email}: {error.text}")

def create_database_connection():
    try:
        connection = mysql.connector.connect(
            host='your_host',
            database='your_database',
            user='your_username',
            password='your_password'
        )
        if connection.is_connected():
            return connection
    except Error as e:
        print("Error while connecting to MySQL", e)
        logging.error(f"Database error: {e}")
        return None


def draw_winners():
    logging.info("Starting the lottery draw")
    connection = create_database_connection()
    if connection is None:
        return
    try:
        cursor = connection.cursor(dictionary=True)
        tomorrow_date = (datetime.now() + timedelta(days=1)).date()

        # List of shows happening day after
        cursor.execute("SELECT show_id, show_name, available_tickets FROM shows WHERE DATE(time) = %s", (tomorrow_date,))
        shows = cursor.fetchall()

        for show in shows:
            show_id = show['show_id']
            show_name = show['show_name']
            available_tickets = show['available_tickets']

            #Query to pick winners from each show (Can be inefficient with large datasets
            # winners_query = """
            #     SELECT user_id FROM lottery_entries
            #     WHERE show_id = %s
            #     ORDER BY RAND()
            #     LIMIT %s
            #     """
            # cursor.execute(winners_query, (show_id, available_tickets))
            # winners = cursor.fetchall()

            # Fetch eligible entries
            cursor.execute("SELECT user_id FROM lottery_entries WHERE show_id = %s", (show_id,))
            entries = cursor.fetchall()
            #More efficient randomization:
            if len(entries) > 0:
                winners = random.sample(entries, min(len(entries), available_tickets))

                for winner in winners:
                    user_id = winner['user_id']
                    #Query to enter the winners into the 'winners' table
                    cursor.execute("""
                                    INSERT INTO winners (show_id, user_id, ticket_redeemed) 
                                    VALUES (%s, %s, FALSE)
                                    """, (show_id, user_id))

                    cursor.execute("SELECT email FROM users WHERE user_id = %s", (user_id))
                    user_email = cursor.fetchone()['email']
                    #Inform users
                    send_email(user_email, show_name, True)
                    # Clear from 'entries' when an entry wins
                    cursor.execute("""
                        DELETE FROM lottery_entries
                        WHERE show_id = %s AND user_id = %s
                    """, (show_id, user_id))
            connection.commit()
        cursor.close()

    except Error as e:
        print(f"Error: {e}")
        logging.error(f"Database error: {e}")
        connection.rollback()
    finally:
        if connection.is_connected():
            connection.close()
        logging.info("Lottery draw completed")

def manage_winners():
    logging.info("Starting lottery management")
    connection = create_database_connection()
    if connection is None:
        return

    try:
        cursor = connection.cursor(dictionary=True)
        tomorrow_date = (datetime.now() + timedelta(days=1)).date()

        # List of shows happening day after
        cursor.execute("SELECT show_id, show_name, available_tickets FROM shows WHERE DATE(time) = %s", (tomorrow_date,))
        shows = cursor.fetchall()

        for show in shows:
            show_id = show['show_id']
            show_name = show['show_name']

            # Check ticket redemption
            cursor.execute("""
                SELECT user_id FROM winners 
                WHERE show_id = %s AND ticket_redeemed = FALSE
            """, (show_id,))
            unredeemed_winners = cursor.fetchall()
            unredeemed_count = len(unredeemed_winners)

            for winner in unredeemed_winners:
                cursor.execute("SELECT email FROM users WHERE user_id = %s", (winner['user_id'],))
                user_email = cursor.fetchone()['email']
                send_email(user_email, show_name, False)

            # Update number of available tickets
            cursor.execute("""
                    UPDATE shows SET available_tickets = available_tickets + %s 
                    WHERE show_id = %s
                """, (unredeemed_count, show_id))

            # Clear 'winners' table for this show
            cursor.execute("DELETE FROM winners WHERE show_id = %s", (show_id,))
            connection.commit()
        cursor.close()
    except Error as e:
        print(f"Error: {e}")
        logging.error(f"Database error: {e}")
        connection.rollback()
    finally:
        if connection.is_connected():
            connection.close()
        logging.info("Lottery management completed")

def manage_and_redraw_winners():
    manage_winners()
    draw_winners()



if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == 'draw':
            draw_winners()
        elif sys.argv[1] == 'manage_draw':
            manage_winners()
            draw_winners()
        elif sys.argv[1] == 'manage':
            manage_winners()

"""
The code to be added to the CRON table is as follows:

0 12 * * * /path/to/python /path/to/your_script.py draw >> /path/to/logfile.log 2>&1
0 13,14 * * * /path/to/python /path/to/your_script.py manage_draw >> /path/to/logfile.log 2>&1
0 15 * * * /path/to/python /path/to/your_script.py manage >> /path/to/logfile.log 2>&1

"""