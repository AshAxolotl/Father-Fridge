# art contest DONE (ADD A COMMAND WITH 3 OPTIONS FOR CREATING A Art Contest: <THEME/winner announcement/ theme announcement>)

# ROAD MAP:
1. learn sql basics DONE
2. switch to sql (make sure the sql works with the bot being in multiable guilds)
2.1: create a database DONE
2.2 setup pgadmin to view and manage the database DONE
2.3 make it work with python DONE
2.4 make it work with python + async DONE
2.5 make it work with the bot... DONE
2.6 move something basic to database DONE

2.7 MOVE THE REST!!!

3. change the sync command to work beter with more guilds?
4. move stuff that isnt guild spesifc: TOKEN, origin_form_id, in_dev? enz to a config.json(?) file (idk if the service_account.json should be in there) DONE

note: find a good way to sync or make sure the data base is hosted on the remote server

- list of commands that need to be per guild:
- /settings DONE
- /reactionrole DONE
- /wmoji DONE DONE
- /art


# removed for now
"""
        CREATE TABLE IF NOT EXISTS art_contests (
            guild_id BIGINT PRIMARY KEY,
            art_contest_theme TEXT,
            art_contest_role_id BIGINT,
            art_contest_announcements_channel_id BIGINT,
            art_contest_submissions_channel_id BIGINT,
            art_contest_theme_suggestion_channel_id BIGNIT,
            art_contest_poll_message_id BIGINT,
            art_contest_form_id BIGINT,
            art_contest_responder_uri TEXT
        );
"""



# THINGS TO DO AFTER ROAD MAP IS DONE:



create a setup guide for myself DONE

POLL COMMAND v2: switch to buttons?

send msg when they join guild?


# random things to look into:

check out moduls

beter profile pic for bot



