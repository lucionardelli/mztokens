## Basic automatic _getter_ for MZ events tokens

This scripts automagically opens MZ, loads into the site using your own credentials, opens the current event and claims the tokens (whenever possible).

#### Running the script periodically

You may want to add something like this to your crontab (e.g. using `crontab -e`) to automatically run the script every 10 minutes:

    # Look for tokens in MZ events
    */10 * * * * /home/user/mztokens/mz.sh

#### IMPORTANT: _ Don't forget to create a `.env` file with the following keys:_

    `MZ_USERNAME`
    `MZ_PASSWORD`

